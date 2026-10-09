USE EnergyMarketDB;
GO

CREATE TABLE BridgeProductionCommodity (
    production_type_id INT NOT NULL,
	commodity_id INT NOT NULL
);

INSERT INTO BridgeProductionCommodity VALUES (1, 1); -- Oil Production → Brent
INSERT INTO BridgeProductionCommodity VALUES (1, 2); -- Oil Production → WTI
INSERT INTO BridgeProductionCommodity VALUES (2, 3); -- Gas Production → Henry Hub
INSERT INTO BridgeProductionCommodity VALUES (3, 1); -- Unconventional Oil → Brent
INSERT INTO BridgeProductionCommodity VALUES (3, 2); -- Unconventional Oil → WTI
INSERT INTO BridgeProductionCommodity VALUES (4, 4); -- Unconventional Gas → Unconventional Gas
