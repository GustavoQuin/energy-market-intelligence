USE EnergyMarketDB;
GO

CREATE TABLE dbo.FactWeather (
    weather_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT NOT NULL,
    region_id INT NOT NULL,
    temperature_avg DECIMAL(10,2),
    temperature_min DECIMAL(10,2),
    temperature_max DECIMAL(10,2),
    precipitation DECIMAL(10,2),
    wind_speed DECIMAL(10,2),

    CONSTRAINT FK_FactWeather_DimDate
        FOREIGN KEY (date_id)
        REFERENCES dbo.DimDate(date_id),

    CONSTRAINT FK_FactWeather_DimRegion
        FOREIGN KEY (region_id)
        REFERENCES dbo.DimRegion(region_id)
);
GO


SELECT *
FROM dbo.FactWeather;