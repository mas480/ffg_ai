from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from analyzer import (
    analyze_profile_image,
    analyze_multiple_photos,
    analyze_conversation_image,
    suggest_first_messages_from_profile,
)
import shutil
import tempfile
import os

app = FastAPI()

# Разрешаем CORS для Gradio или других UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Утилита сохранения временного файла
def save_temp_file(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        return tmp.name

@app.post("/analyze_profile_image")
async def analyze_profile_image_endpoint(file: UploadFile = File(...)):
    path = save_temp_file(file)
    result = analyze_profile_image(path)
    os.remove(path)
    return JSONResponse(content=result)

@app.post("/analyze_multiple_photos")
async def analyze_multiple_photos_endpoint(files: list[UploadFile] = File(...)):
    paths = [save_temp_file(f) for f in files]
    result = analyze_multiple_photos(paths)
    for p in paths:
        os.remove(p)
    return JSONResponse(content=result)

@app.post("/analyze_conversation_image")
async def analyze_conversation_image_endpoint(file: UploadFile = File(...)):
    path = save_temp_file(file)
    result = analyze_conversation_image(path)
    os.remove(path)
    return JSONResponse(content=result)

@app.post("/suggest_first_messages")
async def suggest_first_messages_endpoint(file: UploadFile = File(...)):
    path = save_temp_file(file)
    result = suggest_first_messages_from_profile(path)
    os.remove(path)
    return JSONResponse(content={"messages": result})