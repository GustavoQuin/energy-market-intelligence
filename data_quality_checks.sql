USE EnergyMarketDB;
GO

/* =========================================================
   1. ROW COUNTS
   ========================================================= */

USE EnergyMarketDB;
GO

/* =========================================================
   1. ROW COUNTS
   ========================================================= */

SELECT 'DimDate' AS TableName, COUNT(*) AS TotalRows
FROM dbo.DimDate

UNION ALL

SELECT 'DimCommodity', COUNT(*)
FROM dbo.DimCommodity

UNION ALL

SELECT 'DimRegion', COUNT(*)
FROM dbo.DimRegion

UNION ALL

SELECT 'DimProductionType', COUNT(*)
FROM dbo.DimProductionType

UNION ALL

SELECT 'FactEnergyPrices', COUNT(*)
FROM dbo.FactEnergyPrices

UNION ALL

SELECT 'FactProduction', COUNT(*)
FROM dbo.FactProduction

UNION ALL

SELECT 'FactExchangeRate', COUNT(*)
FROM dbo.FactExchangeRate

UNION ALL

SELECT 'FactWeather', COUNT(*)
FROM dbo.FactWeather;
GO


/* =========================================================
   2. DUPLICATES
   ========================================================= */

-- Energy prices:
-- one row per date + commodity should exist

SELECT
    date_id,
    commodity_id,
    COUNT(*) AS DuplicateCount
FROM dbo.FactEnergyPrices
GROUP BY
    date_id,
    commodity_id
HAVING COUNT(*) > 1;
GO


-- Exchange rate:
-- one USD/ARS observation per date

SELECT
    date_id,
    currency_pair,
    COUNT(*) AS DuplicateCount
FROM dbo.FactExchangeRate
GROUP BY
    date_id,
    currency_pair
HAVING COUNT(*) > 1;
GO


-- Weather:
-- one observation per date + region

SELECT
    date_id,
    region_id,
    COUNT(*) AS DuplicateCount
FROM dbo.FactWeather
GROUP BY
    date_id,
    region_id
HAVING COUNT(*) > 1;
GO


-- Production:
-- one observation per date + region + production type

SELECT
    date_id,
    region_id,
    production_type_id,
    COUNT(*) AS DuplicateCount
FROM dbo.FactProduction
GROUP BY
    date_id,
    region_id,
    production_type_id
HAVING COUNT(*) > 1;
GO


/* =========================================================
   3. FOREIGN KEY / ORPHAN CHECKS
   ========================================================= */

SELECT f.*
FROM dbo.FactEnergyPrices f
LEFT JOIN dbo.DimDate d
    ON f.date_id = d.date_id
WHERE d.date_id IS NULL;
GO


SELECT f.*
FROM dbo.FactEnergyPrices f
LEFT JOIN dbo.DimCommodity c
    ON f.commodity_id = c.commodity_id
WHERE c.commodity_id IS NULL;
GO


SELECT f.*
FROM dbo.FactProduction f
LEFT JOIN dbo.DimRegion r
    ON f.region_id = r.region_id
WHERE r.region_id IS NULL;
GO


SELECT f.*
FROM dbo.FactProduction f
LEFT JOIN dbo.DimProductionType p
    ON f.production_type_id = p.production_type_id
WHERE p.production_type_id IS NULL;
GO


/* =========================================================
   4. ENERGY PRICE LOGIC
   ========================================================= */

-- Negative or zero prices

SELECT *
FROM dbo.FactEnergyPrices
WHERE
    open_price <= 0
    OR high_price <= 0
    OR low_price <= 0
    OR close_price <= 0;
GO


-- High price should never be below Low price

SELECT *
FROM dbo.FactEnergyPrices
WHERE high_price < low_price;
GO


-- High should be >= open and close

SELECT *
FROM dbo.FactEnergyPrices
WHERE
    high_price < open_price
    OR high_price < close_price;
GO


-- Low should be <= open and close

SELECT *
FROM dbo.FactEnergyPrices
WHERE
    low_price > open_price
    OR low_price > close_price;
GO


/* =========================================================
   5. PRODUCTION CHECKS
   ========================================================= */

SELECT *
FROM dbo.FactProduction
WHERE production_value < 0;
GO


/* =========================================================
   6. EXCHANGE RATE CHECKS
   ========================================================= */

SELECT *
FROM dbo.FactExchangeRate
WHERE official_rate <= 0;
GO


/* =========================================================
   7. WEATHER CHECKS
   ========================================================= */

SELECT *
FROM dbo.FactWeather
WHERE temperature_min > temperature_max;
GO


SELECT *
FROM dbo.FactWeather
WHERE precipitation < 0;
GO


SELECT *
FROM dbo.FactWeather
WHERE wind_speed < 0;
GO


/* =========================================================
   8. DATE RANGE VALIDATION
   ========================================================= */

SELECT
    MIN([date]) AS MinDate,
    MAX([date]) AS MaxDate
FROM dbo.DimDate;
GO


SELECT
    MIN(date_id) AS MinEnergyDate,
    MAX(date_id) AS MaxEnergyDate
FROM dbo.FactEnergyPrices;
GO


SELECT
    MIN(date_id) AS MinExchangeDate,
    MAX(date_id) AS MaxExchangeDate
FROM dbo.FactExchangeRate;
GO


SELECT
    MIN(date_id) AS MinWeatherDate,
    MAX(date_id) AS MaxWeatherDate
FROM dbo.FactWeather;
GO


SELECT
    MIN(date_id) AS MinProductionDate,
    MAX(date_id) AS MaxProductionDate
FROM dbo.FactProduction;
GO