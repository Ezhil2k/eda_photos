from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
from PIL.ExifTags import TAGS
import os

router = APIRouter()

# Directory for storing uploaded images
UPLOAD_DIRECTORY = "/app/images"

# Ensure the upload directory exists
# os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Function to extract EXIF metadata
def extract_exif(image_path):
    image = Image.open(image_path)
    exif_data = image._getexif()
    if not exif_data:
        return {}
    exif = {TAGS.get(tag): value for tag, value in exif_data.items() if tag in TAGS}
    return exif

# Endpoint for image upload
@router.post("/upload", tags=["images"])
async def upload_image(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
    exif_data = extract_exif(file_location)
    return {"filename": file.filename, "exif": exif_data}

# Endpoint for image deletion
@router.delete("/images/{filename}", tags=["images"])
async def delete_image(filename: str):
    file_location = os.path.join(UPLOAD_DIRECTORY, filename)
    if os.path.exists(file_location):
        os.remove(file_location)
        return {"message": "Image deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Image not found")
