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
    #----------RAW SQL approach----------#
    page = 1 if search_page == "" else int(search_page)

    with db.engine.begin() as connection:
        stats = connection.execute(sqlalchemy.text(
            """
            SELECT count(cart_id)
            FROM cart_items
                JOIN carts ON carts.id = cart_items.cart_id
                JOIN customer_visit ON customer_visit.id = carts.customer_id
            WHERE customer_name ILIKE :customer_name 
                AND sku ILIKE :potion_sku
            """
        ), 
        {
            "customer_name": f"%{customer_name}%",
            "potion_sku": f"%{potion_sku}%"
        }).scalar_one()
        
        print(stats)

        content = connection.execute(sqlalchemy.text(
            f"""
            SELECT cart_id as line_item_id,
                sku AS item_sku,
                customer_name,
                sales_price*quantity AS line_item_total,
                time_stamp AS timestamp
            FROM cart_items
                JOIN carts ON carts.id = cart_items.cart_id
                JOIN customer_visit ON customer_visit.id = carts.customer_id
            WHERE customer_name ILIKE :customer_name 
                AND sku ILIKE :potion_sku
            ORDER BY {sort_col.value} {sort_order.value}
            LIMIT 5 OFFSET :page
            """
        ), 
        {
            "customer_name": f"%{customer_name}%",
            "potion_sku": f"%{potion_sku}%",
            "page": page-1
        }
        ).mappings().fetchall()

        return {
            "previous": "" if page == 1 else f"{page-1}",
            "next": "" if page == stats//5 + 1 else f"{page+1}",
            "results": content
            }

    #----------Query Builder Approach----------#
    # page = 1 if search_page == "" else int(search_page)    
    # #Used to get the total results from the search.
    # stats_query = (sqlalchemy.select(sqlalchemy.func.count(db.cart_items.c.cart_id))
    #                 .select_from(db.cart_items)
    #                 .join(db.carts, db.carts.c.id == db.cart_items.c.cart_id)
    #                 .join(db.customer_visit, db.customer_visit.c.id == db.carts.c.customer_id)
    #                 .where(db.customer_visit.c.customer_name.ilike(f"%{customer_name}%"))
    #                 .where(db.cart_items.c.sku.ilike(f"%{potion_sku}%"))
    #                 )
    # #Used to the content that is to be shown.
    # content_query = (
    #                 sqlalchemy.select(db.cart_items.c.cart_id.label("line_item_id"),
    #                                    db.cart_items.c.sku.label("item_sku"),
    #                                    db.customer_visit.c.customer_name.label("customer_name"),
    #                                    db.cart_items.c.sales_price.label("line_item_total"),
    #                                    db.cart_items.c.time_stamp.label("timestamp"))
    #                 .select_from(db.cart_items)
    #                 .join(db.carts, db.carts.c.id == db.cart_items.c.cart_id)
    #                 .join(db.customer_visit, db.customer_visit.c.id == db.carts.c.customer_id)
    #                 .where(db.customer_visit.c.customer_name.ilike(f"%{customer_name}%"))
    #                 .where(db.cart_items.c.sku.ilike(f"%{potion_sku}%"))
    #                 .limit(5).offset((page-1)*5)
    #                 )
    # #orders the content to the shown.
    # match (sort_col, sort_order):
    #     case (search_sort_options.timestamp, search_sort_order.asc):
    #         content_query = content_query.order_by(db.cart_items.c.time_stamp)
    #     case (search_sort_options.timestamp, search_sort_order.desc):
    #         content_query = content_query.order_by(db.cart_items.c.time_stamp.desc())

    #     case (search_sort_options.line_item_total, search_sort_order.asc):
    #         content_query = content_query.order_by(db.cart_items.c.sales_price)
    #     case (search_sort_options.line_item_total, search_sort_order.desc):
    #         content_query = content_query.order_by(db.cart_items.c.sales_price.desc())

    #     case (search_sort_options.item_sku, search_sort_order.asc):
    #         content_query = content_query.order_by(db.cart_items.c.sku)
    #     case (search_sort_options.item_sku, search_sort_order.desc):
    #         content_query = content_query.order_by(db.cart_items.c.sku.desc())

    #     case (search_sort_options.customer_name, search_sort_order.asc):
    #         content_query = content_query.order_by(db.customer_visit.c.customer_name)
    #     case (search_sort_options.customer_name, search_sort_order.desc):
    #         content_query = content_query.order_by(db.customer_visit.c.customer_name.desc())

    # with db.engine.begin() as connection:
    #     #execute the stats query.
    #     stats = connection.execute(stats_query).scalar_one()
    #     #compiles results and executes the content query.
    #     result = {
    #         "previous": "" if page == 1 else f"{page-1}",
    #         "next": "" if page == stats//5 + 1 else f"{page+1}",
    #         "results": connection.execute(content_query).mappings().fetchall()
    #         }
    
    # return result

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
        time_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM times")).scalar_one()
        customer_list = []
        for customer in customers:
            customer_list.append({
                "visit_id": visit_id,
                "customer_name": customer.customer_name,
                "character_class": customer.character_class,
                "character_level": customer.level,
                "date_id": time_id
            })
        if len(customer_list) > 0:
            connection.execute(sqlalchemy.text("INSERT INTO customer_visit (visit_id, customer_name, character_class, character_level, date_id) VALUES (:visit_id, :customer_name, :character_class, :character_level, :date_id)"), customer_list)
    
    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """Request body"""
    #simply a single customer who is creating a cart.

    """Creates a cart in the current_cart_list"""
    with db.engine.begin() as connection:
        customer_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM customer_visit WHERE customer_name = :customer_name AND character_class = :character_class AND character_level = :character_level"), {"customer_name": new_cart.customer_name, "character_class": new_cart.character_class, "character_level": new_cart.level}).scalar_one()
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:customer_id) RETURNING id"), {"customer_id": customer_id}).scalar_one()

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
        time_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM times")).scalar_one()
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, sku, quantity, sales_price) SELECT :cart_id, :sku, :quantity, sales_price FROM catalog_log WHERE :sku = catalog_log.sku AND :time_id = catalog_log.time_id"), {"cart_id": cart_id, "sku": item_sku, "quantity":cart_item.quantity, "time_id": time_id})
    
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

        time_id = connection.execute(sqlalchemy.text("SELECT max(id) FROM times")).scalar_one()
        transaction_id = connection.execute(sqlalchemy.text("INSERT INTO transactions (transaction_type, time_id, order_id) VALUES (:transaction_type, :time_id, :order_id) RETURNING id"), {"transaction_type":"cart_checkout", "time_id":time_id, "order_id":cart_id}).scalar_one()
        checkout_list = connection.execute(sqlalchemy.text("SELECT sku, quantity, sales_price FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id}).fetchall()
        potion_ledger = []
        gold_ledger = []
        catalog_log = []
        total_gold = 0
        total_bought = 0
        for item in checkout_list:
            potion_ledger.append({
                "transaction_id": transaction_id,
                "sku": item[0],
                "potion_quantity": -item[1]
            })
            total_bought += item[1]
            total_gold += item[1]*item[2]
            catalog_log.append({
                "time_id": time_id,
                "sku": item[0],
                "bought": item[1]
            })
        gold_ledger.append({
            "transaction_id": transaction_id,
            "gold_quantity": total_gold
        })
        connection.execute(sqlalchemy.text("INSERT INTO potion_ledger (transaction_id, sku, potion_quantity) VALUES (:transaction_id, :sku, :potion_quantity)"), potion_ledger)
        connection.execute(sqlalchemy.text("INSERT INTO gold_ledger (transaction_id, gold_quantity) VALUES (:transaction_id, :gold_quantity)"), gold_ledger)
        connection.execute(sqlalchemy.text("UPDATE catalog_log SET bought = bought+:bought WHERE time_id = :time_id AND sku = :sku"), catalog_log)
        connection.execute(sqlalchemy.text("UPDATE carts SET payment = :payment WHERE id = :cart_id"), {"payment": cart_checkout.payment, "cart_id": cart_id})

    """Response"""
    return {"total_potions_bought": total_bought, "total_gold_paid": total_gold}