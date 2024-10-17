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
        #clear each table.
        #don't delete some for record keeping.
        connection.execute(sqlalchemy.text("DELETE FROM upgrade_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM ml_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM gold_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM potion_ledger"))
        #connection.execute(sqlalchemy.text("DELETE FROM cart_items"))
        #connection.execute(sqlalchemy.text("DELETE FROM carts"))
        #connection.execute(sqlalchemy.text("DELETE FROM customer_visit"))
        #connection.execute(sqlalchemy.text("DELETE FROM potion_menu"))
        connection.execute(sqlalchemy.text("DELETE FROM transactions"))
        #connection.execute(sqlalchemy.text("DELETE FROM times"))
        
        #setup each table.
        time_id = connection.execute(sqlalchemy.text("INSERT INTO times (day, time) VALUES (\'Setup\', 0) RETURNING id")).scalar_one()
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (transaction_type, time_id, order_id) VALUES (\'Setup\', :time_id, 0) RETURNING id"), {"time_id": time_id}).scalar_one()
        connection.execute(sqlalchemy.text("INSERT INTO upgrade_ledger (transaction_id, potion_upgrades, ml_upgrades) VALUES (:transaction_id, :potion_upgrades, :ml_upgrades)"), {"transaction_id": transaction_id, "potion_upgrades": 1, "ml_upgrades": 1})
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, barrel_potion_sku, ml_type, ml_quantity, cost) VALUES (:transaction_id, :barrel_potion_sku, :ml_type, :ml_quantity, :cost)"), 
                           [
                                {"transaction_id": transaction_id, "barrel_potion_sku": "setup0", "ml_type": 0, "ml_quantity": 0, "cost": 0},
                                {"transaction_id": transaction_id, "barrel_potion_sku": "setup1", "ml_type": 1, "ml_quantity": 0, "cost": 0},
                                {"transaction_id": transaction_id, "barrel_potion_sku": "setup2", "ml_type": 2, "ml_quantity": 0, "cost": 0},
                                {"transaction_id": transaction_id, "barrel_potion_sku": "setup3", "ml_type": 3, "ml_quantity": 0, "cost": 0}
                            ])
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, gold_quantity) VALUES (:transaction_id, :gold_quantity)"), {"transaction_id": transaction_id, "gold_quantity": 100})
        potion_menu = []
        for r in range(3):
            for g in range(3):
                for b in range(3):
                    for d in range(3):
                        if r+g+b+d == 2:
                            potion_menu.append({
                                "sku": f"{r*50}R_{g*50}G_{b*50}B_{d*50}D",
                                "name": "Mystery potion",
                                "red": r*50,
                                "green": g*50,
                                "blue": b*50,
                                "dark": d*50,
                                "current_price": 0
                            })
    #    connection.execute(sqlalchemy.text("INSERT INTO potion_menu (sku, name, red, green, blue, dark, current_price) VALUES (:sku, :name, :red, :green, :blue, :dark, :current_price)"), potion_menu)    
    #     connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (transaction_id, sku, potion_quantity, sales_price) VALUES (:transaction_id, :sku, :potion_quantity, :sales_price)"),
    #                        [
    #                             {"transaction_id": transaction_id, "sku": "0R_0G_0B_100D", "potion_quantity": 0, "sales_price": 0},
    #                             {"transaction_id": transaction_id, "sku": "0R_0G_100B_0D", "potion_quantity": 0, "sales_price": 0},
    #                             {"transaction_id": transaction_id, "sku": "0R_100G_0B_0D", "potion_quantity": 0, "sales_price": 0},
    #                             {"transaction_id": transaction_id, "sku": "100R_0G_0B_0D", "potion_quantity": 0, "sales_price": 0}
    #                         ])
    return "OK"

