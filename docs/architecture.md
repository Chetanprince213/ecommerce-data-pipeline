# E-Commerce Data Pipeline Architecture

## Overview

The project separates cloud-based data transformation from local analytics and monitoring.

## Data Flow

```mermaid
flowchart TD
    A["Synthetic E-commerce CSV Files"] --> B["Amazon S3 - Raw Data"]
    B --> C["AWS Glue + PySpark"]
    C --> D["Processed Parquet Datasets in S3"]
    D --> E["Download Processed Data Locally"]
    E --> F["DuckDB + SQL Analytics"]
    F --> G["Streamlit Dashboard"]
    D --> H["Python Data Quality Checks"]
    H --> I["Data Quality Reports"]
    J["Python Pipeline Runner"] --> K["Project Smoke Test"]
    J --> F
    J --> H
    J --> L["Execution Logs and CSV History"]
    L --> M["Pipeline Monitor"]
    N["Windows Task Scheduler"] --> J
```

## Component Responsibilities

- **Amazon S3:** Stores raw and processed datasets.
- **AWS Glue and PySpark:** Transform raw datasets into Parquet outputs.
- **DuckDB and SQL:** Analyze locally available processed data.
- **Python data quality scripts:** Validate records and business rules.
- **Pipeline runner:** Executes local smoke tests, analytics, and quality checks.
- **Pipeline monitor:** Summarizes execution history.
- **Windows Task Scheduler:** Starts the local workflow on a schedule.
- **Streamlit:** Presents analytical results through a dashboard.

## Scope Note

The AWS Glue transformation and local Python orchestration are separate stages. The local runner does not currently trigger the Glue job automatically.
