from fastapi import APIRouter

router = APIRouter()

# Dummy search endpoint
@router.get("/search", tags=["search"])
async def search(query: str):
    # Return dummy results for now
    return {
        "query": query,
        "results": [
            {"id": 1, "name": "Dummy Image 1", "description": "A dummy image result."},
            {"id": 2, "name": "Dummy Image 2", "description": "Another dummy image result."}
        ]
    }
