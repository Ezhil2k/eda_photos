from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db, FaceEmbedding
from ..services.face_service import extract_faces_and_encodings
import os
import numpy as np
from sklearn.cluster import DBSCAN

router = APIRouter()

IMAGES_DIR = "/app/images"

@router.post("/faces/reprocess", tags=["faces"])
async def faces_reprocess(image_name: str = Query(None), force: bool = Query(False), db: Session = Depends(get_db)):
    processed = created = updated = skipped = 0
    errors = []
    targets = []
    if image_name:
        targets = [image_name]
    else:
        if not os.path.isdir(IMAGES_DIR):
            return {"processed": 0, "created": 0, "updated": 0, "skipped": 0, "errors": [f"Images dir not found: {IMAGES_DIR}"]}
        targets = [f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f))]

    for fname in targets:
        processed += 1
        path = os.path.join(IMAGES_DIR, fname)
        try:
            existing = db.query(FaceEmbedding).filter(FaceEmbedding.image_name == fname).first()
            if existing and not force:
                skipped += 1
                continue
            faces = extract_faces_and_encodings(path)
            # Replace existing rows
            db.query(FaceEmbedding).filter(FaceEmbedding.image_name == fname).delete()
            for idx, (enc, box) in enumerate(faces):
                db.add(FaceEmbedding(image_name=fname, face_index=idx, box=box, embedding=enc))
            db.commit()
            if existing:
                updated += 1
            else:
                created += 1
        except Exception as e:
            db.rollback()
            errors.append({"file": fname, "error": str(e)})

    return {"processed": processed, "created": created, "updated": updated, "skipped": skipped, "errors": errors[:10]}

# Simple listing of faces by image
@router.get("/faces/by-image", tags=["faces"])
async def faces_by_image(image_name: str, db: Session = Depends(get_db)):
    rows = db.query(FaceEmbedding).filter(FaceEmbedding.image_name == image_name).all()
    return [{"image_name": r.image_name, "face_index": r.face_index, "box": r.box} for r in rows]

# Cluster faces across all images and return groups
@router.get("/faces/clusters", tags=["faces"])
async def faces_clusters(eps: float = 0.45, min_samples: int = 2, db: Session = Depends(get_db)):
    # Fetch all face embeddings
    rows = db.query(FaceEmbedding).all()
    if not rows:
        return {"clusters": [], "info": "no face embeddings"}

    X = np.array([r.embedding for r in rows], dtype=np.float32)
    # DBSCAN with cosine-like distance: use metric='euclidean' on normalized vectors if needed
    # Normalize encodings for better clustering stability
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-8
    Xn = X / norms
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean').fit(Xn)
    labels = clustering.labels_.tolist()

    # Group results by cluster label (ignore noise label -1)
    clusters = {}
    for r, label in zip(rows, labels):
        if label == -1:
            continue
        clusters.setdefault(label, []).append({
            "image_name": r.image_name,
            "face_index": r.face_index,
            "box": r.box
        })

    # Convert to list of clusters sorted by size
    cluster_list = [
        {"cluster_id": int(cid), "count": len(items), "faces": items}
        for cid, items in sorted(clusters.items(), key=lambda kv: -len(kv[1]))
    ]

    return {"clusters": cluster_list, "params": {"eps": eps, "min_samples": min_samples}}
