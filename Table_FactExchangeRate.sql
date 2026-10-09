USE EnergyMarketDB;
GO

CREATE TABLE dbo.FactExchangeRate (
    exchange_rate_id INT IDENTITY(1,1) PRIMARY KEY,
    date_id INT NOT NULL,
    currency_pair VARCHAR(20) NOT NULL,
    official_rate DECIMAL(18,4) NOT NULL,
    market_rate DECIMAL(18,4),
    rate_change DECIMAL(18,4),
    rate_change_pct DECIMAL(18,6),

    CONSTRAINT FK_FactExchangeRate_DimDate
        FOREIGN KEY (date_id)
        REFERENCES dbo.DimDate(date_id)
);
GO


SELECT * 
FROM dbo.FactExchangeRate