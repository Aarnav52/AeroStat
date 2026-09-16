import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
load_dotenv()

user = os.getenv("user")
password = quote_plus(os.getenv("password"))
host = os.getenv("host")
port = os.getenv("port")
database = os.getenv("database")

DATABASE_URL = (
    f"postgresql://{user}:{password}@{host}:{port}/{database}"
)

print("Host:", host)
print("Port:", port)
print("User:", user)
print("Connecting...")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT NOW();"))
        print("\nDATABASE CONNECTION SUCCESSFUL")
except Exception as e:
    print("\nDATABASE CONNECTION FAILED")
    print(e)

query = """
SELECT *
FROM flight_observations_raw
LIMIT 10;
"""

df = pd.read_sql(query, engine)

print(df)
print("\nShape:", df.shape)