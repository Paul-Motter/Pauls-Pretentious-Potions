import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """Request Body"""
    print(f"Customers: {customers}")

    """Log which customers visited the shop and when.""" 
    #logging all customers with customer info and time.   
    with db.engine.begin() as connection:
        time = connection.execute(sqlalchemy.text("SELECT current_day, current_hour FROM shop_info")).fetchone()
        for one_customer in customers:
            connection.execute(sqlalchemy.text(f"INSERT INTO all_visitors_log (customer_name, character_class, level, day, hour) VALUES ('{one_customer.customer_name}','{one_customer.character_class}',{one_customer.level},'{time[0]}',{time[1]})"))
    
    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """Request body"""
    #simply a single customer who is creating a cart.

    """Creates a cart in the current_cart_list"""
    with db.engine.begin() as connection:
        carts = connection.execute(sqlalchemy.text("SELECT cart_id FROM current_cart_list")).fetchall()
        if len(carts) == 0: #if no carts then first ID is 1.
            cart_id = 1
        else:
            cart_id = carts[len(carts)-1][0]+1 #if there are previous carts then the ID is the last ID plus 1.

        connection.execute(sqlalchemy.text(f"INSERT INTO current_cart_list (cart_id) VALUES ({cart_id})"))
        
    """Response"""
    #A unique id for the cart.
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """Request Body"""
    #gives a cart_id from before with an item and cart_item.quantity for that item.
    print(f"cart_id: {cart_id}, item_sku: {item_sku}, cart_item: {cart_item}")

    """Finds the cart_id and updates with the selected purchase of the customer"""
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE current_cart_list SET item_sku = '{item_sku}', quantity = {cart_item.quantity} WHERE cart_id = {cart_id}"))
    
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """Request Body"""
    #gives a cart_id and cart_checkout.
    print(f"cart_id: {cart_id}, cart_checkout: {cart_checkout}")

    """gets orderID and quantity and then updates gold and potion inventory. assumes green potions are bought and price is always 50"""
    with db.engine.begin() as connection:
        #get current cart order
        cart = connection.execute(sqlalchemy.text(f"SELECT item_sku, quantity FROM current_cart_list WHERE cart_id = {cart_id}")).fetchone()
        #delete the current order
        connection.execute(sqlalchemy.text(f"DELETE FROM current_cart_list WHERE cart_id = {cart_id}"))
        #get potion quanitity and update
        inventory = connection.execute(sqlalchemy.text("SELECT num_green_potions, gold FROM global_inventory")).fetchall()
        #get gold and update 
        #assumes buying green potion worth 50 gold.
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {inventory[0][0] - cart[1]}, gold = {inventory[0][1] + cart[1]*50}"))

    """Response"""
    return {"total_potions_bought": cart[1], "total_gold_paid": cart[1]*50}
