# Apache Airflow & GitHub Actions - Complete Guide

## Table of Contents
1. [What is Apache Airflow?](#what-is-apache-airflow)
2. [What is GitHub Actions?](#what-is-github-actions)
3. [Key Differences](#key-differences)
4. [How They Work Together](#how-they-work-together)
5. [Writing GitHub Actions YAML Files](#writing-github-actions-yaml-files)
6. [Common Errors & Solutions](#common-errors--solutions)
7. [This Project's Architecture](#this-projects-architecture)

---

## What is Apache Airflow?

**Apache Airflow** is an open-source platform for programmatically authoring, scheduling, and monitoring workflows and pipelines.

### Key Concepts

| Term | Description |
|------|-------------|
| **DAG** (Directed Acyclic Graph) | A collection of tasks organized to show their relationships and dependencies |
| **Task** | A single unit of work (e.g., run a Python function, execute a SQL query) |
| **Operator** | Defines what a task does (PythonOperator, BashOperator, etc.) |
| **Scheduler** | Monitors all DAGs and triggers tasks whose dependencies are complete |
| **Worker** | Executes the tasks |
| **Web Server** | Provides the UI for monitoring and managing DAGs |

### Example DAG (from this project)

```python
# dags/sqlserver_to_postgres_etl.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    dag_id='full_etl_pipeline',           # Unique DAG identifier
    start_date=datetime(2024, 1, 1),      # When DAG becomes active
    schedule_interval=None,               # Run manually (no schedule)
    catchup=False                         # Don't run past scheduled runs
) as dag:

    # Define tasks
    extract_task = PythonOperator(
        task_id="extract_customers",      # Unique task ID
        python_callable=extract_and_stage,
        op_args=["customers"]
    )
    
    transform_task = PythonOperator(
        task_id="build_intermediate",
        python_callable=build_intermediate
    )
    
    # Define dependencies (task order)
    extract_task >> transform_task
```

### How Airflow Works in This Project

```
┌─────────────────────────────────────────────────────────────────┐
│                        AIRFLOW SCHEDULER                        │
│  Monitors DAGs and triggers tasks when dependencies are met    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DAG: ETL Pipeline                       │
│                                                                 │
│  extract_customers ──┐                                         │
│  extract_products  ──┤                                         │
│  extract_orders    ──┼──► build_intermediate ──► build_marts  │
│  extract_payments  ──┤                                         │
│  extract_shipments ──┘                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────┐              ┌──────────────────────────────┐
│   SQL Server     │              │       PostgreSQL             │
│   (Source DB)    │   ─────►     │   (Destination/Analytics DB) │
│                  │   ETL        │                              │
└──────────────────┘              └──────────────────────────────┘
```

---

## What is GitHub Actions?

**GitHub Actions** is a CI/CD (Continuous Integration/Continuous Deployment) platform built into GitHub. It automates software development workflows like testing, building, and deploying code.

### Key Concepts

| Term | Description |
|------|-------------|
| **Workflow** | An automated process defined in a YAML file (`.github/workflows/*.yml`) |
| **Event/Trigger** | What starts the workflow (push, pull_request, schedule, etc.) |
| **Job** | A set of steps that run on the same runner |
| **Step** | A single task (run a command, use an action) |
| **Action** | A reusable unit of code (e.g., `actions/checkout@v6`) |
| **Runner** | The server that executes the workflow (GitHub-hosted or self-hosted) |

### Workflow File Structure

```yaml
name: Workflow Name          # Display name

on:                          # Triggers
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:                         # Environment variables (global)
  MY_VAR: value

jobs:
  job-name:                  # Job identifier
    runs-on: ubuntu-latest   # Runner type
    
    services:                # Container services (databases, etc.)
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:                   # Steps to execute
      - name: Step Name
        uses: action@version
      
      - name: Run Command
        run: echo "Hello"
```

---

## Key Differences

| Aspect | Apache Airflow | GitHub Actions |
|--------|----------------|----------------|
| **Primary Purpose** | Data pipeline orchestration | CI/CD automation |
| **Scheduling** | Cron-based, complex schedules | Event-driven (push, PR, manual) |
| **State Management** | Tracks task state, retries, backfills | Stateless, each run is independent |
| **Task Dependencies** | Complex DAGs with branching | Linear or matrix-based |
| **Execution Time** | Long-running (hours/days) | Short-running (max 6 hours) |
| **UI** | Rich web UI for monitoring | Basic workflow run logs |
| **Best For** | ETL, data pipelines, scheduled jobs | Testing, building, deploying code |

### Visual Comparison

```
AIRFLOW                                    GITHUB ACTIONS
─────────                                  ────────────────
Schedule-driven:                           Event-driven:
                                          
┌──────────┐                               ┌─────────┐
│ Cron:    │                               │  Push   │
│ 0 2 * *  │────► Trigger DAG              │  Event  │────► Trigger Workflow
│ 00       │                               └─────────┘
└──────────┘                                      │
                                                  ▼
                                           ┌─────────────┐
                                           │   Runner    │
                                           │  (VM/Container)│
                                           └─────────────┘
```

---

## How They Work Together

In this project, **GitHub Actions** handles CI/CD (testing code changes), while **Airflow** handles the actual ETL pipeline execution in production.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT FLOW                            │
└─────────────────────────────────────────────────────────────────────┘

    Developer                          GitHub
       │                                │
       │  1. Push code                  │
       │──────────────────────────────► │
       │                                │
       │                                │ 2. Trigger Workflow
       │                                │
       │                                ▼
       │                        ┌───────────────┐
       │                        │ GitHub Actions│
       │                        │   CI Pipeline │
       │                        │               │
       │                        │ - Run Tests   │
       │                        │ - Validate    │
       │                        └───────────────┘
       │                                │
       │  3. Pass/Fail Status           │
       │◄───────────────────────────────│
       │                                │
       
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION FLOW                             │
└─────────────────────────────────────────────────────────────────────┘

    Airflow Scheduler
           │
           │ 1. Trigger DAG (schedule/manual)
           ▼
    ┌───────────────┐
    │   Airflow     │
    │   Workers     │
    │               │
    │ - Extract     │
    │ - Transform   │
    │ - Load        │
    └───────────────┘
           │
           ▼
    ┌───────────────┐      ┌──────────────┐
    │  SQL Server   │─────►│  PostgreSQL  │
    │  (Source)     │ ETL  │  (Target)    │
    └───────────────┘      └──────────────┘
```

---

## Writing GitHub Actions YAML Files

### Complete Example (This Project)

```yaml
# .github/workflows/etl_ci.yml

# 1. Workflow Name (shown in GitHub Actions UI)
name: ETL CI Pipeline

# 2. Triggers - When to run this workflow
on:
  push:
    branches: 
      - main          # Run on pushes to main branch
  pull_request:
    branches: 
      - main          # Run on PRs to main branch

# 3. Environment Variables (available to all steps)
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true  # Fix Node.js deprecation

# 4. Jobs - What to run
jobs:
  test:                                    # Job ID
    # Runner specification
    runs-on: ubuntu-latest                 # Latest Ubuntu VM
    
    # Container services (databases, etc.)
    services:
      postgres:
        image: postgres:15                 # Docker image
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: retail_analytics_db
        ports:
          - 5433:5432                      # Map host:container ports
        options: >-                        # Docker run options
          --health-cmd="pg_isready -U postgres"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    
    # Steps to execute
    steps:
      # Step 1: Checkout code
      - name: Checkout code
        uses: actions/checkout@v6          # Official GitHub action
      
      # Step 2: Set up Python
      - name: Set up Python
        uses: actions/setup-python@v6     # Official GitHub action
        with:
          python-version: 3.9              # Python version
      
      # Step 3: Install dependencies
      - name: Install dependencies
        run: |                             # Multi-line shell command
          pip install pandas psycopg2-binary pytest pytest-mock
      
      # Step 4: Wait for services
      - name: Wait for Postgres
        run: |
          sleep 10
      
      # Step 5: Run tests with environment variables
      - name: Run unit tests
        env:                               # Step-specific env vars
          POSTGRES_HOST: localhost
          POSTGRES_PORT: 5433
        run: |
          pytest tests/ -v
```

### YAML Syntax Guide

#### Basic Structure
```yaml
# Key-value pairs
name: My Workflow

# Lists
branches:
  - main
  - develop

# Nested objects
on:
  push:
    branches: [main]

# Multi-line strings (preserve newlines)
run: |
  echo "Line 1"
  echo "Line 2"

# Multi-line strings (fold newlines to spaces)
options: >-
  --option1
  --option2

# Environment variables
env:
  VAR1: value1
  VAR2: "value with spaces"
```

#### Common Actions
```yaml
# Checkout repository
- uses: actions/checkout@v6

# Set up Node.js
- uses: actions/setup-node@v4
  with:
    node-version: '20'

# Set up Python
- uses: actions/setup-python@v6
  with:
    python-version: '3.9'

# Cache dependencies
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# Upload artifacts
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: test-results/
```

#### Conditional Execution
```yaml
# Run only on main branch
- name: Deploy
  if: github.ref == 'refs/heads/main'
  run: ./deploy.sh

# Run only if previous step failed
- name: Notify on Failure
  if: failure()
  run: ./notify.sh

# Run only on pull requests
- name: Comment on PR
  if: github.event_name == 'pull_request'
  run: ./comment.sh
```

---

## Common Errors & Solutions

### Error 1: Node.js Deprecation Warning
```
Node.js 20 actions are deprecated...
```

**Solution:**
```yaml
env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

# Use latest action versions
- uses: actions/checkout@v6
- uses: actions/setup-python@v6
```

### Error 2: Container Failed to Start
```
Error: One or more containers failed to start.
```

**Causes:**
- Insufficient runner resources (memory/CPU)
- Incorrect health check syntax
- Container image issues

**Solutions:**
```yaml
# Option 1: Fix health check syntax
services:
  postgres:
    options: >-
      --health-cmd="pg_isready -U postgres"
      --health-interval=10s
      --health-retries=5

# Option 2: Start container manually
- name: Start Container
  run: docker run -d --name mydb image:tag

- name: Wait for Ready
  run: |
    for i in {1..30}; do
      if command_succeeds; then break; fi
      sleep 5
    done
```

### Error 3: Module Not Found
```
ModuleNotFoundError: No module named 'xxx'
```

**Solution:**
```yaml
# Install all required dependencies
- name: Install dependencies
  run: |
    pip install -r requirements.txt

# Or install specific packages
- name: Install dependencies
  run: |
    pip install pandas pytest psycopg2-binary
```

### Error 4: Database Connection Failed
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
```yaml
# 1. Add wait time for database
- name: Wait for Postgres
  run: sleep 10

# 2. Use correct port mapping
services:
  postgres:
    ports:
      - 5433:5432  # Host:Container

# 3. Pass environment variables to steps
- name: Run tests
  env:
    POSTGRES_HOST: localhost
    POSTGRES_PORT: 5433
  run: pytest tests/
```

### Error 5: Permission Denied
```
Permission denied: unable to access file
```

**Solution:**
```yaml
# Fix file permissions
- name: Fix permissions
  run: chmod +x scripts/*.sh

# Or run with proper user
- name: Run script
  run: ./script.sh
```

### Error 6: Workflow Not Triggering
**Check:**
1. File is in `.github/workflows/` directory
2. File has `.yml` or `.yaml` extension
3. `on:` trigger matches your event
4. Branch name is correct

### Error 7: Job Timeout
```
Error: The operation was canceled.
```

**Solution:**
```yaml
# Increase timeout (default: 360 minutes)
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 60
```

### Debugging Tips

```yaml
# Enable debug logging
env:
  ACTIONS_RUNNER_DEBUG: true
  ACTIONS_STEP_DEBUG: true

# Add debug steps
- name: Debug
  run: |
    echo "Current directory: $(pwd)"
    echo "Files: $(ls -la)"
    echo "Python version: $(python --version)"
    echo "Env vars: $(env | sort)"
```

---

## This Project's Architecture

### Project Structure
```
docker-sql/
├── .github/
│   └── workflows/
│       └── etl_ci.yml          # GitHub Actions CI pipeline
├── dags/
│   └── sqlserver_to_postgres_etl.py   # Airflow DAG
├── tests/
│   └── test_etl.py             # Unit tests
├── docker-compose.yml          # Local development containers
├── Dockerfile                  # Airflow container image
└── docs/
    └── AIRFLOW_GITHUB_ACTIONS_GUIDE.md
```

### Data Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                        LOCAL DEVELOPMENT                          │
└────────────────────────────────────────────────────────────────────┘

docker-compose.yml starts:
  
┌──────────────┐    ┌──────────────┐    ┌─────────────────┐
│  SQL Server  │    │   Airflow    │    │   PostgreSQL    │
│  :1433       │    │  Scheduler   │    │   :5432         │
│              │    │  + Webserver │    │                 │
│  Source Data │    │              │    │  Analytics DB   │
└──────────────┘    └──────────────┘    └─────────────────┘
                           │
                           │ Executes DAG
                           ▼
                    ┌──────────────┐
                    │  ETL Steps:  │
                    │              │
                    │  1. Extract  │───────► Read from SQL Server
                    │  2. Stage    │───────► Create staging tables
                    │  3. Transform│───────► Join/enrich data
                    │  4. Load     │───────► Write to PostgreSQL
                    │  5. Validate │───────► Check data quality
                    └──────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                         CI/CD PIPELINE                            │
└────────────────────────────────────────────────────────────────────┘

GitHub Actions (etl_ci.yml):

  Push/PR Event
       │
       ▼
  ┌─────────────────┐
  │  Checkout Code  │
  └─────────────────┘
       │
       ▼
  ┌─────────────────┐
  │  Setup Python   │
  └─────────────────┘
       │
       ▼
  ┌─────────────────┐
  │ Install Deps    │
  └─────────────────┘
       │
       ▼
  ┌─────────────────┐
  │ Start Postgres  │
  │  (Test Service) │
  └─────────────────┘
       │
       ▼
  ┌─────────────────┐
  │  Run Tests      │
  │  (Mocked)       │
  └─────────────────┘
       │
       ▼
  Pass/Fail Status
```

### ETL Pipeline Steps (Airflow DAG)

```python
# 1. EXTRACT - Pull data from SQL Server
extract_customers    extract_products    extract_orders
        │                   │                  │
        └───────────────────┼──────────────────┘
                            │
# 2. STAGE - Create staging tables in PostgreSQL
                            ▼
                    stg_customers, stg_products, stg_orders
                            │
# 3. TRANSFORM - Join and enrich data
                            ▼
                    int_orders_enriched
                            │
# 4. LOAD - Create fact and dimension tables
                            ▼
            fct_orders, dim_customers, dim_products
                            │
# 5. AGGREGATE - Create summary tables
                            ▼
            agg_daily_sales, agg_customer_metrics
                            │
# 6. VALIDATE - Check data quality
                            ▼
                    ✅ Validation passed
```

### Configuration Files

#### docker-compose.yml (Local Development)
```yaml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    ports:
      - "1433:1433"
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=ankit4539047@

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=airflow_db

  airflow-scheduler:
    build: .
    volumes:
      - ./dags:/opt/airflow/dags
    command: airflow scheduler
```

#### etl_ci.yml (CI/CD)
```yaml
name: ETL CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        ports:
          - 5433:5432
        options: >-
          --health-cmd="pg_isready -U postgres"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: 3.9
      - run: pip install pandas psycopg2-binary pytest pytest-mock
      - run: sleep 10
      - run: pytest tests/ -v
        env:
          POSTGRES_HOST: localhost
          POSTGRES_PORT: 5433
```

### Running Locally

```bash
# Start all containers
docker-compose up -d

# View Airflow UI
# http://localhost:8080 (login: admin/admin)

# Trigger DAG manually via CLI
docker exec airflow-scheduler airflow dags trigger full_etl_pipeline

# View logs
docker-compose logs -f airflow-scheduler

# Stop all containers
docker-compose down
```

### Running CI/CD

```bash
# Push to GitHub
git add .
git commit -m "Update ETL logic"
git push origin main

# GitHub Actions automatically runs the workflow
# View results at: https://github.com/your-username/your-repo/actions
```

---

## Quick Reference

### Airflow Operators
```python
PythonOperator      # Run Python function
BashOperator        # Run bash command
PostgresOperator    # Run SQL on PostgreSQL
MySqlOperator       # Run SQL on MySQL
EmailOperator       # Send email
```

### GitHub Actions Context
```yaml
${{ github.ref }}           # Branch/tag ref
${{ github.sha }}           # Commit SHA
${{ github.actor }}         # User who triggered
${{ github.event_name }}    # Event type
${{ runner.os }}            # Runner OS
${{ secrets.MY_SECRET }}    # Encrypted secret
```

### Common Commands
```bash
# Airflow
airflow dags list
airflow dags trigger <dag_id>
airflow tasks list <dag_id>
airflow logs <dag_id> <task_id>

# Docker
docker-compose up -d
docker-compose logs -f
docker-compose down

# GitHub Actions (local testing)
act                    # Run actions locally (requires act tool)
```

---

## Summary

| Tool | Use in This Project |
|------|---------------------|
| **Airflow** | Production ETL: SQL Server → PostgreSQL |
| **GitHub Actions** | CI: Test code changes before merge |
| **Docker Compose** | Local development environment |
| **PostgreSQL** | Analytics database (destination) |
| **SQL Server** | Operations database (source) |

Both Airflow and GitHub Actions are essential:
- **GitHub Actions** ensures code quality before deployment
- **Airflow** runs the actual data pipelines in production
