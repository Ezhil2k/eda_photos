import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

# Load the CLIP model and processor
MODEL_ID = "openai/clip-vit-large-patch14-336"
clip_model = CLIPModel.from_pretrained(MODEL_ID)
clip_processor = CLIPProcessor.from_pretrained(MODEL_ID)

# Function to generate embeddings for an image
def generate_clip_image_embeddings(image_path):
    image = Image.open(image_path)
    inputs = clip_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        embeddings = clip_model.get_image_features(**inputs).cpu()
    return embeddings.numpy().astype('float32')[0]

# Function to generate embeddings for a text query
def generate_clip_text_embeddings(text: str):
    inputs = clip_processor(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        embeddings = clip_model.get_text_features(**inputs).cpu()
    return embeddings.numpy().astype('float32')[0]
