FROM apache/airflow:2.8.1

USER root

# Install ODBC driver
RUN apt-get update && apt-get install -y \
    curl gnupg apt-transport-https ca-certificates \
    unixodbc unixodbc-dev

# Add Microsoft repo
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Back to airflow user
USER airflow

# Install Python libs
RUN pip install pyodbc pandas psycopg2-binary