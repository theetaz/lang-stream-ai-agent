from api.routes import router as api_router
from fastapi import FastAPI

app = FastAPI(title="AI Agent API")

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent API"}
