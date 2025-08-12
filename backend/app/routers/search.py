from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, bindparam
from ..database import get_db
from ..services.clip_service import generate_clip_text_embeddings
from pgvector.sqlalchemy import Vector

router = APIRouter()

@router.get("/search", tags=["search"])
async def search(query: str, db: Session = Depends(get_db)):
    # Generate text embedding for query
    q_emb = generate_clip_text_embeddings(query)
    emb_param = [float(x) for x in q_emb.tolist()]

    # If there are no embeddings, short-circuit
    exists = db.execute(text("SELECT 1 FROM image_embeddings LIMIT 1")).first()
    if not exists:
        return {"query": query, "results": [], "info": "no embeddings in database"}

    sql = text(
        """
        SELECT image_name, 1 - (embedding <#> :emb) AS similarity
        FROM image_embeddings
        ORDER BY embedding <-> :emb
        LIMIT 20
        """
    ).bindparams(bindparam("emb", type_=Vector(768)))

    rows = db.execute(sql, {"emb": emb_param}).mappings().all()
    return {"query": query, "results": rows}
