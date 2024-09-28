import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/info",
    tags=["info"],
    dependencies=[Depends(auth.get_api_key)],
)

class Timestamp(BaseModel):
    day: str
    hour: int

@router.post("/current_time")
def post_time(timestamp: Timestamp):
    """Share current time and save in shop_info"""
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE shop_info SET current_day = '{timestamp.day}', current_hour = {timestamp.hour}"))

    return "OK"

