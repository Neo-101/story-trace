import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import novels, analysis, jobs

app = FastAPI(
    title="StoryTrace API",
    generate_unique_id_function=lambda route: route.name # Use function name as operation ID
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(novels.router)
app.include_router(analysis.router)
app.include_router(jobs.router)

@app.get("/")
async def index():
    return {"message": "StoryTrace API is running. Please access the frontend at http://localhost:5173"}

if __name__ == "__main__":
    import uvicorn
    from core.config import settings
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
