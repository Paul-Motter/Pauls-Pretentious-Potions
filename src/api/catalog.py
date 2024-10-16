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
    catalogue_entries = []
    with db.engine.begin() as connection:
        #returns a list of options in the order of highest total stock to lowest exempting those that are zero stock.
        potion_list = connection.execute(sqlalchemy.text("""SELECT potion_menu.sku, name, SUM(potion_quantity) AS quantity, current_price, red, green, blue, dark 
                                                         FROM potion_menu JOIN potion_ledger ON potion_menu.sku = potion_ledger.sku 
                                                         GROUP BY potion_menu.sku, name, current_price, red, green, blue, dark 
                                                         HAVING sum(potion_quantity) != 0 
                                                         ORDER BY quantity DESC""")).fetchall()
        #gets the first 6 indexes unless there not enough different potion_types.
        for i in range(6) if len(potion_list)>=6 else range(len(potion_list)):
                catalogue_entries.append({
                    "sku": potion_list[i][0],
                    "name": potion_list[i][1],
                    "quantity": int(potion_list[i][2]),
                    "price": potion_list[i][3],
                    "potion_type": [potion_list[i][4], potion_list[i][5], potion_list[i][6], potion_list[i][7]]
                })
    
    """Reponse"""
    print(f"My Catalogue: {catalogue_entries}")
    return catalogue_entries
