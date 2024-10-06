import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """Request Body"""
    print(f"potions_delivered: {potions_delivered}")
    print(f"order_id: {order_id}")

    """Update inventory with the new potions and"""
    with db.engine.begin() as connection:
        for potion in potions_delivered:
            for i in range(4): #for each of the 4 potion_type in potion
                connection.execute(sqlalchemy.text(f"UPDATE ml_storage SET ml_stored = ml_stored - {potion.potion_type[i]*potion.quantity} WHERE potion_type = {i}"))
            #update to new current stock with previous stock plus delivered. 
            connection.execute(sqlalchemy.text(f"UPDATE potion_storage SET stock = stock + {potion.quantity} WHERE (red, green, blue, dark) = ({potion.potion_type[0]}, {potion.potion_type[1]}, {potion.potion_type[2]}, {potion.potion_type[3]})"))

    return "Done"

#creates a plan to mix an amount of potions each with a potion_type and quanity.
@router.post("/plan")
def get_bottle_plan():
    """Go from barrel to bottle."""
    potion_plan = []

    potion_type = [0,0,0,0]
    with db.engine.begin() as connection:
        ml_storage = connection.execute(sqlalchemy.text("SELECT ml_stored FROM ml_storage ORDER BY potion_type ASC")).fetchall()
        max_potion_quantity = connection.execute(sqlalchemy.text("SELECT potion_capacity FROM shop_info")).fetchone()[0]//4 #determins the max quantity of each basic potion type
        for i in range(4): #for each basic potion type
            potion_type[i] = 100
            potion = connection.execute(sqlalchemy.text(f"SELECT stock FROM potion_storage WHERE red = {potion_type[0]} AND green = {potion_type[1]} AND blue = {potion_type[2]} AND dark = {potion_type[3]}")).fetchone()
            if potion[0] < max_potion_quantity and ml_storage[i][0] >= 100:
                potion_plan.append({
                                    "potion_type": potion_type.copy(),
                                    "quantity": ml_storage[i][0]//100 if potion[0]+(ml_storage[i][0]//100) <= max_potion_quantity else max_potion_quantity-potion[0] 
                })
            potion_type[i] = 0

    """Response"""
    print(f"potion_plan: {potion_plan}")
    return potion_plan

if __name__ == "__main__":
    print(get_bottle_plan())