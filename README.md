<img width="1255" height="705" alt="Page 1 - Executive Overview" src="https://github.com/user-attachments/assets/77e5e055-38f0-49b8-8261-be7832eb517b" />
<img width="1253" height="715" alt="Page 5 - Data Platform Architecture" src="https://github.com/user-attachments/assets/5b8c5bce-2607-4a15-a10e-175a104493e0" />
<img width="1257" height="701" alt="Page 4 - Prices and Production II" src="https://github.com/user-attachments/assets/bb91fb8b-a21d-4b5c-89e5-d508134fbc30" />
<img width="1257" height="705" alt="Page 3 - Prices and Production I" src="https://github.com/user-attachments/assets/e36da70c-2d7d-41eb-a6e0-f6bd11b96e09" />
<img width="1725" height="721" alt="Page 2 - Energy Commodity KPIs" src="https://github.com/user-attachments/assets/ac2b7da7-fdb6-4e79-8c9e-254913f1ec18" />
<img width="1247" height="711" alt="Portada Energy Dashboard" src="https://github.com/user-attachments/assets/cd39b53f-ce39-4cb0-8459-401b35a0ad2c" />
# Energy Market Intelligence

Automated data pipeline and Power BI dashboard for energy market analysis.

## Project Overview

This project integrates energy prices, exchange rates, weather data, and hydrocarbon production data into a SQL Server database for analysis and visualization in Power BI.

## Architecture

Data Sources → Python ETL → SQL Server → Power BI Dashboard

## Technologies

* **Python:** data extraction, transformation, and loading
* **SQL Server:** relational database and data storage
* **SQL:** schema creation, validation, and data quality checks
* **Power BI:** data modeling, DAX measures, and visualization

## Data Sources

* U.S. Energy Information Administration (EIA)
* Argentina Datos
* Meteostat
* Hydrocarbon production data

## Repository Structure

* `Scripts/` — Python ETL scripts
* `*.sql` — database schema, validation, and data quality queries
* `load_dimdate.py` — date dimension loading script

## Key Objectives

* Automate data ingestion from multiple sources
* Centralize energy market data in SQL Server
* Support analysis of commodity prices, exchange rates, weather, and production
* Build a foundation for Power BI reporting and market monitoring

## Data and Credentials

Local source files, spreadsheets, and credentials are excluded from the repository. API keys and connection settings should be configured locally.
