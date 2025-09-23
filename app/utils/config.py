import os
from dotenv import load_dotenv
load_dotenv()

# For PostgreSQL connection
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "waiwan_admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "1234")
PG_DBNAME = os.getenv("PG_DBNAME", "waiwan_db")

# For Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
PRESENCE_TTL_SECONDS = int(os.getenv("PRESENCE_TTL_SECONDS", "60"))

MODEL_NAME = os.getenv("MODEL_NAME", "")

# AUTH JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "43200"))
JWT_ISSUER = os.getenv("JWT_ISSUER", "waiwan-app")

