#my imports
import functools
import time
#his imports
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
    ml_ledger = []
    gold_quantity = 0
    with db.engine.begin() as connection:
        #get time and enter transaction
        time_id = connection.execute(sqlalchemy.text("SELECT MAX(id) FROM times")).scalar_one()
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (transaction_type, time_id, order_id) VALUES (:transaction_type, :time_id, :order_id) RETURNING id"), {"transaction_type": "barreler", "time_id": time_id, "order_id": order_id}).fetchone()[0]
        #collect information.
        for barrel in barrels_delivered:
            ml_ledger.append(
                {
                "transaction_id": transaction_id,
                "barrel_sku": barrel.sku,
                "ml_type": barrel.potion_type.index(1),
                "ml_quantity": barrel.ml_per_barrel*barrel.quantity,
                "cost": barrel.price*barrel.quantity
                })
            gold_quantity -= barrel.price*barrel.quantity
        #INSERT to ml_ledger
        connection.execute(sqlalchemy.text("INSERT INTO ml_ledger (transaction_id, barrel_potion_sku, ml_type, ml_quantity, cost) VALUES (:transaction_id, :barrel_sku, :ml_type, :ml_quantity, :cost)"), ml_ledger)
        #INSERT to gold_ledger.
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, gold_quantity) VALUES (:transaction_id, :gold_quantity)"), {"transaction_id": transaction_id, "gold_quantity": gold_quantity})

    return "OK"


@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """Request Body"""
    print(f"wholesale_catalog: {wholesale_catalog}")

    """
    Does not make purchases based on the day, hour.
    """

    """purchases based solely on inventory status."""
    #How much of a full inventory should be each potiontype.
    barrel_plan = []

    #Get information about current shop and inventory status.
    with db.engine.begin() as connection:
    #    potion_storage = connection.execute(sqlalchemy.text("SELECT stock FROM potion_storage")).fetchall()
    #    ml_storage = connection.execute(sqlalchemy.text("SELECT potion_type, ml_stored FROM ml_storage ORDER BY potion_type ASC")).fetchall()
    #    shop_info = connection.execute(sqlalchemy.text("SELECT gold, ml_capacity, potion_capacity FROM shop_info")).fetchone()

        shop_capacity = connection.execute(sqlalchemy.text("SELECT 10000*SUM(ml_upgrades) AS ml_capacity, 50*SUM(potion_upgrades) AS potion_capacity FROM upgrade_ledger;")).fetchone()
        ml_storage = connection.execute(sqlalchemy.text("SELECT ml_type, SUM(ml_quantity) AS total_ml_quantity FROM ml_ledger GROUP BY ml_type ORDER BY total_ml_quantity")).fetchall()
        total_gold = connection.execute(sqlalchemy.text("SELECT SUM(gold_quantity) FROM gold_ledger")).fetchone()

    #keeping track of multiple barrel purchase stats.
    subtotal_gold = 0
    purchased_ml = [0, 0, 0, 0]
    black_list = [False, False, False, False]
    
    perc_type = 0.25
    #buying_offset_ml delays buying barrels for a specific type by so many ml. This ensures the shop doesn't only top off mls but buys builk for better price/ml
    if shop_capacity[0] >= 60000: #Waits to buy large barrels. buys dark barrels so capcpacity accounts for 4 types.
        buying_offset_ml = 10000
        #perc_type is default 25%
    elif shop_capacity[0] >= 40000: #Waits to buy medium barrels. buys dark barrels so capacity accounts for 4 types.
        buying_offset_ml = 2500
        #perc_type is default 25%
    elif shop_capacity[0] >= 20000: #Wait to buy medium barrels. no dark barrels so capacity accounts for 3 types.
        buying_offset_ml = 2500
        black_list[3] = True
        perc_type = 0.30
    else: 
        if functools.reduce(lambda a, b: a + b[1], ml_storage, 0) < 1000:
            buying_offset_ml = 501 #allows for more diverse buying by restricting buying medium barrels at the start
        else:
            buying_offset_ml = 0 #allows for medium barrel buying.
        black_list[3] = True 
        #when max ml per type is 2500 at the start. this prevents the buying of medium barrels to get diverse potion types faster.
        perc_type = 0.30

    #each potion type shouldn't take up more than this in sotrage.
    #with information make informed decision about what to get.
    #if total ml stored or total potions stored is at 90% capacity don't buy anything and save up for shop upgrade. might want to change to compare to a fixed value in the future
    #if functools.reduce(lambda total, current: total + current[1], ml_storage, 0) >= 0.90*shop_capacity[0] or functools.reduce(lambda total, current: total + current[0], potion_storage, 0) >= 0.90*shop_capacity[1]:
    #    return barrel_plan 

    #purchase barrels by lowest type currently stocked and highest ml barrel currently affordable. recheck order and gold after every "purchase" 
    #sort catalogue by potion_type and then ml_per_barrel.
    wholesale_catalog = sorted(wholesale_catalog, key=lambda b: (b.potion_type, b.ml_per_barrel), reverse = True)
    
    lowest_index = 0
    while not all(black_list): #if all of blacklist is True then break out of while.
        ml_storage = sorted(ml_storage, key=lambda a: a[1] + purchased_ml[a[0]])
        for i in range(len(ml_storage)):
            if black_list[ml_storage[i][0]] == False:
                lowest_index = i
                break
        
        barrel_purchased = False 
        for barrel in wholesale_catalog:
            if(barrel.potion_type[ml_storage[lowest_index][0]] == 1 and #barrel is correct type
               subtotal_gold + barrel.price <= total_gold[0] and #shop has gold for the purchase
               ml_storage[lowest_index][1] + purchased_ml[ml_storage[lowest_index][0]] + barrel.ml_per_barrel <=  perc_type*float(shop_capacity[0])-buying_offset_ml):  #purchase doesn't overfill the potion types alloted space. 
                if (functools.reduce(lambda a,b, barrel_sku = barrel.sku: a or b.get("sku") == barrel_sku, barrel_plan, False)):#if barrel is already in the plan.
                    for i in range(len(barrel_plan)): #get the index of barrel.
                        if barrel_plan[i].get("sku") == barrel.sku: plan_index = i
                    if barrel.quantity > barrel_plan[plan_index].get("quantity"): #PURCHASE: catalog entry has enough quantity.
                        barrel_plan[plan_index].update({"quantity": barrel_plan[plan_index].get("quantity") + 1}) #update the quantity of the barrel in barrel_plan.
                        barrel_purchased = True
                        subtotal_gold += barrel.price
                        purchased_ml[ml_storage[lowest_index][0]] += barrel.ml_per_barrel
                        break
                    else:
                        black_list[ml_storage[lowest_index][0]] = True #purchased all of a specific sku so don't buy more.
                        break #no need to check other barrels to buy 1 since I've bought all of one sku already and the potion_type is already on the balck_list
                else:
                    barrel_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
                    barrel_purchased = True
                    subtotal_gold += barrel.price
                    purchased_ml[ml_storage[lowest_index][0]] += barrel.ml_per_barrel
                    break
        if barrel_purchased == False:
            black_list[ml_storage[lowest_index][0]] = True
    
    print(f"barrel_plan: {barrel_plan}")
    return barrel_plan
 