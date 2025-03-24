from fastapi import FastAPI
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

app = FastAPI()

@app.get("/api/test-db")
def test_db():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    cur = conn.cursor()
    cur.execute("SELECT NOW()")
    row = cur.fetchone()
    cur.close()
    conn.close()

    return {"time": row[0]}
