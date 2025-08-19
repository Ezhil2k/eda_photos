from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db, FaceGroupsCache
from ..services.face_service import extract_faces_and_encodings
from ..deps import get_current_user
import os
import numpy as np
from sklearn.cluster import DBSCAN

router = APIRouter()

IMAGES_DIR = os.getenv("IMAGE_DIR", "/app/images")

@router.post("/process-faces", tags=["faces"])
async def process_faces(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not os.path.isdir(IMAGES_DIR):
        payload = {"clusters": {}, "total_clusters": 0}
        # Upsert single row cache
        existing = db.query(FaceGroupsCache).first()
        if existing:
            existing.data = payload
        else:
            db.add(FaceGroupsCache(data=payload))
        db.commit()
        return {"faces": payload, "status": "ok"}

    encs = []
    names = []
    for fname in sorted(os.listdir(IMAGES_DIR)):
        path = os.path.join(IMAGES_DIR, fname)
        if not os.path.isfile(path):
            continue
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        try:
            faces = extract_faces_and_encodings(path)
            for enc, _ in faces:
                encs.append(enc)
                names.append(fname)
        except Exception:
            continue

    clusters_out = {}
    if encs:
        X = np.array(encs, dtype=np.float32)
        clustering = DBSCAN(metric='euclidean', eps=0.6, min_samples=1)
        labels = clustering.fit_predict(X).tolist()

        cluster_map = {}
        for label, fname in zip(labels, names):
            cluster_map.setdefault(str(label), []).append(fname)
        clusters_out = cluster_map

    payload = {"clusters": clusters_out, "total_clusters": len(clusters_out)}
    existing = db.query(FaceGroupsCache).first()
    if existing:
        existing.data = payload
    else:
        db.add(FaceGroupsCache(data=payload))
    db.commit()

    return {"faces": payload, "status": "ok"}

@router.get("/face-groups", tags=["faces"])
async def face_groups(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cached = db.query(FaceGroupsCache).first()
    if not cached or not cached.data:
        return {"clusters": {}, "total_clusters": 0}
    return cached.data
