from Logger import get_logger
from DB import DB

import os
import time
import traceback
from ossapi import Ossapi, RoomSearchMode, Scope, Grant, Room


def identity(type, value, **args):
    return value


class OsuMultiTracker:
    
    def __init__(self):
        
        self.collection_interval = 60 * 1
        
        self.data_folder = "/opt/osu_multi/data"
        
        self.db = DB(data_folder=self.data_folder)
        
        self.logger = get_logger("Tracker", os.path.join(self.data_folder, "log"))
        
        self.client_id = os.environ["CLIENT_ID"]
        self.client_secret = os.environ["CLIENT_SECRET"]
        self.redirect_url = os.environ["REDIRECT_URL"]
        
        token_dir = os.path.join(self.data_folder, "token")
        os.makedirs(token_dir, exist_ok=True)
        
        if not os.listdir(token_dir):
            self.logger.error("No token found. Please copy token file to token/ directory.")
            raise Exception("No token found. Please copy token file to token/ directory.")
        
        try:
            self.api = Ossapi(
                self.client_id, 
                self.client_secret, 
                redirect_uri=self.redirect_url, 
                scopes=[Scope.PUBLIC], 
                grant=Grant.AUTHORIZATION_CODE,
                token_directory=token_dir
            )
        except Exception as e:
            self.logger.error(f"Error initializing Ossapi: {e}", exc_info=True)
            raise e
    
        self.api._instantiate_type = identity
        
        
    def collect_lobbies(self):
        params = {
            # "limit": 10,
            "mode": "active",
            "sort": "created",
            "type_group": "realtime",
        }
        try:
            lobbies = self.api._request(None, "GET", "/rooms", params=params)
        except Exception as e:
            self.logger.error(f"Error occurred in API request: {e}", exc_info=True)
            return
        
        self.db.add_lobby(lobbies)
        

    def run(self):
        self.logger.info("Starting tracker")
        
        while True:
            self.collect_lobbies()
            time.sleep(self.collection_interval)
            