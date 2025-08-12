import face_recognition
from typing import List, Tuple

# Returns list of (encoding_vector, box_dict)
def extract_faces_and_encodings(image_path: str):
    image = face_recognition.load_image_file(image_path)
    boxes = face_recognition.face_locations(image, model="hog")  # or "cnn" if GPU
    encodings = face_recognition.face_encodings(image, boxes)
    results = []
    for idx, (enc, box) in enumerate(zip(encodings, boxes)):
        top, right, bottom, left = box
        results.append((enc.astype('float32').tolist(), {"top": top, "right": right, "bottom": bottom, "left": left}))
    return results
