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
			"upvotes": result["upvotes"],
			"downvotes": result["downvotes"],
			"upvoted_users": result["upvoted_users"],
			"downvoted_users": result["downvoted_users"],
			"updated_at": result["creation_time"],
			"created_at": result["creation_time"],
			"pgp_status": "unverified"
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
			"author": author["_id"],
			"content": data["content"],
			"upvotes": 0,
			"downvotes": 0,
			"upvoted_users": [],
			"downvoted_users": [],
			"updated_at": creation_time,
			"created_at": creation_time,
			"pgp_status": "unverified"
		}
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
			"upvotes": 0,
			"downvotes": 0,
			"upvoted_users": [],
			"downvoted_users": [],
			"updated_at": creation_time,
			"created_at": creation_time,
			"pgp_status": "unverified"
		},
		status_code = 200
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
			"upvotes": data["upvotes"],
			"downvotes": data["downvotes"],
			"upvoted_users": data["upvoted_users"],
			"downvoted_users": data["downvoted_users"],
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

@Router.get("/{owner_id}/{post_id}/upvote")
async def upvote_blog(request: Request, owner_id: int, post_id: int):
	headers: dict = dict(request.headers)

	if headers.get("Authorization") is None: return JSONResponse(
		{
			"error": "unauthorized"
		},
		status_code = 401
	)

	author: dict | None = await users.find_one(
		{
			"token": headers["Authorization"]
		}
	)

	if author is None: return JSONResponse(
		{
			"error": "Invalid Token Provided."
		},
		status_code = 401
	)

	post: dict | None = await blogs.find_one(
		{
			"_id": post_id,
			"author": owner_id
		}
	)

	if post is None: return JSONResponse(
		{
			"error": "Blog not found."
		},
		status_code = 404
	)

	if author["_id"] in post["upvoted_users"]:
		await blogs.update_one(
			{
				"_id": post_id,
				"author": owner_id
			},
			{
				"$pull": {
					"upvoted_users": author["_id"]
				},
				"$inc": {
					"upvotes": -1
				}
			}
		)
		return JSONResponse(
			{
				"action": "unupvoted"
			},
			status_code = 200
		)

	if author["_id"] in post["downvoted_users"]:
		await blogs.update_one(
			{
				"_id": post_id,
				"author": owner_id
			},
			{
				"$addToSet": {
					"upvoted_users": author["_id"]
				},
				"$pull": {
					"downvoted_users": author["_id"]
				},
				"$inc": {
					"upvotes": 1,
					"downvotes": -1
				}
			}
		)

		return JSONResponse(
			{
				"action": "upvoted"
			},
			status_code = 200
		)

	await blogs.update_one(
		{
			"_id": post_id,
			"author": owner_id
		},
		{
			"$addToSet": {
				"upvoted_users": author["_id"]
			},
			"$inc": {
				"upvotes": 1
			}
		}
	)

	return JSONResponse(
		{
			"action": "upvoted"
		},
		status_code = 200
	)

@Router.get("/{owner_id}/{post_id}/downvote")
async def downvote_blog(request: Request, owner_id: int, post_id: int):
	headers: dict = dict(request.headers)

	if headers.get("Authorization") is None: return JSONResponse(
		{
			"error": "unauthorized"
		},
		status_code = 401
	)

	author: dict | None = await users.find_one(
		{
			"token": headers["Authorization"]
		}
	)

	if author is None: return JSONResponse(
		{
			"error": "Invalid Token Provided."
		},
		status_code = 401
	)

	post: dict | None = await blogs.find_one(
		{
			"_id": post_id,
			"author": owner_id
		}
	)

	if post is None: return JSONResponse(
		{
			"error": "Blog not found."
		},
		status_code = 404
	)

	if author["_id"] in post["downvoted_users"]:
		await blogs.update_one(
			{
				"_id": post_id,
				"author": owner_id
			},
			{
				"$pull": {
					"downvoted_users": author["_id"]
				},
				"$inc": {
					"downvotes": -1
				}
			}
		)
		return JSONResponse(
			{
				"action": "undownvoted"
			},
			status_code = 200
		)

	if author["_id"] in post["upvoted_users"]:
		await blogs.update_one(
			{
				"_id": post_id,
				"author": owner_id
			},
			{
				"$addToSet": {
					"downvoted_users": author["_id"]
				},
				"$pull": {
					"upvoted_users": author["_id"]
				},
				"$inc": {
					"downvotes": 1,
					"upvotes": -1
				}
			}
		)

		return JSONResponse(
			{
				"action": "downvoted"
			},
			status_code = 200
		)

	await blogs.update_one(
		{
			"_id": post_id,
			"author": owner_id
		},
		{
			"$addToSet": {
				"downvoted_users": author["_id"]
			},
			"$inc": {
				"downvotes": 1
			}
		}
	)

	return JSONResponse(
		{
			"action": "downvoted"
		},
		status_code = 200
	)