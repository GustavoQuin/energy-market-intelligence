# =========================================================
# IMPORTS
# =========================================================
import io
import os
from datetime import datetime
from pathlib import Path
import urllib3

from dotenv import load_dotenv
import pandas as pd
import requests
import sqlalchemy
from sqlalchemy import text

# Cargar variables de entorno desde .env local
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# CONFIGURATION & DATABASE CONNECTION
# =========================================================
DB_SERVER = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "EnergyMarketDB")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
EIA_API_KEY = os.getenv("EIA_API_KEY")

# Ruta relativa estándar para datos locales dentro del repo
BASE_DIR = Path(__file__).resolve().parent
FALLBACK_DATA_PATH = os.getenv(
    "FALLBACK_DATA_PATH", 
    str(BASE_DIR / "data" / "raw" / "TD_S_SescoWebUP_Fallback.xlsx")
)

# Conexión SQLAlchemy con Windows Authentication o User/Pass según variables
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if db_user and db_password:
    connection_uri = (
        f"mssql+pyodbc://{db_user}:{db_password}@{DB_SERVER}/{DB_NAME}"
        f"?driver={DB_DRIVER.replace(' ', '+')}"
    )
else:
    # Autenticación integrada de Windows
    connection_uri = (
        f"mssql+pyodbc://@{DB_SERVER}/{DB_NAME}"
        f"?driver={DB_DRIVER.replace(' ', '+')}&trusted_connection=yes"
    )

engine = sqlalchemy.create_engine(connection_uri)

# =========================================================
# MAPEAR DIMENSIONES
# =========================================================
df_dim_commodity = pd.read_sql("SELECT commodity_id, commodity_name FROM dbo.DimCommodity", engine)
commodity_map = dict(zip(df_dim_commodity['commodity_name'], df_dim_commodity['commodity_id']))

df_dim_region = pd.read_sql("SELECT region_id, region_name FROM dbo.DimRegion", engine)
region_map = dict(zip(df_dim_region['region_name'], df_dim_region['region_id']))

df_dim_prodtype = pd.read_sql("SELECT production_type_id, production_type_name FROM dbo.DimProductionType", engine)
prodtype_map = dict(zip(df_dim_prodtype['production_type_name'], df_dim_prodtype['production_type_id']))


