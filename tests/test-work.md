# SQL Server to PostgreSQL ETL Pipeline

[![CI/CD](https://github.com/your-username/docker-sql/actions/workflows/etl_ci.yml/badge.svg)](https://github.com/your-username/docker-sql/actions/workflows/etl_ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready ETL (Extract, Transform, Load) pipeline that transfers data from **Microsoft SQL Server** to **PostgreSQL** using **Apache Airflow**, with automated testing via **GitHub Actions**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [License](#license)

---

## 📖 Overview

This project implements a complete data pipeline that:

1. **Extracts** data from SQL Server tables (customers, products, orders, payments, shipments)
2. **Transforms** and enriches the data with joins and aggregations
3. **Loads** the data into PostgreSQL for analytics
4. **Validates** data quality at each step

Built with Apache Airflow for orchestration and GitHub Actions for continuous integration.

---

## ✨ Features

- **Automated ETL Pipeline** - Scheduled or manual execution via Airflow DAGs
- **Data Quality Validation** - Built-in checks for NULLs, empty tables, and business rules
- **CI/CD Integration** - Automated testing on every push/PR with GitHub Actions
- **Dockerized Environment** - Easy local development with Docker Compose
- **Mocked Unit Tests** - Fast, reliable tests without heavy database dependencies
- **Environment Configuration** - Flexible settings for dev, staging, and production
- **Comprehensive Logging** - Detailed logs for debugging and monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ETL PIPELINE FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐     EXTRACT      ┌──────────────┐
│  SQL Server  │ ───────────────► │  Staging     │
│  (Source)    │                  │  Tables      │
│              │                  │  (PostgreSQL)│
│ - customers  │                  │              │
│ - products   │                  │ - stg_*      │
│ - orders     │                  └──────────────┘
│ - payments   │                         │
│ - shipments  │                         │ TRANSFORM
└──────────────┘                         ▼
                            ┌──────────────────────┐
                            │  Intermediate Tables │
                            │  int_orders_enriched │
                            └──────────────────────┘
                                     │
                                     │ LOAD
                                     ▼
                            ┌──────────────────────┐
                            │  Fact & Dimension    │
                            │  - fct_orders        │
                            │  - dim_customers     │
                            │  - dim_products      │
                            └──────────────────────┘
                                     │
                                     │ AGGREGATE
                                     ▼
                            ┌──────────────────────┐
                            │  Aggregation Tables  │
                            │  - agg_daily_sales   │
                            │  - agg_customer_*    │
                            └──────────────────────┘
                                     │
                                     │ VALIDATE
                                     ▼
                            ┌──────────────────────┐
                            │  Data Quality Checks │
                            │  ✅ PASS / ❌ FAIL   │
                            └──────────────────────┘
```

---

## 📦 Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Python | 3.8+ | ETL scripts and tests |
| Git | 2.30+ | Version control |

**Optional:**
- Apache Airflow (for local development without Docker)
- SQL Server Management Studio (for database administration)
- pgAdmin (for PostgreSQL administration)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/docker-sql.git
cd docker-sql

# 2. Start all services
docker-compose up -d

# 3. Access Airflow UI
# Open browser: http://localhost:8080
# Login: admin / admin

# 4. Trigger the ETL pipeline
# In Airflow UI: Toggle "full_etl_pipeline" DAG to ON

# 5. View logs
docker-compose logs -f airflow-scheduler
```

---

## 📥 Installation

### Local Development Setup

#### 1. Clone Repository
```bash
git clone https://github.com/your-username/docker-sql.git
cd docker-sql
```

#### 2. Start Containers
```bash
docker-compose up -d
```

This starts:
- **SQL Server** (port 1433) - Source database
- **PostgreSQL** (port 5432) - Destination database
- **Airflow Scheduler** - Executes DAGs
- **Airflow Webserver** - UI for monitoring

#### 3. Verify Services
```bash
# Check container status
docker-compose ps

# Expected output:
# NAME                    STATUS
# sqlserver               Up (healthy)
# postgres                Up (healthy)
# airflow-scheduler       Up
# airflow-webserver       Up
```

#### 4. Install Python Dependencies (Optional)
```bash
# For local testing without Docker
pip install pandas psycopg2-binary pyodbc pytest pytest-mock apache-airflow
```

### Production Deployment

1. **Configure environment variables** in your deployment platform
2. **Update connection strings** in `dags/sqlserver_to_postgres_etl.py`
3. **Deploy Airflow** using Kubernetes, ECS, or managed service (MWAA, Astronomer)
4. **Set up monitoring** and alerting for DAG failures

---

## 💻 Usage

### Running the ETL Pipeline

#### Via Airflow UI
1. Open http://localhost:8080
2. Login with credentials (admin/admin)
3. Find `full_etl_pipeline` DAG
4. Toggle the switch to enable
5. Click ▶️ (Play button) to trigger manually

#### Via Command Line
```bash
# Trigger DAG
docker exec airflow-scheduler airflow dags trigger full_etl_pipeline

# Check DAG status
docker exec airflow-scheduler airflow dags list

# Check task status
docker exec airflow-scheduler airflow tasks list full_etl_pipeline
```

#### Via Airflow API
```bash
curl -X POST "http://localhost:8080/api/v1/dags/full_etl_pipeline/dagRuns" \
  -H "Content-Type: application/json" \
  -u "admin:admin" \
  -d '{"conf": {}}'
```

### Monitoring the Pipeline

```bash
# View real-time logs
docker-compose logs -f airflow-scheduler

# View specific task logs
docker exec airflow-scheduler airflow tasks logs full_etl_pipeline extract_customers

# Check database row counts
docker exec postgres psql -U postgres -d retail_analytics_db \
  -c "SELECT COUNT(*) FROM fct_orders;"
```

### Stopping Services
```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v
```

---

## 📁 Project Structure

```
docker-sql/
├── .github/
│   └── workflows/
│       └── etl_ci.yml              # GitHub Actions CI/CD pipeline
├── dags/
│   └── sqlserver_to_postgres_etl.py # Airflow DAG definition
├── tests/
│   └── test_etl.py                 # Unit tests with mocks
├── docs/
│   └── AIRFLOW_GITHUB_ACTIONS_GUIDE.md  # Comprehensive guide
├── docker-compose.yml              # Local development containers
├── Dockerfile                      # Airflow container image
├── README.md                       # This file
└── requirements.txt                # Python dependencies (optional)
```

### File Descriptions

| File | Purpose |
|------|---------|
| `.github/workflows/etl_ci.yml` | CI/CD workflow - runs tests on push/PR |
| `dags/sqlserver_to_postgres_etl.py` | Main ETL pipeline - extract, transform, load logic |
| `tests/test_etl.py` | Unit tests - validates ETL logic with mocked data |
| `docker-compose.yml` | Local environment - defines all containers |
| `Dockerfile` | Airflow image - custom Airflow installation |
| `docs/AIRFLOW_GITHUB_ACTIONS_GUIDE.md` | Documentation - detailed Airflow & GitHub Actions guide |

---

## ⚙️ Configuration

### Environment Variables

#### SQL Server Connection
```python
# In dags/sqlserver_to_postgres_etl.py
SQLSERVER_HOST = "sqlserver"      # Docker service name (local) or hostname (prod)
SQLSERVER_PORT = "1433"
SQLSERVER_DATABASE = "retail_ops_db"
SQLSERVER_USER = "sa"
SQLSERVER_PASSWORD = "ankit4539047@"
```

#### PostgreSQL Connection
```python
# In dags/sqlserver_to_postgres_etl.py
POSTGRES_HOST = "postgres"        # Docker service name (local) or hostname (prod)
POSTGRES_PORT = "5432"
POSTGRES_DATABASE = "retail_analytics_db"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
```

#### Override with Environment Variables
```bash
# For production deployment
export SQLSERVER_HOST=prod-sqlserver.company.com
export SQLSERVER_PASSWORD=${PROD_SQL_PASSWORD}
export POSTGRES_HOST=prod-postgres.company.com
```

### Airflow DAG Configuration

```python
# In dags/sqlserver_to_postgres_etl.py

with DAG(
    dag_id='full_etl_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',    # Change to: None (manual), @hourly, @weekly
    catchup=False,                 # Don't run past scheduled runs
    max_active_runs=1,            # Prevent concurrent runs
    tags=['etl', 'retail']        # For filtering in UI
) as dag:
```

---

## 🧪 Testing

### Running Tests Locally

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_etl.py::test_fct_orders_not_empty -v

# Run with coverage
pytest tests/ --cov=dags --cov-report=html
```

### Test Coverage

```
============================= test session starts ==============================
collected 5 items

tests/test_etl.py::test_fct_orders_not_empty PASSED                      [ 20%]
tests/test_etl.py::test_no_null_order_id PASSED                          [ 40%]
tests/test_etl.py::test_positive_revenue PASSED                          [ 60%]
tests/test_etl.py::test_etl_extraction_logic PASSED                      [ 80%]
tests/test_etl.py::test_dtype_mapping PASSED                             [100%]

============================== 5 passed in 0.05s =============================
```

### Test Descriptions

| Test | Purpose |
|------|---------|
| `test_fct_orders_not_empty` | Verifies fct_orders has data after ETL |
| `test_no_null_order_id` | Checks no NULL values in order_id |
| `test_positive_revenue` | Validates total revenue is positive |
| `test_etl_extraction_logic` | Tests SQL Server & PostgreSQL connection functions |
| `test_dtype_mapping` | Verifies pandas → PostgreSQL type conversion |

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Every push or pull request triggers the CI pipeline:

```yaml
# .github/workflows/etl_ci.yml

name: ETL CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        ports:
          - 5433:5432
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
      - run: pip install pandas psycopg2-binary pytest pytest-mock
      - run: pytest tests/ -v
```

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE FLOW                          │
└─────────────────────────────────────────────────────────────────┘

  Push/PR Event
       │
       ▼
  ┌─────────────┐
  │ 1. Checkout │  Clone repository
  └─────────────┘
       │
       ▼
  ┌─────────────┐
  │ 2. Setup    │  Install Python 3.9
  └─────────────┘
       │
       ▼
  ┌─────────────┐
  │ 3. Install  │  pip install dependencies
  └─────────────┘
       │
       ▼
  ┌─────────────┐
  │ 4. Services │  Start PostgreSQL container
  └─────────────┘
       │
       ▼
  ┌─────────────┐
  │ 5. Test     │  pytest tests/ -v
  └─────────────┘
       │
    ┌──┴──┐
    │     │
   PASS  FAIL
    │     │
    ▼     ▼
  ✓ Merge  ❌ Block merge
         Fix errors
```

### Viewing CI Results

1. Go to repository on GitHub
2. Click **Actions** tab
3. Select workflow run
4. View logs for each step

---

## 🔧 Troubleshooting

### Common Issues

#### 1. SQL Server Container Won't Start
```bash
# Check logs
docker-compose logs sqlserver

# Solution: Increase memory allocation
# SQL Server requires minimum 2GB RAM
```

#### 2. Airflow DAG Not Showing
```bash
# Refresh DAGs
docker exec airflow-scheduler airflow dags refresh

# Check for syntax errors
docker exec airflow-scheduler python -m py_compile dags/sqlserver_to_postgres_etl.py
```

#### 3. Database Connection Failed
```bash
# Verify containers are running
docker-compose ps

# Test connectivity
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'ankit4539047@' -Q 'SELECT 1'
```

#### 4. Tests Fail Locally
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

#### 5. GitHub Actions Fail
```yaml
# Enable debug logging
env:
  ACTIONS_RUNNER_DEBUG: true
  ACTIONS_STEP_DEBUG: true
```

### Debug Commands

```bash
# View all containers
docker ps -a

# View Airflow logs
docker-compose logs -f airflow-scheduler airflow-webserver

# Access SQL Server container
docker exec -it sqlserver /bin/bash

# Access PostgreSQL container
docker exec -it postgres psql -U postgres

# Check Airflow database
docker exec airflow-scheduler airflow db check-migration
```

---
