# Import statements
from fastapi import FastAPI
from .routers import auth, images, health

# FastAPI app with automatic Swagger documentation
app = FastAPI(
    title="EDA Photos API",
    description="API documentation for the EDA Photos project",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Operations related to user authentication"},
        {"name": "images", "description": "Operations related to image management"},
        {"name": "search", "description": "Operations related to image search"},
        {"name": "health", "description": "Health check endpoint"}
    ]
)

# Include routers
app.include_router(auth.router)
app.include_router(images.router)
app.include_router(health.router)

# Future Feature: Implement CLIP search functionality here
# Future Feature: Implement face clustering logic here
# Future Feature: Implement soft delete for images here