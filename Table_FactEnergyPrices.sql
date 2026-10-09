USE EnergyMarketDB;
GO

CREATE TABLE FactEnergyPrices (
    energy_price_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT NOT NULL,
    commodity_id INT NOT NULL,
    open_price DECIMAL(18,4),
    high_price DECIMAL(18,4),
    low_price DECIMAL(18,4),
    close_price DECIMAL(18,4) NOT NULL,
    daily_change DECIMAL(18,4),
    daily_change_pct DECIMAL(18,6),
    moving_avg_7d DECIMAL(18,4),
    moving_avg_30d DECIMAL(18,4),
    volatility_30d DECIMAL(18,6),

    CONSTRAINT FK_FactEnergyPrices_DimDate
        FOREIGN KEY (date_id)
        REFERENCES DimDate(date_id),

    CONSTRAINT FK_FactEnergyPrices_DimCommodity
        FOREIGN KEY (commodity_id)
        REFERENCES DimCommodity(commodity_id)
);
GO

SELECT *
FROM FactEnergyPrices;

