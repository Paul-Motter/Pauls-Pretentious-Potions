import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("UPDATE shop_info SET gold = 100, ml_capacity = 10000, potion_capacity = 50"))
        connection.execute(sqlalchemy.text("UPDATE ml_storage SET ml_stored = 0, total_ml_bought = 0, total_gold_spent = 0"))
        connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
        connection.execute(sqlalchemy.text("DELETE FROM customers"))
        connection.execute(sqlalchemy.text("DELETE FROM time"))
        connection.execute(sqlalchemy.text("DELETE FROM my_catalog"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_storage"))
        connection.execute(sqlalchemy.text("INSERT INTO potion_storage (red, green, blue, dark, sku, stock, total_sold, name, price) VALUES (0, 0, 0, 100, '0R_0G_0B_100D', 0, 0, 'Dark_100', 0), (0, 0, 100, 0, '0R_0G_100B_0D', 0, 0, 'Blue_100', 0), (0, 100, 0, 0, '0R_100G_0B_0D', 0, 0, 'Green_100', 0), (100, 0, 0, 0, '100R_0G_0B_0D', 0, 0, 'Red_100', 0);"))
        #connection.execute(sqlalchemy.text("DELETE FROM potion_storage WHERE red != 100 OR green != 100 OR blue != 100 OR dark != 100"))
        #connection.execute(sqlalchemy.text("UPDATE potion_storage SET stock = 0, total_sold = 0, price = 0"))

    return "OK"

