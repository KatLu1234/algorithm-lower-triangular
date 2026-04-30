from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.api import api_router

app = FastAPI(
    title="Lower Triangular Project API",
    openapi_url="/api/v1/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to Lower Triangular Project API"}
