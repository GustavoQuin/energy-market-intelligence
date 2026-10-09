USE EnergyMarketDB;
GO

CREATE TABLE dbo.FactProduction (
    production_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT NOT NULL,
    region_id INT NOT NULL,
    production_type_id INT NOT NULL,
    production_value DECIMAL(18,4) NOT NULL,
    unit VARCHAR(30) NOT NULL,
    monthly_change DECIMAL(18,4),
    monthly_change_pct DECIMAL(18,6),
    year_over_year_change_pct DECIMAL(18,6),

    CONSTRAINT FK_FactProduction_DimDate
        FOREIGN KEY (date_id)
        REFERENCES dbo.DimDate(date_id),

    CONSTRAINT FK_FactProduction_DimRegion
        FOREIGN KEY (region_id)
        REFERENCES dbo.DimRegion(region_id),

    CONSTRAINT FK_FactProduction_DimProductionType
        FOREIGN KEY (production_type_id)
        REFERENCES dbo.DimProductionType(production_type_id)
);
GO

SELECT *
FROM dbo.FactProduction;