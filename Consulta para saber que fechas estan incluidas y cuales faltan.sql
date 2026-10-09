SELECT 
    MAX(date_id) AS ultima_fecha_id,
    CAST(CONVERT(char(8), MAX(date_id)) AS date) AS ultima_fecha,
    CAST(GETDATE() AS date) AS fecha_actual,
    DATEDIFF(DAY, CAST(CONVERT(char(8), MAX(date_id)) AS date), GETDATE()) AS dias_atraso
FROM dbo.FactEnergyPrices;
