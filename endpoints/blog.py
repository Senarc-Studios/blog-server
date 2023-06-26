import random

from backend.constants import Constants

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

Router = APIRouter(
	prefix = "/blog",
	tags = ["blog"],
	responses = {
		404: {
			"description": "Not found"
		}
	}
)
constants = Constants()
blogs = AsyncIOMotorClient(constants.MONGO_URL)[constants.MONGO_DB].blogs
users = AsyncIOMotorClient(constants.MONGO_URL)[constants.MONGO_DB].users

@Router.get("/{owner_id}/{post_id}")
async def get_blog(owner_id: int, post_id: int):
	result: dict | None = await blogs.find_one(
		{
			"_id": post_id,
			"author": owner_id
		}
	)

	author: dict | None = await users.find_one(
		{
			"_id": owner_id
		}
	)

	author: dict = {
		"_id": int("0"*24),
		"avatar": "https://avatars.githubusercontent.com/u/0?v=4",
		"unix": "deleted",
		"username": "deleted"
	} if author is None else author

	if result is None:
		return JSONResponse(
			{
				"error": "Blog not found."
			},
			status_code = 404
		)

	return JSONResponse(
		{
			"id": post_id,
			"title": result["title"],
			"author": {
				"id": author["_id"],
				"avatar": author["avatar"],
				"unix": author["unix"],
				"username": author["username"]
			},
			"content": result["content"],
			"author": result["author"],
			"updated_at": result["updated_at"],
			"created_at": result["created_at"]
			# "pgp_signature": result["pgp_signature"],
			# "pgp_public_key": result["pgp_public_key"],
			# "pgp_verified": result["pgp_verified"]
		}
	)

@Router.post("/create")
async def create_blog(request: Request):
	data: dict | None = await request.json()
	headers: dict = dict(request.headers)

	if headers.get("Authorization") is None: return JSONResponse(
		{
			"error": "unauthorized"
		},
		status_code = 401
	)

	if not all(key in data for key in ("title", "content", "author")): return JSONResponse(
		{
			"error": "bad request"
		},
		status_code = 400
	)

	author = await users.find_one(
		{
			"token": headers["Authorization"]
		}
	)

	creation_time = int(datetime.now().timestamp())
	random_int: int = random.randint(100000, 999999)
	post_id: int = creation_time * (10 ** len(str(random_int))) + random_int

	result = await blogs.insert_one(
		{
			"_id": post_id,
			"title": data["title"],
			"content": data["content"],
			"author": author["_id"],
			"updated_at": creation_time,
			"created_at": creation_time,
			"pgp_status": "unverified"
		}
	)
	return JSONResponse(
		{
			"id": post_id,
			"title": result["title"],
			"content": result["content"],
			"author": author["_id"],
			"updated_at": creation_time,
			"created_at": creation_time,
			"pgp_status": "unverified"
		}
	)

@Router.patch("/update")
async def update_blog(request: Request):
	data: dict | None = await request.json()
	headers: dict = dict(request.headers)

	if headers.get("Authorization") is None: return JSONResponse(
		{
			"error": "unauthorized"
		},
		status_code = 401
	)

	if not all(key in data for key in ("title", "content", "id")): return JSONResponse(
		{
			"error": "bad request"
		},
		status_code = 400
	)

	author = await users.find_one(
		{
			"token": headers["Authorization"]
		}
	)

	post = await blogs.find_one(
		{
			"_id": data["id"],
		}
	)

	if post["author"] != author["_id"]: return JSONResponse(
		{
			"error": "forbidden"
		},
		status_code = 403
	)

	await blogs.update_one(
		{
			"_id": data["id"],
			"author": author["_id"]
		},
		{
			"$set": {
				"title": data["title"],
				"content": data["content"],
				"updated_at": int(datetime.now().timestamp())
			}
		}
	)
	return JSONResponse(
		{
			"id": data["id"],
			"title": data["title"],
			"content": data["content"],
			"author": author["_id"],
			"updated_at": int(datetime.now().timestamp()),
			"created_at": post["created_at"],
			"pgp_status": post["pgp_status"]
		},
		status_code = 200
	)

@Router.delete("/delete/{post_id}")
async def delete_blog(request: Request, post_id: str):
	headers: dict = dict(request.headers)

	if headers.get("Authorization") is None: return JSONResponse(
		{
			"error": "unauthorized"
		},
		status_code = 401
	)

	author = await users.find_one(
		{
			"token": headers["Authorization"]
		}
	)

	post = await blogs.find_one(
		{
			"_id": post_id,
		}
	)

	if post["author"] != author["_id"]: return JSONResponse(
		{
			"error": "forbidden"
		},
		status_code = 403
	)

	await blogs.delete_one(
		{
			"_id": post_id,
			"author": author["_id"]
		}
	)
	return JSONResponse(
		{
			"message": "success"
		},
		status_code = 200
	)