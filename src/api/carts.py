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
        time = connection.execute(sqlalchemy.text("SELECT date_id FROM time ORDER BY date_id DESC LIMIT 1")).fetchone()
        for customer in customers:
            connection.execute(sqlalchemy.text(f"INSERT INTO customers (customer_id, customer_name, character_class, level, date_id) VALUES ({visit_id},'{customer.customer_name}','{customer.character_class}',{customer.level}, {time[0]})"))
    
    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """Request body"""
    #simply a single customer who is creating a cart.

    """Creates a cart in the current_cart_list"""
    with db.engine.begin() as connection:
        last_cart_id = connection.execute(sqlalchemy.text("SELECT cart_id FROM customers WHERE cart_id IS NOT NULL ORDER BY cart_id DESC LIMIT 1")).fetchone()
        #for the first cart let the id be 1.
        if last_cart_id is None:
            last_cart_id = [0]
        connection.execute(sqlalchemy.text(f"UPDATE customers SET cart_id = {last_cart_id[0]+1} WHERE customer_name = '{new_cart.customer_name}' AND character_class = '{new_cart.character_class}' AND level = {new_cart.level}"))
        
    """Response"""
    #A unique id for the cart.
    return {"cart_id": last_cart_id[0]+1}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """Request Body"""
    #gives a cart_id from before with an item and cart_item.quantity for that item.
    print(f"cart_id: {cart_id}, item_sku: {item_sku}, cart_item: {cart_item}")

    """Finds the cart_id and updates with the selected purchase of the customer"""
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"INSERT INTO cart_items (sku, quantity, cart_id) VALUES ('{item_sku}', {cart_item.quantity}, {cart_id})"))
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
        checkout_list = connection.execute(sqlalchemy.text("SELECT red, green, blue, dark, quantity, price FROM cart_items JOIN potion_storage ON cart_items.sku = potion_storage.sku")).fetchall()
        total_bought = 0
        total_paid = 0
        for item in checkout_list:
            total_bought += item[4]
            total_paid += item[4]*item[5]
            connection.execute(sqlalchemy.text(f"UPDATE potion_storage SET stock = stock - {item[4]}, total_sold = total_sold + {item[4]} WHERE red = {item[0]} AND green = {item[1]} AND blue = {item[2]} AND dark = {item[3]}"))
        connection.execute(sqlalchemy.text(f"UPDATE shop_info SET gold = gold + {total_paid}"))
        connection.execute(sqlalchemy.text(f"INSERT INTO payment_type (payment) VALUES ('{cart_checkout.payment}')"))
    """Response"""
    return {"total_potions_bought": total_bought, "total_gold_paid": total_paid}