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
        connection.execute(sqlalchemy.text("INSERT INTO times (day, time) VALUES (:day, :hour)"), {"day": timestamp.day, "hour": timestamp.hour})

    return "OK"

