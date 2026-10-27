import os
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ["PATH"]

from pathlib import Path
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, IntegerType, StringType,
    DoubleType
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / "spark"

CUSTOMER_SCHEMA = StructType([
    StructField("customer_id", IntegerType(), False),
    StructField("customer_name", StringType(), True),
    StructField("email", StringType(), True),
    StructField("city", StringType(), True),
    StructField("signup_date", StringType(), True),
])

PRODUCT_SCHEMA = StructType([
    StructField("product_id", IntegerType(), False),
    StructField("product_name", StringType(), True),
    StructField("category", StringType(), True),
    StructField("unit_price", DoubleType(), True),
])

ORDER_SCHEMA = StructType([
    StructField("order_id", IntegerType(), False),
    StructField("customer_id", IntegerType(), True),
    StructField("product_id", IntegerType(), True),
    StructField("order_date", StringType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("unit_price", DoubleType(), True),
    StructField("discount_pct", DoubleType(), True),
    StructField("sales_amount", DoubleType(), True),
    StructField("order_status", StringType(), True),
])


def require_no_rows(df, description):
    """Fail the job if a required data-quality rule is violated."""
    sample = df.limit(5).collect()

    if sample:
        raise ValueError(
            f"{description}. Example invalid rows: {sample}"
        )


def main():
    for filename in [
        "customers.csv", "products.csv", "orders.csv"
    ]:
        if not (RAW_DIR / filename).exists():
            raise FileNotFoundError(
                f"Required CSV missing: {RAW_DIR / filename}"
            )

    spark = (
        SparkSession.builder
        .appName("EcommerceDataTransformation")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    try:
        # 1. Read source CSVs with explicit schemas.
        customers = (
            spark.read
            .option("header", True)
            .schema(CUSTOMER_SCHEMA)
            .csv(str(RAW_DIR / "customers.csv"))
        )

        products = (
            spark.read
            .option("header", True)
            .schema(PRODUCT_SCHEMA)
            .csv(str(RAW_DIR / "products.csv"))
        )

        orders = (
            spark.read
            .option("header", True)
            .schema(ORDER_SCHEMA)
            .csv(str(RAW_DIR / "orders.csv"))
        )

        # 2. Convert source date strings to Spark date types.
        customers = customers.withColumn(
            "signup_date", F.to_date("signup_date")
        )

        orders = orders.withColumn(
            "order_date", F.to_date("order_date")
        )

        # 3. Validate required values.
        require_no_rows(
            customers.filter(
                F.col("customer_id").isNull()
                | F.col("email").isNull()
                | F.col("signup_date").isNull()
            ),
            "Invalid customer records"
        )

        require_no_rows(
            products.filter(
                F.col("product_id").isNull()
                | F.col("product_name").isNull()
                | F.col("unit_price").isNull()
                | (F.col("unit_price") < 0)
            ),
            "Invalid product records"
        )

        require_no_rows(
            orders.filter(
                F.col("order_id").isNull()
                | F.col("customer_id").isNull()
                | F.col("product_id").isNull()
                | F.col("order_date").isNull()
                | F.col("quantity").isNull()
                | (F.col("quantity") <= 0)
                | F.col("unit_price").isNull()
                | (F.col("unit_price") < 0)
                | F.col("discount_pct").isNull()
                | (~F.col("discount_pct").between(0, 100))
                | F.col("sales_amount").isNull()
                | (F.col("sales_amount") < 0)
            ),
            "Invalid order records"
        )

        # 4. Validate uniqueness of the entity keys.
        require_no_rows(
            customers.groupBy("customer_id")
            .count()
            .filter(F.col("count") > 1),
            "Duplicate customer IDs"
        )

        require_no_rows(
            products.groupBy("product_id")
            .count()
            .filter(F.col("count") > 1),
            "Duplicate product IDs"
        )

        require_no_rows(
            orders.groupBy("order_id")
            .count()
            .filter(F.col("count") > 1),
            "Duplicate order IDs"
        )

        # 5. Validate referential integrity.
        require_no_rows(
            orders.join(
                customers.select("customer_id"),
                on="customer_id",
                how="left_anti"
            ),
            "Orders contain unknown customer IDs"
        )

        require_no_rows(
            orders.join(
                products.select("product_id"),
                on="product_id",
                how="left_anti"
            ),
            "Orders contain unknown product IDs"
        )

                # 6. Create an enriched sales dataset.
        # Rename the catalog price so it doesn't clash with the order-line price.
        product_dim = products.select(
            "product_id",
            "product_name",
            "category",
            F.col("unit_price").alias("list_price"),
        )

        enriched_sales = (
            orders
            .join(customers, on="customer_id", how="inner")
            .join(
                F.broadcast(product_dim),
                on="product_id",
                how="inner"
            )
            .withColumn(
                "gross_amount",
                F.round(
                    F.col("quantity") * F.col("unit_price"),
                    2
                )
            )
            .withColumn(
                "expected_sales_amount",
                F.round(
                    F.col("quantity")
                    * F.col("unit_price")
                    * (1 - F.col("discount_pct") / 100),
                    2
                )
            )
            .withColumn(
                "sales_amount_check",
                F.when(
                    F.abs(
                        F.col("sales_amount")
                        - F.col("expected_sales_amount")
                    ) <= 0.02,
                    F.lit("MATCH")
                ).otherwise(F.lit("MISMATCH"))
            )
            .withColumn(
                "order_year_month",
                F.date_format("order_date", "yyyy-MM")
            )
        )

        # Flag amount discrepancies instead of silently changing source data.
        mismatches = enriched_sales.filter(
            F.col("sales_amount_check") == "MISMATCH"
        ).count()

        print(f"Sales amount mismatches: {mismatches}")

        # 7. Build dashboard-ready aggregate datasets.
        completed_sales = enriched_sales.filter(
            F.col("order_status") == "COMPLETED"
        )

        daily_sales = (
            enriched_sales.groupBy("order_date")
            .agg(
                F.count("*").alias("total_orders"),
                F.sum("quantity").alias("units_sold"),
                F.round(
                    F.sum(
                        F.when(
                            F.col("order_status") == "COMPLETED",
                            F.col("sales_amount")
                        ).otherwise(0)
                    ),
                    2
                ).alias("completed_revenue")
            )
        )

        customer_summary = (
            completed_sales.groupBy(
                "customer_id", "customer_name", "city"
            )
            .agg(
                F.countDistinct("order_id").alias("completed_orders"),
                F.round(
                    F.sum("sales_amount"), 2
                ).alias("lifetime_revenue")
            )
        )

        product_summary = (
            completed_sales.groupBy(
                "product_id", "product_name", "category"
            )
            .agg(
                F.countDistinct("order_id").alias("completed_orders"),
                F.sum("quantity").alias("units_sold"),
                F.round(
                    F.sum("sales_amount"), 2
                ).alias("revenue")
            )
        )

        # 8. Write outputs to local Parquet folders.
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        outputs = {
            "customers": customers,
            "products": products,
            "enriched_sales": enriched_sales,
            "daily_sales": daily_sales,
            "customer_summary": customer_summary,
            "product_summary": product_summary,
        }

        for name, df in outputs.items():
            target = OUTPUT_DIR / name

            writer = df.write.mode("overwrite")

            if name == "enriched_sales":
                writer = writer.partitionBy("order_year_month")

            writer.parquet(str(target))

            print(
                f"Wrote {name}: {df.count()} rows -> {target}"
            )

        print("\nPySpark transformation completed successfully.")

    finally:
        spark.stop()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nTRANSFORMATION FAILED: {exc}", file=sys.stderr)
        raise
