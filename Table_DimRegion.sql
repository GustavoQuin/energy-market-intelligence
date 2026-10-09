USE EnergyMarketDB;
GO

CREATE TABLE DimRegion (
    region_id INT PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL,
    province VARCHAR(50),
    basin VARCHAR(50),
    country VARCHAR(50) NOT NULL
);
GO

SELECT *
FROM DimRegion;