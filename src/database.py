import os
import dotenv
from sqlalchemy import create_engine

from src import database as db
import sqlalchemy

def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")

engine = create_engine(database_connection_url(), pool_pre_ping=True)
# metadata_obj = sqlalchemy.MetaData()
# cart_items = sqlalchemy.Table("cart_items", metadata_obj, autoload_with=db.engine)
# carts = sqlalchemy.Table("carts", metadata_obj, autoload_with=db.engine)
# customer_visit = sqlalchemy.Table("customer_visit", metadata_obj, autoload_with=db.engine)
