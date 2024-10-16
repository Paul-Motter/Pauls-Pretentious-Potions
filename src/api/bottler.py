from functools import reduce
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
        time_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM times")).scalar_one()
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (transaction_type, time_id, order_id) VALUES (:transaction_type, :time_id, :order_id) RETURNING id"), {"transaction_type": "bottler", "time_id": time_id, "order_id": order_id}).scalar_one()
        price_per_ml = map(lambda a: a[0], connection.execute(sqlalchemy.text("SELECT sum(cost)/COALESCE(NULLIF(SUM(ml_quantity), 0), 1) AS cost_per_ml FROM ml_ledger WHERE ml_quantity >= 0 GROUP BY ml_type ORDER BY ml_type ASC")).fetchall())
        potion_ledger = []
        ml_ledger = []
        for potion in potions_delivered:
            potion_ledger.append({
                "transaction_id": transaction_id,
                "sku": f"{potion.potion_type[0]}R_{potion.potion_type[1]}G_{potion.potion_type[2]}B_{potion.potion_type[3]}D",
                "potion_quantity": potion.quantity,
                "sales_price": 2*reduce(lambda a,b: a + b[0]*b[1], zip(price_per_ml, potion.potion_type), 0)
            })
            for ml_type in range(len(potion.potion_type)):
                if potion.potion_type[ml_type] != 0:
                    ml_ledger.append({
                        "transaction_id": transaction_id,
                        "ml_type": ml_type,
                        "ml_quantity": -potion.potion_type[ml_type]*potion.quantity,
                        "potion_sku": f"{potion.potion_type[0]}R_{potion.potion_type[1]}G_{potion.potion_type[2]}B_{potion.potion_type[3]}D",
                        "cost": 0
                    })

        connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (transaction_id, sku, potion_quantity, sales_price) VALUES (:transaction_id, :sku, :potion_quantity, :sales_price)"), potion_ledger)
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, ml_type, ml_quantity, barrel_potion_sku, cost) VALUES (:transaction_id, :ml_type, :ml_quantity, :potion_sku, :cost)"), ml_ledger)
        
    return "Done"

#creates a plan to mix an amount of potions each with a potion_type and quanity.
@router.post("/plan")
def get_bottle_plan():
    """Go from barrel to bottle."""
    potion_plan = []

    potion_type = [0,0,0,0]
    with db.engine.begin() as connection:
        ml_storage = connection.execute(sqlalchemy.text("SELECT sum(ml_quantity) FROM ml_ledger GROUP BY ml_type ORDER BY ml_type ASC")).fetchall()
        max_potion_quantity = connection.execute(sqlalchemy.text("SELECT 50*sum(potion_upgrades) FROM upgrade_ledger")).scalar_one()//4 #determins the max quantity of each basic potion type
        for i in range(4): #for each basic potion type
            potion_type[i] = 100
            potion = connection.execute(sqlalchemy.text(f"SELECT sum(potion_quantity) FROM potion_ledger JOIN potion_menu ON potion_ledger.sku = potion_menu.sku WHERE red = {potion_type[0]} AND green = {potion_type[1]} AND blue = {potion_type[2]} AND dark = {potion_type[3]}")).scalar_one()
            if potion < max_potion_quantity and ml_storage[i][0] >= 100:
                potion_plan.append({
                                    "potion_type": potion_type.copy(),
                                    "quantity": ml_storage[i][0]//100 if potion+(ml_storage[i][0]//100) <= max_potion_quantity else max_potion_quantity-potion 
                })
            potion_type[i] = 0

    """Response"""
    print(f"potion_plan: {potion_plan}")
    return potion_plan

if __name__ == "__main__":
    print(get_bottle_plan())