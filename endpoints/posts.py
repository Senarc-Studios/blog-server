import random

from backend.constants import Constants

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

Router = APIRouter(
    prefix = "/post"
)
constants = Constants()
users = AsyncIOMotorClient(constants.MONGO_URL)[constants.MONGO_DB].users
posts = AsyncIOMotorClient(constants.MONGO_URL)[constants.MONGO_DB].posts

@Router.post("/create")
async def create_post(request: Request) -> JSONResponse:
    data: dict | None = await request.json()
    author: dict | None = await users.find_one(
        {
            "token": request.headers.get("Authorization")
        }
    )

    if data.get("content") is None or not isinstance(str, data.get("content")): return JSONResponse(
        {
            "error": "Invalid content."
        },
        status_code = 400
    )

    if author is None: return JSONResponse(
        {
            "error": "Invalid token."
        },
        status_code = 401
    )

    payload: dict = {
        "id": f"{random.randint(1000000000, 9999999999)}",
        "content": data["content"],
        "private": data["private"],
        "edited": False,
        "author": {
            "id": author["_id"],
            "avatar": author["avatar"],
            "unix": author["unix"],
            "username": author["username"]
        },
        "hearts": {
            "count": 0,
            "users": []
        },
        "comments": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await posts.insert_one(
        {
            "_id": payload["id"],
            "content": data["content"],
            "private": data["private"],
            "edited": False,
            "author": author["_id"],
            "hearts": {
                "count": 0,
                "users": []
            },
            "comments": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    )

    return JSONResponse(
        payload,
        status_code = 200
    )

