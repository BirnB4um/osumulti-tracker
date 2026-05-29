from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import time
from DB import DB

app = FastAPI(root_path="/api/osumulti")
db = DB()


@app.get("/latest_lobbies")
def get_latest_lobbies():
    data = db.get_latest_lobbies()
    if data is None:
        return JSONResponse(content={"message": "No data found"}, status_code=404)
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)