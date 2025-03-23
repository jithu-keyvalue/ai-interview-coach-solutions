from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/api/time")
def get_time(name: str = ''):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return { "message": f"Hi {name}! It's {current_time}" }
