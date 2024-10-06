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

    potion_type = [0,0,0,0]
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE FROM my_catalog"))
    
        for i in range(4): #for each basic potion type
            potion_type[i] = 100
            potion = connection.execute(sqlalchemy.text(f"SELECT red, green, blue, dark, sku, name, stock FROM potion_storage WHERE red = {potion_type[0]} AND green = {potion_type[1]} AND blue = {potion_type[2]} AND dark = {potion_type[3]} AND stock > 0")).fetchone()
            if potion is not None:
                #decided to keep price constant as large barrels can make a potion for 5 gold and there would need to be some sort of variable markup to that compared to small barrel prices.
                price = 50 #sum([zip(connection.execute(sqlalchemy.text("SELECT total_gold_spend/total_ml_bought as price_per_ml FROM ml_storage")).fetchone(), potion_type)])
                connection.execute(sqlalchemy.text(f"UPDATE potion_storage SET price = {price} WHERE red = {potion_type[0]} AND green = {potion_type[1]} AND blue = {potion_type[2]} AND dark = {potion_type[3]}"))
                catalogue_entries.append({
                    "sku": potion[4],
                    "name": potion[5],
                    "quantity": potion[6],
                    "price": price,
                    "potion_type": [potion[0], potion[1], potion[2], potion[3]]
                })
                connection.execute(sqlalchemy.text(f"INSERT INTO my_catalog (red, green, blue, dark) VALUES ({potion_type[0]},{potion_type[1]},{potion_type[2]},{potion_type[3]})"))
            potion_type[i] = 0
    
    """Reponse"""
    print(f"My Catalogue: {catalogue_entries}")
    return catalogue_entries
