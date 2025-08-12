from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from ..database import get_db, ImageEmbedding, FaceEmbedding
from ..services.clip_service import generate_clip_image_embeddings
from PIL import Image
from PIL.ExifTags import TAGS
import os
from ..services.face_service import extract_faces_and_encodings

router = APIRouter()

# Directory for storing uploaded images
UPLOAD_DIRECTORY = "/app/images"

# Function to extract EXIF metadata
def extract_exif(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    if not exif_data:
        return {}
    exif = {TAGS.get(tag): value for tag, value in exif_data.items() if tag in TAGS}
    return exif

# Unified upload: accepts 1..N files
@router.post("/upload", tags=["images"])
async def upload_images(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    processed = created = updated = failed = 0
    results = []
    for file in files:
        file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
        try:
            # Save file
            with open(file_location, "wb") as buffer:
                buffer.write(await file.read())
            exif_data = extract_exif(file_location)

            # Generate embedding and upsert
            embedding = generate_clip_image_embeddings(file_location)
            emb_list = [float(x) for x in embedding.tolist()]
            existing = db.query(ImageEmbedding).filter(ImageEmbedding.image_name == file.filename).first()
            if existing:
                existing.embedding = emb_list
                updated += 1
                status = "updated"
            else:
                db.add(ImageEmbedding(image_name=file.filename, embedding=emb_list))
                created += 1
                status = "created"
            db.commit()

            # Generate face embeddings and upsert per face
            try:
                faces = extract_faces_and_encodings(file_location)
                # Remove existing faces for this image first to keep in sync
                db.query(FaceEmbedding).filter(FaceEmbedding.image_name == file.filename).delete()
                for idx, (enc, box) in enumerate(faces):
                    db.add(FaceEmbedding(image_name=file.filename, face_index=idx, box=box, embedding=enc))
                db.commit()
            except Exception:
                pass

            results.append({"filename": file.filename, "status": status, "exif_available": bool(exif_data)})
            processed += 1
        except Exception as e:
            db.rollback()
            failed += 1
            results.append({"filename": file.filename, "status": "failed", "error": str(e)})

    return {
        "processed": processed,
        "created": created,
        "updated": updated,
        "failed": failed,
        "details": results,
    }

# Unified delete: accepts 1..N filenames
class DeleteRequest(BaseModel):
    filenames: List[str]

@router.delete("/images", tags=["images"])
async def delete_images(payload: DeleteRequest, db: Session = Depends(get_db)):
    deleted_files = deleted_rows = not_found = 0
    details = []
    for filename in payload.filenames:
        file_location = os.path.join(UPLOAD_DIRECTORY, filename)
        file_deleted = False
        try:
            if os.path.exists(file_location):
                os.remove(file_location)
                file_deleted = True
                deleted_files += 1
            existing = db.query(ImageEmbedding).filter(ImageEmbedding.image_name == filename).first()
            if existing:
                db.delete(existing)
                deleted_rows += 1
            existing_faces = db.query(FaceEmbedding).filter(FaceEmbedding.image_name == filename).all()
            if existing_faces:
                db.query(FaceEmbedding).filter(FaceEmbedding.image_name == filename).delete()
            db.commit()
            if file_deleted or existing:
                details.append({"filename": filename, "status": "deleted"})
            else:
                not_found += 1
                details.append({"filename": filename, "status": "not_found"})
        except Exception as e:
            db.rollback()
            details.append({"filename": filename, "status": "failed", "error": str(e)})
    return {
        "deleted_files": deleted_files,
        "deleted_embeddings": deleted_rows,
        "not_found": not_found,
        "details": details,
    }