# =========================================================
# 1. FACT ENERGY PRICES (EIA API v2)
# =========================================================
try:
    print("Loading FactEnergyPrices...\n")

    if not EIA_API_KEY:
        raise ValueError("EIA_API_KEY no configurada en las variables de entorno.")

    url = f"https://api.eia.gov/v2/petroleum/pri/spt/data/?api_key={EIA_API_KEY}&frequency=daily&data[0]=value&facets[series][]=RWTC"

    data = requests.get(url, timeout=30).json()
    df_oil = pd.DataFrame(data['response']['data'])
    df_oil = df_oil.rename(columns={'period': 'date', 'value': 'close_price'})
    df_oil['date'] = pd.to_datetime(df_oil['date'])
    df_oil['date_id'] = df_oil['date'].dt.strftime('%Y%m%d').astype(int)
    df_oil['close_price'] = pd.to_numeric(df_oil['close_price'], errors='coerce')
    
    # Ordenar cronológicamente para cálculos de ventana
    df_oil = df_oil.sort_values('date').dropna(subset=['close_price'])

    # Asignar dimensión y métricas
    df_oil['commodity_id'] = commodity_map['WTI Crude']
    df_oil['open_price'] = df_oil['close_price']
    df_oil['high_price'] = df_oil['close_price']
    df_oil['low_price'] = df_oil['close_price']
    df_oil['daily_change'] = df_oil['close_price'].diff()
    df_oil['daily_change_pct'] = df_oil['close_price'].pct_change() * 100
    df_oil['moving_avg_7d'] = df_oil['close_price'].rolling(7).mean()
    df_oil['moving_avg_30d'] = df_oil['close_price'].rolling(30).mean()
    df_oil['volatility_30d'] = df_oil['close_price'].rolling(30).std()

    df_oil = df_oil.astype({
        'open_price': 'float', 'high_price': 'float', 'low_price': 'float',
        'close_price': 'float', 'daily_change': 'float', 'daily_change_pct': 'float',
        'moving_avg_7d': 'float', 'moving_avg_30d': 'float', 'volatility_30d': 'float'
    })[[
        'date_id', 'commodity_id', 'open_price', 'high_price', 'low_price',
        'close_price', 'daily_change', 'daily_change_pct',
        'moving_avg_7d', 'moving_avg_30d', 'volatility_30d'
    ]]

    # Filtrar solo registros incrementales
    ultima_sql = pd.read_sql("SELECT MAX(date_id) AS ultima_fecha FROM dbo.FactEnergyPrices", engine)['ultima_fecha'][0]
    
    if pd.notnull(ultima_sql):
        df_oil = df_oil[df_oil['date_id'] > int(ultima_sql)]

    if df_oil.empty:
        print("No hay nuevos precios para cargar.\n")
    else:
        with engine.connect() as conn:
            date_ids = [int(x) for x in df_oil['date_id'].unique()]
            conn.execute(
                text("DELETE FROM dbo.FactEnergyPrices WHERE date_id IN :date_ids"),
                {"date_ids": tuple(date_ids)}
            )
            conn.commit()

        df_oil.to_sql("FactEnergyPrices", engine, if_exists="append", index=False, schema="dbo")
        print(f"FactEnergyPrices cargado exitosamente: {len(df_oil)} filas insertadas.\n")

except Exception as e:
    print(f"Error en FactEnergyPrices: {e}\n")


# =========================================================
# 2. FACT EXCHANGE RATE (ArgentinaDatos API)
# =========================================================
try:
    print("Loading FactExchangeRate...\n")

    url = "https://api.argentinadatos.com/v1/cotizaciones/dolares/oficial"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    df_fx = pd.DataFrame(response.json())
    df_fx["date"] = pd.to_datetime(df_fx["fecha"])
    df_fx["date_id"] = df_fx["date"].dt.strftime("%Y%m%d").astype(int)
    df_fx["official_rate"] = pd.to_numeric(df_fx["venta"], errors="coerce")
    df_fx = df_fx.dropna(subset=["official_rate"]).sort_values("date")

    df_fx["currency_pair"] = "USDARS"
    df_fx["rate_change"] = df_fx["official_rate"].diff()
    df_fx["rate_change_pct"] = df_fx["official_rate"].pct_change()
    df_fx["market_rate"] = None

    df_fx = df_fx.astype({
        "official_rate": "float",
        "rate_change": "float",
        "rate_change_pct": "float"
    })[["date_id", "currency_pair", "official_rate", "market_rate", "rate_change", "rate_change_pct"]]

    ultima_sql = pd.read_sql("SELECT MAX(date_id) AS ultima_fecha FROM dbo.FactExchangeRate", engine)["ultima_fecha"][0]

    if pd.notnull(ultima_sql):
        df_fx = df_fx[df_fx["date_id"] > int(ultima_sql)]

    if df_fx.empty:
        print("No hay nuevas cotizaciones para cargar.\n")
    else:
        with engine.connect() as conn:
            date_ids = [int(x) for x in df_fx['date_id'].unique()]
            conn.execute(
                text("DELETE FROM dbo.FactExchangeRate WHERE date_id IN :date_ids"),
                {"date_ids": tuple(date_ids)}
            )
            conn.commit()

        df_fx.to_sql("FactExchangeRate", engine, if_exists="append", index=False, schema="dbo")
        print(f"FactExchangeRate cargado exitosamente: {len(df_fx)} filas insertadas.\n")

except Exception as e:
    print(f"Error en FactExchangeRate: {e}\n")


