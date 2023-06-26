import re
import base64
import random

from backend.constants import Constants

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

Router = APIRouter(
	prefix = "/auth",
	tags = ["Authentication"]
)
constants = Constants()
auth_collection = AsyncIOMotorClient(constants.MONGO_URL)["blog"]["auth"]

@Router.post("/login")
async def login(request: Request) -> JSONResponse:
	data = await request.json()

	if data.get("password") is None: return JSONResponse(
		{
			"error": "Invalid username or password."
		},
		status_code = 401
	)

	if data.get("unix") is None and data.get("email") is None: return JSONResponse(
		{
			"error": "Invalid username or password."
		},
		status_code = 401
	)

	user_info: dict | None = await auth_collection.find_one(
		{
			"unix": data["unix"],
			"password": hash(data["password"])
		}
	) if data.get("unix") is not None else await auth_collection.find_one(
		{
			"email": data["email"],
			"password": hash(data["password"])
		}
	)

	return JSONResponse(
		{
			"error": "Invalid username or password."
		},
		status_code = 401
	) if user_info is None else JSONResponse(
		{
			"token": user_info.get("token")
		},
		status_code = 201
	)

@Router.post("/register")
async def register(request: Request) -> JSONResponse:
	data = await request.json()

	if not all(key in data for key in ("unix", "email", "username", "password")): return JSONResponse(
		{
			"error": "Invalid data."
		},
		status_code = 400
	)

	if re.match(r"[^@]+@[^@]+\.[^@]+", data["email"]) is None: return JSONResponse(
		{
			"error": "Invalid email."
		},
		status_code = 400
	)

	data["email"] = data["email"].split("+")[0] + "@" + data["email"].split("@")[-1] if "+" in data["email"] else data["email"]

	if await auth_collection.find_one(
		{
			"unix": data["unix"]
		}
	) is not None: return JSONResponse(
		{
			"error": "Unix already exists."
		},
		status_code = 409
	)
	elif await auth_collection.find_one(
		{
			"email": data["email"]
		}
	) is not None: return JSONResponse(
		{
			"error": "Email already exists."
		},
		status_code = 409
	)

	if not all(isinstance(str, value) for value in data.values()): return JSONResponse(
		{
			"error": "Invalid data type."
		},
		status_code = 400
	)

	if len(data["unix"]) > 32: return JSONResponse(
		{
			"error": "Unix is too long."
		},
		status_code = 400
	)

	elif len(data["unix"]) < 3: return JSONResponse(
		{
			"error": "Unix is too short."
		},
		status_code = 400
	)

	creation_time = int(datetime.now().timestamp())
	random_int: int = random.randint(100000, 999999)
	user_id: int = creation_time * (10 ** len(str(random_int))) + random_int

	payload = {
		"_id": user_id,
		"unix": data["unix"],
		"username": data["username"],
		"password": hash(data["password"]),
		"email": data["email"],
		"token": (
			base64.b64encode(str(random.randint(0, 2**64)).encode()).decode() +
			">>" +
			base64.b64encode(str(user_id).encode()).decode() +
			">>" +
			base64.b64encode(str(creation_time).encode()).decode() +
			"<"
		)
	}

	await auth_collection.insert_one(
		payload
	)
	return JSONResponse(
		{
			"token": payload["token"]
		},
		status_code = 201
	)