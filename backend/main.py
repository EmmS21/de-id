from fastapi import FastAPI, HTTPException, Body
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",
]

# Add CORSMiddleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("obi/deid_roberta_i2b2")
model = AutoModelForTokenClassification.from_pretrained("obi/deid_roberta_i2b2")


@app.get("/sample-data")
async def read_sample_data():
    file_path = Path('./data.txt')  
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = file.read()
        return {"data": data}
    except IOError:
        raise HTTPException(status_code=404, detail="File not found")


def tokenize_text(text: str):
    # This function should return tokenized text in a format suitable for the model
    return tokenizer(text, return_tensors="pt", truncation=True, padding=True)

def predict_phi(tokens):
    # This should use the model to predict PHI tokens
    with torch.no_grad():
        outputs = model(**tokens)
    predictions = torch.argmax(outputs.logits, dim=-1)
    print("Predictions:", predictions)  # Print or log the predictions to examine them
    return predictions

def deidentify_text(text: str, predictions, tokens):
    anonymized_text = []
    token_texts = tokenizer.convert_ids_to_tokens(tokens['input_ids'][0])
    for idx, (token_text, pred) in enumerate(zip(token_texts, predictions[0])):
        label = model.config.id2label[pred.item()]
        if 'B-PATIENT' in label or 'L-PATIENT' in label or 'U-AGE' in label or 'U-ID' in label or 'B-DATE' in label or 'I-DATE' in label or 'L-DATE' in label or 'B-STAFF' in label or 'L-STAFF' in label:
            anonymized_text.append("[REDACTED]")
        else:
            anonymized_text.append(token_text)

    final_text = tokenizer.convert_tokens_to_string(anonymized_text)
    return final_text

@app.post("/deidentify")
def deidentify(clinical_text: str = Body(..., embed=True)):
    print('text', clinical_text)
    tokens = tokenize_text(clinical_text)
    predictions = predict_phi(tokens)
    deidentified_text = deidentify_text(clinical_text, predictions, tokens)
    return {"deidentified_text": deidentified_text}
