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
        inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions from global_inventory")).fetchall()

    catalogue_entries.append({
        "sku": "GREEN100",
        "name": "green_potion",
        "quantity": inventory[0][0],
        "price": 75,
        "potion_type": [0, 100, 0, 0],

    })

    print(f"catalogueEntries: {catalogue_entries}")

    return catalogue_entries
