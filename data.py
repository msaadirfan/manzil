import pandas as pd
from sqlalchemy import create_engine

# ==============================
# 1️⃣ Database connection
# ==============================
username = "msaadirfan"
password = "Saadpmc9."
host = "localhost"
port = "5432"
database = "manzil_db"

engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")

# ==============================
# 2️⃣ Load CSV / TXT data
# ==============================
stations = pd.read_csv("stations.txt")
routes = pd.read_csv("routes.txt")

print("Stations preview:\n", stations.head())
print("Routes preview:\n", routes.head())

# ==============================
# 3️⃣ Insert stations
# ==============================
stations.to_sql("routefinder_station", engine, if_exists="append", index=False)
print(f"Inserted {len(stations)} stations into routefinder_station")

# ==============================
# 4️⃣ Create station lookup
# ==============================
station_lookup = pd.read_sql("SELECT station_id FROM routefinder_station", engine)
print("Station lookup:\n", station_lookup.head())

# ==============================
# 5️⃣ Merge routes with stations
# ==============================
# Merge from_station
routes = routes.merge(
    station_lookup,
    left_on="from_station_id",
    right_on="station_id",
    how="left"
).rename(columns={"station_id": "from_station_fk"})

# Merge to_station
routes = routes.merge(
    station_lookup,
    left_on="to_station_id",
    right_on="station_id",
    how="left"
).rename(columns={"station_id": "to_station_fk"})

# ==============================
# 6️⃣ Prepare final routes
# ==============================
routes_final = routes[["route_id", "from_station_fk", "to_station_fk", "distance_kms"]].copy()
routes_final.rename(columns={
    "from_station_fk": "from_station_id",
    "to_station_fk": "to_station_id"
}, inplace=True)

print("Routes ready for insert:\n", routes_final.head())

# ==============================
# 7️⃣ Insert routes
# ==============================
routes_final.to_sql("routefinder_route", engine, if_exists="append", index=False)
print(f"Inserted {len(routes_final)} routes into routefinder_route")
