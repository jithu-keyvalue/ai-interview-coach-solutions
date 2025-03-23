from fastapi import FastAPI
import datetime

app = FastAPI()

@app.get("/")
def hello_world():
    return "Hello world!"


@app.get("/api/time")
def get_time():
    current_time = datetime.datetime.now()
    return { "time": current_time }