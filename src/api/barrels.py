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
    """Request Body"""
    print(f"barrels_delivered: {barrels_delivered}")
    print(f"order_id: {order_id}")

    """Checks each delivery to update ml stored and subtract price. Assumes all barrels are green potions."""
    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT ml_green_potions, gold FROM global_inventory")).fetchall()
    #assumes row 1 in green potions and that the barrels are all green.
    for barrel in barrels_delivered:  
#        inventory[0][0] += barrel.ml_per_barrel*barrel.quantity            Why doesn't this work?!?!? says type doesn't support combined assignment.
        new_ml_green = inventory[0][0] + barrel.ml_per_barrel*barrel.quantity
        new_total_gold = inventory[0][1] - barrel.price*barrel.quantity
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET ml_green_potions = {new_ml_green}, gold = {new_total_gold}"))
   
    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
# Gets called once a day
# return [ {
#           "sku": String
#           "quantity": int
# }]
    """Request Body"""
    print(f"wholesale_catalog: {wholesale_catalog}")

    """Purchases based solely on inventory status."""
    #How much of a full inventory should be each potiontype.
    barrel_plan = []
    percent_type_full = [0,0,0,0]
    perc_green = 1/4
    perc_red = 1/4
    perc_blue = 1/4
    perc_dark = 1/4
    subtotal = 0

    #Get information about current shop and inventory status.
    with db.engine.begin() as connection:
        ml_inventory = connection.execute(sqlalchemy.text("SELECT potion_type, ml_sotored FROM ml_storage")).fetchall
        shop_info = connection.execute(sqlalchemy.text("SELECT gold, ml_capacity FROM shop_info")).fetchone

    #with information make informed decision about what to get.
    for ml_type in ml_inventory:
        percent_type_full[ml_type[0]] = ml_type[1]/shop_info[1] #percent of total capacity is that type.

    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).fetchall()
    #check if each barrel 
    for barrel in wholesale_catalog:
        if (barrel.sku == "SMALL_GREEN_BARREL" and barrel.quantity > 0 and barrel.price <= inventory[0][1] and inventory[0][0] < 10):
            barrel_plan.append(
                {
                    "sku": barrel.sku,
                    "quantity": 1,
                }
            )
            
    """Response"""
    print(f"barrel_plan: {barrel_plan}")
    return barrel_plan