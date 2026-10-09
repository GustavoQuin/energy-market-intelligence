USE EnergyMarketDB;
GO

CREATE TABLE Staging_UnconventionalGasPrices (
    date DATE,
    open_price DECIMAL(18,4),
    high_price DECIMAL(18,4),
    low_price DECIMAL(18,4),
    close_price DECIMAL(18,4),
    daily_change DECIMAL(18,4),
    daily_change_pct DECIMAL(18,4),
    moving_avg_7d DECIMAL(18,4),
    moving_avg_30d DECIMAL(18,4)
);
