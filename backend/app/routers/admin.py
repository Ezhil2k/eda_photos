from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db, ImageEmbedding
from ..services.clip_service import generate_clip_image_embeddings
from .faces import process_faces as run_face_processing
import os

router = APIRouter()

# Directory where images are stored inside the container (env override for consistency)
IMAGES_DIR = os.getenv("IMAGE_DIR", "/app/images")

@router.post("/admin/reprocess_embeddings", tags=["admin"])
async def reprocess_embeddings(
    force: bool = Query(False, description="If true, recompute and overwrite existing embeddings"),
    db: Session = Depends(get_db),
):
    if not os.path.isdir(IMAGES_DIR):
        return {"processed": 0, "created": 0, "updated": 0, "skipped": 0, "errors": [f"Images dir not found: {IMAGES_DIR}"]}

    filenames = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]
    processed = created = updated = skipped = 0
    errors = []

    for fname in filenames:
        processed += 1
        path = os.path.join(IMAGES_DIR, fname)
        try:
            existing = db.query(ImageEmbedding).filter(ImageEmbedding.image_name == fname).first()
            if existing and not force:
                skipped += 1
                continue

            emb = generate_clip_image_embeddings(path)
            emb_list = [float(x) for x in emb.tolist()]

            if existing and force:
                existing.embedding = emb_list
                updated += 1
            else:
                db.add(ImageEmbedding(image_name=fname, embedding=emb_list))
                created += 1

            if (created + updated) % 50 == 0:
                db.commit()
        except Exception as e:
            errors.append({"file": fname, "error": str(e)})

    db.commit()

    # Also (re)process face recognition clusters and store cache in DB
    faces_result = await run_face_processing(db)  # returns {"faces": {...}, "status": "ok"}

    return {
        "processed": processed,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors_count": len(errors),
        "errors": errors[:10],  # return up to 10 error details
        "faces": faces_result.get("faces"),
        "faces_status": faces_result.get("status"),
    }
