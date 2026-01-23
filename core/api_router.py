from typing import Union
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models.parameters import Item
'''
You can optionally deploy your FastAPI app to FastAPI Cloud, go and join the waiting list if you haven't.
'''

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

print ("server started");


origins = [
    "http://localhost:8000",  # Example frontend origin
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET, POST"],
    allow_headers=["*"],  
)


@app.get("/")
async def main():
    return FileResponse("index.html")


@app.get("/preset/{preset_id}")
def get_by_preset(preset_id: str):
    return {"your preset": preset_id}


@app.post("/params")
def get_by_params(params: Item):
    return {"your params": params}