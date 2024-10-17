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
        price_per_ml = map(lambda a: a[0], connection.execute(sqlalchemy.text("SELECT round(sum(cost)/COALESCE(NULLIF(SUM(ml_quantity), 0), 1), 2) AS cost_per_ml FROM ml_ledger WHERE ml_quantity >= 0 GROUP BY ml_type ORDER BY ml_type ASC")).fetchall())
        potion_ledger = []
        ml_ledger = []
        for potion in potions_delivered:
            potion_ledger.append({
                "transaction_id": transaction_id,
                "sku": f"{potion.potion_type[0]}R_{potion.potion_type[1]}G_{potion.potion_type[2]}B_{potion.potion_type[3]}D",
                "potion_quantity": potion.quantity,
                "sales_price": int(2*reduce(lambda a,b: a + b[0]*b[1], zip(price_per_ml, potion.potion_type), 0))
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


    ml_spent = [0,0,0,0]
    with db.engine.begin() as connection:
        #total stored ml for each type ordered by ml_type ASC
        ml_storage = connection.execute(sqlalchemy.text("SELECT sum(ml_quantity) FROM ml_ledger GROUP BY ml_type ORDER BY ml_type ASC")).fetchall()
        # [0] is max capacity for potions while [1] is max ml capacity.
        max_capacity = connection.execute(sqlalchemy.text("SELECT 50*sum(potion_upgrades), 10000*sum(ml_upgrades) FROM upgrade_ledger")).fetchone()
        #returns a list of potions and their stock in my inventory.
        potions = connection.execute(sqlalchemy.text("SELECT red, green, blue, dark, COALESCE(sum(potion_quantity), 0) AS quantity FROM potion_menu LEFT JOIN potion_ledger ON potion_menu.sku = potion_ledger.sku GROUP BY red, green, blue, dark ORDER BY quantity ASC")).fetchall()
        if max_capacity[1] >= 40000: #dark barrels will be purchased and dark potions can be made/sold.
            possible_types = 10
        else: #no dark barrels eliminates possibilities.
            possible_types = 6 
        for potion in potions: #for each basic potion type
            #check that the ml required to make at least one potion is in stock and we need more of this potion.
            if potion[4] < max_capacity[0]//possible_types and ml_storage[0][0]-ml_spent[0] >= potion[0] and ml_storage[1][0]-ml_spent[1] >= potion[1] and ml_storage[2][0]-ml_spent[2] >= potion[2] and ml_storage[3][0]-ml_spent[3] >= potion[3]:
                #finds the max possible quantity producible.
                quantity = []
                for i in range(4):
                    if potion[i] != 0:
                        quantity.append(ml_storage[i]-ml_spent[i]//potion[i])
                quantity = int(min(quantity) if potion[4]+min(quantity) <= max_capacity[0]//possible_types else (max_capacity[0]//possible_types)-potion[4])
                #append the quantity we can actually make and store onto potion_plan.
                potion_plan.append({
                                    "potion_type": [potion[0], potion[1], potion[2], potion[3]],
                                    "quantity": quantity
                })
                #update ml_spent
                for i in range(4):
                    ml_spent[i] += potion[i]*quantity

    """Response"""
    print(f"potion_plan: {potion_plan}")
    return potion_plan

if __name__ == "__main__":
    print(get_bottle_plan())