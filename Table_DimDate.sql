USE EnergyMarketDB;
GO

CREATE TABLE DimDate (
    date_id INT PRIMARY KEY,
    [date] DATE NOT NULL,
    [year] INT NOT NULL,
    [quarter] VARCHAR(10),
    [month] INT,
    month_name VARCHAR(20),
    [week] INT,
    [day] INT,
    day_name VARCHAR(20),
    is_weekend BIT
);
GO


SELECT * 
FROM DimDate