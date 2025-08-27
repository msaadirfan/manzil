import pandas as pd
from sqlalchemy import create_engine

# Database Connection
username = "msaadirfan"
password = "Saadpmc9."
host = "localhost"
port = "5432"
database = "manzil_db"


engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")


stations = pd.read_csv("stations.txt")
routes = pd.read_csv("routes.txt")

print("Stations preview:\n", stations.head())
print("Routes preview:\n", routes.head())


stations.to_sql("routefinder_station", engine, if_exists="append", index=False)
print(f"Inserted {len(stations)} stations into routefinder_station")


station_lookup = pd.read_sql("SELECT id, station_id FROM routefinder_station", engine)
print("Station lookup:\n", station_lookup.head())


routes = routes.merge(
    station_lookup,
    left_on="from_station_id",
    right_on="station_id"
).rename(columns={"id": "from_station_fk"}).drop(columns=["station_id"])

routes = routes.merge(
    station_lookup,
    left_on="to_station_id",
    right_on="station_id"
).rename(columns={"id": "to_station_fk"}).drop(columns=["station_id"])

routes_final = routes[["route_id", "from_station_fk", "to_station_fk", "distance_kms"]].copy()
routes_final.rename(columns={
    "from_station_fk": "from_station_id",
    "to_station_fk": "to_station_id"
}, inplace=True)

print("Routes (ready for insert):\n", routes_final.head())

routes_final.to_sql("routefinder_route", engine, if_exists="append", index=False)
print(f"Inserted {len(routes_final)} routes into routefinder_route")
