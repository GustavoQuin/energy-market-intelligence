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
