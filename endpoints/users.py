from backend.constants import Constants

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from motor.motor_asyncio import AsyncIOMotorClient

Router = APIRouter(
	prefix = "/users",
	tags = ["users"],
	responses = {
		404: {
			"description": "Not found"
		}
	}
)
constants = Constants()
blog = AsyncIOMotorClient(constants.MONGO_URL)[constants.MONGO_DB].blogs
users = AsyncIOMotorClient(constants.MONGO_URL)[constants.MONGO_DB].users

@Router.get("/{unix}")
async def get_user(unix: str):
    result: dict | None = await users.find_one(
        {
            "unix": unix
        }
    )
    if result is None:
        return JSONResponse(
            {
                "error": "User not found."
            },
            status_code = 404
        )
    post_count: int = await blog.count_documents(
        {
            "unix": unix
        }
    )
    posts: list = await blog.find(
        {
            "unix": unix
        },
        limit = 10
    )
    return JSONResponse(
        {
            "id": result["_id"],
            "username": result["username"],
            "unix": result["unix"],
            "posts": posts,
            "total_posts": post_count,
            "updated_at": result["updated_at"],
            "created_at": result["created_at"]
        },
        status_code = 200
    )

@Router.get("/{unix}/posts")
async def get_user_posts(unix: str):
    result: dict | None = await users.find_one(
        {
            "unix": unix
        }
    )
    if result is None:
        return JSONResponse(
            {
                "error": "User not found."
            },
            status_code = 404
        )

    posts: list = await blog.find(
        {
            "author": result["_id"]
        }
    )

    return JSONResponse(
        posts,
        status_code = 200
    )