# =========================================================
# 3. FACT WEATHER (Open-Meteo Historical & Near-Realtime API)
# =========================================================
try:
    print("Loading FactWeather...\n")

    # Coordenadas parametrizables (default: Neuquén)
    latitude = float(os.getenv("WEATHER_LATITUDE", -38.9516))
    longitude = float(os.getenv("WEATHER_LONGITUDE", -68.0591))

    ultima_sql = pd.read_sql("SELECT MAX(date_id) AS ultima_fecha FROM dbo.FactWeather", engine)['ultima_fecha'][0]

    if pd.notnull(ultima_sql):
        start_date = (pd.to_datetime(str(ultima_sql), format='%Y%m%d') + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        start_date = (datetime.today().replace(year=datetime.today().year - 1)).strftime('%Y-%m-%d')

    end_date = datetime.today().strftime('%Y-%m-%d')

    if pd.to_datetime(start_date) > pd.to_datetime(end_date):
        print("No hay fechas pendientes de consultar para FactWeather.\n")
        df_weather = pd.DataFrame()
    else:
        url_weather = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_mean",
                "temperature_2m_min",
                "temperature_2m_max",
                "precipitation_sum",
                "wind_speed_10m_max"
            ],
            "timezone": "America/Argentina/Buenos_Aires"
        }

        response = requests.get(url_weather, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "daily" in data and len(data["daily"]["time"]) > 0:
            df_weather = pd.DataFrame(data["daily"]).rename(columns={
                'time': 'date',
                'temperature_2m_mean': 'temperature_avg',
                'temperature_2m_min': 'temperature_min',
                'temperature_2m_max': 'temperature_max',
                'precipitation_sum': 'precipitation',
                'wind_speed_10m_max': 'wind_speed'
            })

            df_weather['date'] = pd.to_datetime(df_weather['date'])
            df_weather['date_id'] = df_weather['date'].dt.strftime('%Y%m%d').astype(int)
            df_weather['region_id'] = region_map['Neuquén Province']

            df_weather = df_weather.astype({
                'temperature_avg': 'float', 'temperature_min': 'float',
                'temperature_max': 'float', 'precipitation': 'float', 'wind_speed': 'float'
            })[['date_id', 'region_id', 'temperature_avg', 'temperature_min', 'temperature_max', 'precipitation', 'wind_speed']]

            with engine.connect() as conn:
                date_ids = [int(x) for x in df_weather['date_id'].unique()]
                conn.execute(
                    text("DELETE FROM dbo.FactWeather WHERE date_id IN :date_ids"),
                    {"date_ids": tuple(date_ids)}
                )
                conn.commit()

            df_weather.to_sql("FactWeather", engine, if_exists="append", index=False, schema="dbo")
            print(f"FactWeather cargado exitosamente: {len(df_weather)} filas insertadas.\n")
        else:
            print("Open-Meteo no devolvió registros nuevos para el rango solicitado.\n")
            df_weather = pd.DataFrame()

except Exception as e:
    print(f"Error en FactWeather: {e}\n")


# =========================================================
# 4. FACT PRODUCTION (Híbrido: Portal Oficial con Fallback Local)
# =========================================================
try:
    print("Loading FactProduction via API / Portal Oficial...\n")

    ultima_sql = pd.read_sql(
        "SELECT MAX(date_id) AS ultima_fecha FROM dbo.FactProduction", 
        engine
    )["ultima_fecha"][0]

    download_url = "http://datos.energia.gob.ar/dataset/c846e79c-026c-4040-897f-1ad3543b407c/resource/b5b58cdc-9e07-41f9-b392-fb9ec68b0725/download/produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    df_raw = None

    print(f"Intentando descargar desde: {download_url}")
    try:
        r_csv = requests.get(download_url, headers=headers, verify=False, timeout=180, stream=True)
        if r_csv.status_code == 200:
            usecols = ["anio", "mes", "prod_pet", "prod_gas", "provincia", "sub_tipo_recurso"]
            df_raw = pd.read_csv(
                io.BytesIO(r_csv.content),
                sep=None,
                engine="python",
                usecols=lambda c: c.lower() in usecols
            )
            df_raw.columns = [c.lower() for c in df_raw.columns]
            print("Descarga remota completada con éxito.")
        else:
            print(f"Servidor oficial no disponible (HTTP {r_csv.status_code}).")
    except Exception as net_err:
        print(f"Aviso de red al descargar ({net_err}).")

    # Fallback al archivo local si la descarga remota falló
    if df_raw is None:
        if os.path.exists(FALLBACK_DATA_PATH):
            print(f"Activando fallback a archivo local: {os.path.basename(FALLBACK_DATA_PATH)}")
            df_local = pd.read_excel(FALLBACK_DATA_PATH, skiprows=6)
            df_raw = df_local.rename(columns={
                "Desde": "start_date",
                "Petróleo (m3)": "prod_pet",
                "Gas (Miles de m3)": "prod_gas"
            })
            df_raw["start_date"] = pd.to_datetime(df_raw["start_date"], errors="coerce")
            df_raw = df_raw.dropna(subset=["start_date"])
            df_raw["anio"] = df_raw["start_date"].dt.year
            df_raw["mes"] = df_raw["start_date"].dt.month
            df_raw["provincia"] = "Neuquén"
            df_raw["sub_tipo_recurso"] = "NO CONVENCIONAL"
        else:
            print(f"No se encontró archivo local de respaldo en: {FALLBACK_DATA_PATH}")
            df_raw = pd.DataFrame()

    if not df_raw.empty:
        if "provincia" in df_raw.columns:
            df_raw = df_raw[df_raw["provincia"].str.contains("Neuqu", case=False, na=False)]

        df_raw["date_id"] = (
            df_raw["anio"].astype(str) + 
            df_raw["mes"].astype(str).str.zfill(2) + 
            "01"
        ).astype(int)

        if pd.notnull(ultima_sql):
            df_prod = df_raw[df_raw["date_id"] > int(ultima_sql)].copy()
        else:
            df_prod = df_raw.copy()

        if df_prod.empty:
            print("No hay nuevos registros de producción para cargar.\n")
        else:
            is_unconv = df_prod["sub_tipo_recurso"].str.contains("SHALE|TIGHT|NO CONVENCIONAL", case=False, na=False)

            df_u_oil = df_prod[is_unconv].groupby("date_id", as_index=False)["prod_pet"].sum()
            df_u_oil["production_type_id"] = prodtype_map["Unconventional Oil"]
            df_u_oil["production_value"] = df_u_oil["prod_pet"]
            df_u_oil["unit"] = "m3/day"

            df_u_gas = df_prod[is_unconv].groupby("date_id", as_index=False)["prod_gas"].sum()
            df_u_gas["production_type_id"] = prodtype_map["Unconventional Gas"]
            df_u_gas["production_value"] = df_u_gas["prod_gas"]
            df_u_gas["unit"] = "thousand m3/day"

            df_c_oil = df_prod[~is_unconv].groupby("date_id", as_index=False)["prod_pet"].sum()
            df_c_oil["production_type_id"] = prodtype_map["Oil Production"]
            df_c_oil["production_value"] = df_c_oil["prod_pet"]
            df_c_oil["unit"] = "m3/day"

            df_c_gas = df_prod[~is_unconv].groupby("date_id", as_index=False)["prod_gas"].sum()
            df_c_gas["production_type_id"] = prodtype_map["Gas Production"]
            df_c_gas["production_value"] = df_c_gas["prod_gas"]
            df_c_gas["unit"] = "thousand m3/day"

            parts = [df for df in [df_u_oil, df_u_gas, df_c_oil, df_c_gas] if not df.empty]
            df_final = pd.concat(parts, ignore_index=True)
            df_final["region_id"] = region_map["Neuquén Province"]

            df_final = df_final.sort_values(["production_type_id", "date_id"])
            df_final["monthly_change"] = df_final.groupby("production_type_id")["production_value"].diff()
            df_final["monthly_change_pct"] = df_final.groupby("production_type_id")["production_value"].pct_change() * 100
            df_final["year_over_year_change_pct"] = df_final.groupby("production_type_id")["production_value"].pct_change(periods=12) * 100

            df_final = df_final.astype({
                "date_id": "int",
                "region_id": "int",
                "production_type_id": "int",
                "production_value": "float",
                "unit": "str",
                "monthly_change": "float",
                "monthly_change_pct": "float",
                "year_over_year_change_pct": "float"
            })[[
                "date_id", "region_id", "production_type_id", "production_value",
                "unit", "monthly_change", "monthly_change_pct", "year_over_year_change_pct"
            ]]

            # Limpieza idempotente por lotes de combinaciones únicas
            with engine.connect() as conn:
                keys_to_delete = df_final[["date_id", "region_id", "production_type_id"]].drop_duplicates().to_dict(orient="records")
                for key in keys_to_delete:
                    conn.execute(
                        text("""
                            DELETE FROM dbo.FactProduction
                            WHERE date_id = :date_id
                              AND region_id = :region_id
                              AND production_type_id = :production_type_id
                        """),
                        key
                    )
                conn.commit()

            df_final.to_sql("FactProduction", engine, if_exists="append", index=False, schema="dbo")
            print(f"FactProduction cargado exitosamente: {len(df_final)} filas insertadas.\n")

except Exception as e:
    print(f"Error en FactProduction: {e}\n")


# =========================================================
# FINAL VALIDATION & ADAPTIVE ALERTING
# =========================================================
try:
    print("=" * 60)
    print("FINAL DATABASE VALIDATION")
    print("=" * 60)

    for table in ["FactEnergyPrices", "FactExchangeRate", "FactWeather", "FactProduction"]:
        rows = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM dbo.{table}", engine)
        print(f"{table}: {rows['cnt'][0]} rows (total en SQL)")

    print("=" * 60)
    print("FINAL DATE VALIDATION & SLA CHECK")
    print("=" * 60)

    query = """
    SELECT 'FactEnergyPrices' AS tabla, MAX(date_id) AS ultima_fecha FROM dbo.FactEnergyPrices
    UNION ALL
    SELECT 'FactExchangeRate', MAX(date_id) FROM dbo.FactExchangeRate
    UNION ALL
    SELECT 'FactWeather', MAX(date_id) FROM dbo.FactWeather
    UNION ALL
    SELECT 'FactProduction', MAX(date_id) FROM dbo.FactProduction;
    """
    df_dates = pd.read_sql(query, engine)
    df_dates['ultima_fecha'] = pd.to_datetime(df_dates['ultima_fecha'], format='%Y%m%d')
    df_dates['dias_atraso'] = (pd.to_datetime("today").normalize() - df_dates['ultima_fecha']).dt.days

    print(df_dates.to_string(index=False))
    print("-" * 60)

    sla_atraso = {
        'FactEnergyPrices': 4,
        'FactExchangeRate': 4,
        'FactWeather': 2,
        'FactProduction': 95
    }

    alertas = 0
    for _, row in df_dates.iterrows():
        limite = sla_atraso.get(row['tabla'], 3)
        if row['dias_atraso'] > limite:
            print(f"⚠️ ALERTA: {row['tabla']} tiene {row['dias_atraso']} días de atraso (umbral permitido: {limite} días).")
            alertas += 1

    if alertas == 0:
        print("✔ Todas las tablas se encuentran dentro del SLA operativo.")

    print("\nMASTER ETL COMPLETED SUCCESSFULLY.")

except Exception as e:
    print(f"Error en Validación Final: {e}")