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

@Router.get("/{author_id}/{post_id}")
async def get_post(request: Request, author_id: int, post_id: int) -> JSONResponse:
    post: dict | None = await posts.find_one(
        {
            "_id": post_id,
            "author": author_id
        }
    )

    if post is None: return JSONResponse(
        {
            "error": "Post not found."
        },
        status_code = 404
    )

    if post["private"]:
        user: dict | None = await users.find_one(
            {
                "token": request.headers.get("Authorization")
            }
        )

        if user is None: return JSONResponse(
            {
                "error": "Post not found."
            },
            status_code = 404
        )

        author: dict | None = await users.find_one(
            {
                "_id": author_id
            }
        )

        if user["_id"] in author["links"]:
            return JSONResponse(
                {
                    "id": post["_id"],
                    "content": post["content"],
                    "private": post["private"],
                    "edited": post["edited"],
                    "author": post["author"],
                    "hearts": post["hearts"],
                    "comments": post["comments"],
                    "created_at": post["created_at"],
                    "updated_at": post["updated_at"]
                },
                status_code = 200
            )

    else:
        return JSONResponse(
            {
                "id": post["_id"],
                "content": post["content"],
                "private": post["private"],
                "edited": post["edited"],
                "author": post["author"],
                "hearts": post["hearts"],
                "comments": post["comments"],
                "created_at": post["created_at"],
                "updated_at": post["updated_at"]
            }
        )

@Router.get("/feed")
async def get_feed(request: Request) -> JSONResponse:
    user: dict | None = await users.find_one(
        {
            "token": request.headers.get("Authorization")
        }
    )

    if user is None: return JSONResponse(
        {
            "error": "Invalid token."
        },
        status_code = 401
    )

    posts: list = await posts.find(
        {
            "author": {
                "$in": user["following"]
            }
        },
        limit = 7
    ).sort(
        [
            ("created_at", -1)
        ]
    )

    # Add more posts that the users don't follow.
    if len(posts) < 15:
        posts += await posts.find(
            {
                "author": {
                    "$nin": user["following"]
                }
            },
            limit = 7
        ).sort(
            [
                ("created_at", -1)
            ]
        )

    return JSONResponse(
        posts,
        status_code = 200
    )

@Router.get("/{author_id}/{post_id}/heart")
async def heart_post(request: Request, author_id: int, post_id: int) -> JSONResponse:
    post: dict | None = await posts.find_one(
        {
            "_id": post_id,
            "author": author_id
        }
    )

    if post is None: return JSONResponse(
        {
            "error": "Post not found."
        },
        status_code = 404
    )

    user: dict | None = await users.find_one(
        {
            "token": request.headers.get("Authorization")
        }
    )

    if user is None: return JSONResponse(
        {
            "error": "Invalid token."
        },
        status_code = 401
    )

    if user["_id"] in post["hearts"]["users"]:
        await posts.update_one(
            {
                "_id": post_id
            },
            {
                "$inc": {
                    "hearts.count": -1
                },
                "$pull": {
                    "hearts.users": user["_id"]
                }
            }
        )

        return JSONResponse(
            {
                "message": "Successfully unhearted post."
            },
            status_code = 200
        )

    await posts.update_one(
        {
            "_id": post_id
        },
        {
            "$inc": {
                "hearts.count": 1
            },
            "$push": {
                "hearts.users": user["_id"]
            }
        }
    )

    return JSONResponse(
        {
            "message": "Successfully hearted post."
        },
        status_code = 200
    )