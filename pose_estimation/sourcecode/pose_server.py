from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uvicorn
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image
import torch
import numpy as np
from out_source_stuff import AdaptiveShortNetwork5
from torchvision import transforms
import os
import time
import json
import threading
from const import best_model_dir, active_mask_path, server_icon
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

app = FastAPI()

model_path = best_model_dir
favicon_path = server_icon


#Konvertiert ein JSON-Objekt in ein flaches Rotationsarray
def parse_rotations(joint_data):
    if "rotations" in joint_data and isinstance(joint_data["rotations"], list):
        return joint_data["rotations"]
    else:
        # Alt-Format: joint_id -> [r1, r2, r3]
        flat = []
        for joint_id in sorted(joint_data.keys(), key=int):
            if joint_id.isdigit():
                values = joint_data[joint_id]
                if isinstance(values, list):
                    flat.extend(values)
        return flat


#Ermittelt aktive Achsen
def get_valid_indices():
    try:
        with open(active_mask_path, 'r') as f:
            mask_data = json.load(f)
                    
            # Falls die Datei bereits active_indices enthält
            if "active_indices" in mask_data:
                active_indices = mask_data["active_indices"]
                print(f"Loaded {len(active_indices)} active indices from file: {active_indices}")
                return active_indices
                    
            # Falls die Datei Rotationswerte enthält, analysieren
            rotations = parse_rotations(mask_data)
            active_indices = []
            for idx, value in enumerate(rotations):
                if abs(value) > 1e-6:
                    active_indices.append(idx)
                    
            print(f"Detected {len(active_indices)} active indices from reference file: {active_indices}")
            return active_indices
                    
    except Exception as e:
        print(f"Error loading active_mask_path: {e}")

        return list(range(51))

# === Modell laden ===
active_indices = get_valid_indices()
model = AdaptiveShortNetwork5(output_size=len(active_indices))

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")

model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

# === Bildvorverarbeitung ===
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
])


@app.get("/")
def root():
    return {"Hello World."}


#Icon für Server weil warum nicht
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


#Bekommt input zugesendet
@app.post("/")
async def predict_pose(file: UploadFile = File(...)):
    try:
        content = await file.read()

        start_time = time.time()

        image = Image.open(BytesIO(content)).convert("RGB")
        input_tensor = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            pred = model(input_tensor).squeeze().cpu().numpy()

        # ggf. aktives → full-format:
        full_pred = np.zeros(51, dtype=np.float32)
        for i, idx in enumerate(active_indices):
            full_pred[idx] = pred[i]

        joint_rotations = full_pred.reshape(-1, 3).tolist()

        duration = time.time() - start_time
        print(f"Server Time: {duration} in seconds")

        return JSONResponse(content={"rotations": joint_rotations, "duration": duration})
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return JSONResponse(
            content={"error": f"Prediction failed: {str(e)}"},
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run("pose_server:app", host="0.0.0.0", port=8000, log_level="info")
"""
uvicorn pose_server:app --reload

uvicorn.run("pose_server:app", host="0.0.0.0", port=8000)

"""