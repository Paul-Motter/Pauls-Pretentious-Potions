import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()

#sample catalogue entry
#   {
#       "sku": String ALL_CAPS
#       "name": String all_lowercase
#       "quantity": int
#       "price": int
#       "potion type": arr[4] e.g. [10,20,30,40]
#   }
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Each unique item combination must have only a single price. max of 6 potion SKUs offered at one time."""
    catalog_entries = []
    catalog_log = []
    with db.engine.begin() as connection:
        #returns a list of options in the order of highest total stock to lowest exempting those that are zero stock.
        time_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM times")).scalar_one()
        #get rid of current price
        potion_list = connection.execute(sqlalchemy.text("""SELECT potion_menu.sku, name, SUM(potion_quantity) AS quantity, red, green, blue, dark 
                                                         FROM potion_menu JOIN potion_ledger ON potion_menu.sku = potion_ledger.sku 
                                                         GROUP BY potion_menu.sku, name, red, green, blue, dark 
                                                         HAVING sum(potion_quantity) != 0 
                                                         ORDER BY quantity DESC""")).fetchall()
        price_per_ml = list(map(lambda a: a[0], connection.execute(sqlalchemy.text("SELECT round(sum(cost)/COALESCE(NULLIF(SUM(ml_quantity), 0), 1), 2) AS cost_per_ml FROM ml_ledger WHERE ml_quantity >= 0 GROUP BY ml_type ORDER BY ml_type ASC")).fetchall()))
        #gets the first 6 indexes unless there not enough different potion_types.
        for i in range(6) if len(potion_list)>=6 else range(len(potion_list)):
                current_price = int(2*(price_per_ml[0]*potion_list[i][3]+price_per_ml[1]*potion_list[i][4]+price_per_ml[2]*potion_list[i][5]*price_per_ml[3]*potion_list[i][4]))
                catalog_entries.append({
                    "sku": potion_list[i][0],
                    "name": potion_list[i][1],
                    "quantity": int(potion_list[i][2]),
                    "price": current_price,
                    "potion_type": [potion_list[i][3], potion_list[i][4], potion_list[i][5], potion_list[i][6]]
                })
                catalog_log.append({
                     "time_id": time_id,
                     "sku": potion_list[i][0],
                     "bought": 0,
                     "sales_price": current_price
                })
        if len(catalog_log) > 0:
            connection.execute(sqlalchemy.text("INSERT INTO catalog_log (time_id, sku, bought, sales_price) VALUES (:time_id, :sku, :bought, :sales_price)"), catalog_log)    
    """Reponse"""
    print(f"My Catalogue: {catalog_entries}")
    return catalog_entries
