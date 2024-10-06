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
    with db.engine.begin() as connection:
        for barrel in barrels_delivered:  
            storage_index = barrel.potion_type.index(1) #which index in potion type has the value 1.
            #update ml_storage with current barrel.
            connection.execute(sqlalchemy.text(f"UPDATE ml_storage SET ml_stored = ml_stored + {barrel.ml_per_barrel*barrel.quantity} WHERE potion_type = {storage_index}"))
             #update gold with current barrel.
            connection.execute(sqlalchemy.text(f"UPDATE shop_info SET gold = gold - {barrel.price*barrel.quantity}"))

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
        potion_storage = connection.execute(sqlalchemy.text("SELECT stock FROM potion_storage")).fetchall()
        ml_storage = connection.execute(sqlalchemy.text("SELECT potion_type, ml_stored FROM ml_storage ORDER BY potion_type ASC")).fetchall()
        shop_info = connection.execute(sqlalchemy.text("SELECT gold, ml_capacity, potion_capacity FROM shop_info")).fetchone()

    #keeping track of multiple barrel purchase stats.
    subtotal_gold = 0
    purchased_ml = [0, 0, 0, 0]
    black_list = [False, False, False, False]
    
    #buying_offset_ml delays buying barrels for a specific type by so many ml. This ensures the shop doesn't only top off mls but buys builk for better price/ml
    if shop_info[1] >= 60000: buying_offset_ml = 10000
    elif shop_info[1] >= 20000: buying_offset_ml = 2500
    else: buying_offset_ml = 0
    perc_type = 0.25 #each potion type shouldn't take up more than this in sotrage.

    #with information make informed decision about what to get.
    #if total ml stored or total potions stored is at 90% capacity don't buy anything and save up for shop upgrade. might want to change to compare to a fixed value in the future
    if functools.reduce(lambda total, current: total + current[1], ml_storage, 0) >= 0.90*shop_info[1] or functools.reduce(lambda total, current: total + current[0], potion_storage, 0) >= 0.90*shop_info[2]:
        return barrel_plan 

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
               subtotal_gold + barrel.price <= shop_info[0] and #shop has gold for the purchase
               ml_storage[lowest_index][1] + purchased_ml[ml_storage[lowest_index][0]] + barrel.ml_per_barrel <=  perc_type*shop_info[1]-buying_offset_ml):  #purchase doesn't overfill the potion types alloted space. 
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
 