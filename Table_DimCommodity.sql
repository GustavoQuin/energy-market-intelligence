USE EnergyMarketDB;
GO

CREATE TABLE DimCommodity (
    commodity_id INT PRIMARY KEY,
    commodity_name VARCHAR(50) NOT NULL,
    commodity_category VARCHAR(30) NOT NULL,
    unit VARCHAR(30) NOT NULL,
    currency VARCHAR(10) NOT NULL
);
GO

SELECT *
FROM DimCommodity;