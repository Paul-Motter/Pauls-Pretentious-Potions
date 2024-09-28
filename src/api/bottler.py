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

    """Update inventory with the new potions and spent ml"""
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions, ml_green_potions FROM global_inventory")).fetchall()
    #assumes all potions in delivery are green so all ml and potions update the green.
    for potion_delivery in potions_delivered:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {inventory[0][0] + potion_delivery.quantity}, ml_green_potions = {inventory[0][1] - potion_delivery.quantity*100}"))

    return "Done"

#creates a plan to mix an amount of potions each with a potion_type and quanity.
@router.post("/plan")
def get_bottle_plan():
    """Go from barrel to bottle."""
    potion_plan = []
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions, ml_green_potions FROM global_inventory")).fetchall()
    green_potion_potential = inventory[0][1]//100
    if (inventory[0][0] < 50 and green_potion_potential > 0 ):
        potion_plan.append({
            "potion_type": [0, 100, 0, 0],
            "quanitity": green_potion_potential if inventory[0][0]+green_potion_potential <= 50 else 50-inventory[0][0],
        })


    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    # Initial logic: bottle all barrels into red potions.
    """Response"""
    print(f"potion_plan: {potion_plan}")
    return potion_plan

if __name__ == "__main__":
    print(get_bottle_plan())