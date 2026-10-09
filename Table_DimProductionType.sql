USE EnergyMarketDB;
GO

CREATE TABLE DimProductionType (
    production_type_id INT PRIMARY KEY,
    production_type_name VARCHAR(50) NOT NULL,
    production_category VARCHAR(30) NOT NULL,
    unit VARCHAR(30) NOT NULL
);
GO

SELECT *
FROM DimProductionType;