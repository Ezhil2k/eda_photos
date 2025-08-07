from fastapi import APIRouter

router = APIRouter()

# Health check endpoint
@router.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
