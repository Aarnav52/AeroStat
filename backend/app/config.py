import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

config = Config()
