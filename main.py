import uvicorn

from endpoints.authentication import Router as AuthRouter
from endpoints.users import Router as UsersRouter
from endpoints.posts import Router as PostsRouter
from endpoints.blog import Router as BlogRouter

from fastapi import FastAPI, Request

app = FastAPI()

app.include_router(
    AuthRouter,
    UsersRouter,
    PostsRouter,
    BlogRouter
)

@app.get("/")
async def root(request: Request):
    return "This is Senarc Blog API server."

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host = "127.0.0.1",
        port = 8000,
        reload = True
    )