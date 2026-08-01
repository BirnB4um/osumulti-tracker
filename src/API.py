from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import time
import os
from DB import DB
from Logger import get_logger

app = FastAPI(root_path="/api/osumulti")
db = DB()

data_folder = "/opt/osu_multi/data"
logger = get_logger("API", os.path.join(data_folder, "log"))


"""
country:de,us,fr; public:true; diff:2.1-4.5; playercount:1-5; user:peppy; limit:10

filter = {
    "country": ["de", "us", "fr"],
    "public": True,
    "diff": [2.1, 4.5],
    "playercount": [1, 5],
    "user": ["user1", "user2"],
    "limit": 10
}
"""


@app.post("/filter_latest_lobbies")
async def filter_latest_lobbies(request: Request):
    search_filter = await request.json()
    
    data = db.get_latest_lobbies()
    if data is None:
        return JSONResponse(content={"message": "No data found"}, status_code=404)
    
    # validate filter
    validated_filter = {}
    for key, value in search_filter.items():
        if key == "country":
            if isinstance(value, list) and all(isinstance(v, str) for v in value):
                validated_filter["country"] = [v.lower() for v in value]
        elif key == "public":
            if isinstance(value, bool):
                validated_filter["public"] = value
        elif key == "diff":
            if isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float, str)) for v in value):
                validated_filter["diff"] = [float(v) for v in value]
        elif key == "playercount":
            if isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float, str)) for v in value):
                validated_filter["playercount"] = [int(v) for v in value]
        elif key == "user":
            if isinstance(value, list) and all(isinstance(v, str) for v in value):
                validated_filter["user"] = value
        elif key == "limit":
            if isinstance(value, int) and value > 0:
                validated_filter["limit"] = value
                
    # apply filter
    def apply_filter(lobby:dict):
        match = True
        score = 0
        for key, value in validated_filter.items():
            if key == "country":
                player_countries = [p["country_code"].lower() for p in lobby["recent_participants"]]
                hits = sum(1 for pc in player_countries if pc in value)
                if hits == 0:
                    match = False
                    break
                score += hits
            elif key == "public":
                if lobby.get("has_password") == value:
                    match = False
                    break
            elif key == "diff":
                if not (value[0] <= lobby["difficulty_range"]["max"] and value[1] >= lobby["difficulty_range"]["min"]):
                    match = False
                    break
            elif key == "playercount":
                player_count = len(lobby["recent_participants"])
                if not (value[0] <= player_count <= value[1]):
                    match = False
                    break
            elif key == "user":
                lobby_players = set([p["username"] for p in lobby["recent_participants"]])
                if not any([user in lobby_players for user in value]):
                    match = False
                    break
                
        return match, score, lobby
    
    filtered_lobbies = [apply_filter(lobby) for lobby in data["lobbies"]]
    filtered_lobbies = [lobby for lobby in filtered_lobbies if lobby[0]] # filter matches
    filtered_lobbies.sort(key=lambda x: x[1], reverse=True) # sort by score
    filtered_lobbies = [lobby[2] for lobby in filtered_lobbies] # extract lobby data
    
    if "limit" in validated_filter:
        filtered_lobbies = filtered_lobbies[:validated_filter["limit"]]
    
    data["lobbies"] = filtered_lobbies
    return data


@app.get("/latest_lobbies")
async def get_latest_lobbies():
    data = db.get_latest_lobbies()
    if data is None:
        return JSONResponse(content={"message": "No data found"}, status_code=404)
    return data


@app.get("/players")
async def players():
    data = db.get_players()
    if data is None:
        return JSONResponse(content={"message": "No data found"}, status_code=404)
    
    """
    {
        "12345": {
            "id": "12345",
            "username": "Player1",
            ...
        },
        "67890": {
            "id": "67890",
            "username": "Player2",
            ...
        }
    }
    """
    
    return data


@app.post("/set_target_players")
async def set_target_players(request: Request):
    """
    {
    "ids": ["12345", "67890"]
    }
    """
    
    data = await request.json()
    ids = data["ids"]
    db.set_target_players(ids)
    return JSONResponse(content={"message": "Target players set successfully"}, status_code=200)


@app.get("/last_update_time")
async def get_last_update_time():
    data = db.get_last_update_time()
    if data is None:
        return JSONResponse(content={"message": "No data found"}, status_code=404)
    return data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)