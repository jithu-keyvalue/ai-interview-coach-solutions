from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/api/time")
def get_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return { "time": current_time }