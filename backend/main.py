from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import requests
from pathlib import Path
import time
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://de-id.vercel.app"
]

huggingFaceAPI = os.getenv('HUGGING_FACE')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
HUGGINGFACE_ENDPOINT = "https://api-inference.huggingface.co/models/obi/deid_roberta_i2b2"
HEADERS = {"Authorization": f"Bearer {huggingFaceAPI}"}

def call_model(text: str):
    data = {"inputs": text}
    response = requests.post(HUGGINGFACE_ENDPOINT, headers=HEADERS, json=data)
    if response.status_code == 200:
        json_response = response.json()
        if 'error' in json_response and 'currently loading' in json_response['error']:
            estimated_time = json_response.get('estimated_time', 60)  
            time.sleep(estimated_time)  
            return call_model(text)  
        return json_response
    else:
        return None

@app.get("/sample-data")
async def read_sample_data():
    file_path = Path('./data.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = file.read()
        return {"data": data}
    except IOError:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/deidentify")
def deidentify(clinical_text: str = Body(..., embed=True)):
    model_response = call_model(clinical_text)
    if model_response is None or 'error' in model_response:
        return {"error": "Failed to deidentify text due to model loading or response error"}
    words = clinical_text.split()  
    processed_text = clinical_text 

    # Processing from the end to not mess up the indices as we replace
    for token in reversed(model_response):
        if 'start' in token and 'end' in token and 'entity_group' in token:
            start = token['start']
            end = token['end']
            label = token['entity_group']
            if any(label_part in label for label_part in ['PATIENT', 'AGE', 'ID', 'DATE', 'STAFF']):
                processed_text = processed_text[:start] + "[REDACTED]" + processed_text[end:]

    return {"deidentified_text": processed_text}

