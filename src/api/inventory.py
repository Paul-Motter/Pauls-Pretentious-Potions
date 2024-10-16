import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    with db.engine.begin() as connection:
        number_of_potions = connection.execute(sqlalchemy.text("SELECT  COALESCE(sum(potion_quantity), 0) FROM potion_ledger")).scalar_one()
        ml_in_barrels = connection.execute(sqlalchemy.text("SELECT sum(ml_quantity) FROM ml_ledger")).scalar_one()
        gold = connection.execute(sqlalchemy.text("SELECT sum(gold_quantity) FROM gold_ledger")).scalar_one()

    return {"number_of_potions": number_of_potions, "ml_in_barrels": ml_in_barrels, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 4,
        "ml_capacity": 4
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        time_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM times")).scalar_one()
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (transaction_type, time_id, order_id) VALUES (:transaction_type, :time_id, :order_id) RETURNING id"), {"transaction_type": "upgrade", "time_id": time_id, "order_id": order_id}).scalar_one()
        connection.execute(sqlalchemy.text("INSERT INTO upgrade_ledger (transaction_id, potion_upgrades, ml_upgrades) VALUES (:transaction_id, :potion_upgrades, :ml_upgrades)"), {"transaction_id": transaction_id, "potion_upgrades": capacity_purchase.potion_capacity, "ml_upgrades": capacity_purchase.ml_capacity})
        


    return "OK"
