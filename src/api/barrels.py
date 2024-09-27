import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """Checks each delivery to update ml stored and subtract price. Assumes all barrels are green potions."""
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchall()
    #assumes row 1 in green potions and that the barrels are all green.
    for barrel in barrels_delivered:  
        inventory[0][2] += barrel.ml_per_barrel*barrel.quantity
        inventory[0][3] -= barrel.price*barrel.quantity
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET ml_green_potions = {inventory[0][2]}, gold = {inventory[0][3]}"))
    """Status of order"""
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Purchases based solely on inventory status."""
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchall()
    #Sanity check if purchase will work.
    containsSmallGreenBarrel = False
    for barrel in wholesale_catalog:
        if (barrel.sku == "SMALL_GREEN_BARREL" and barrel.quantity > 0): containsSmallGreenBarrel = True
    #put in purchase quantity
    if (inventory[0][1] < 10 and containsSmallGreenBarrel):
        quantity = 1
    """Description of order"""
    print(f"quantity: {quantity}")
    return [
        {
            "sku": "SMALL_GREEN_BARREL",
            "quantity": quantity,
        }
    ]

