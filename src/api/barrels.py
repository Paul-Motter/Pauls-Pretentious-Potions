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

    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):

    with db.engine.begin() as connection:
        inventory = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    #inventory.fetchone()[0]
    #inventory.fetchall()[0][1]
    """ """
    #print("Inventory\n" + inventory)
    #print("Wolesale Catalog\n" + wholesale_catalog)

    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": inventory[0][1],
        }
    ]

