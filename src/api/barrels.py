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
        inventory = connection.execute(sqlalchemy.text("SELECT ml_green_potions, gold FROM global_inventory")).fetchall()
    #assumes row 1 in green potions and that the barrels are all green.
    for barrel in barrels_delivered:  
#        inventory[0][0] += barrel.ml_per_barrel*barrel.quantity            Why doesn't this work?!?!? says type doesn't support combined assignment.
        newmlGreen = inventory[0][0] + barrel.ml_per_barrel*barrel.quantity
        newTotalGold = inventory[0][1] - barrel.price*barrel.quantity
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET ml_green_potions = {newmlGreen}, gold = {newTotalGold}"))
    """Status of order"""
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
# Gets called once a day
# return [ {
#           "sku": String
#           "quantity": int
# }]
    print(f"wholesale_catalog: {wholesale_catalog}")
    """Purchases based solely on inventory status."""
    barrelPlan = []
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).fetchall()
    #check if each barrel 
    for barrel in wholesale_catalog:
        if (barrel.sku == "SMALL_GREEN_BARREL" and barrel.quantity > 0 and barrel.price <= inventory[0][1] and inventory[0][0] < 10):
            barrelPlan.append({
                "sku": barrel.sku,
                "quantity": 1
            })
            
    """Description of order"""
    print(f"barrelPlan: {barrelPlan}")
    return barrelPlan

