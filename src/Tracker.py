from Logger import get_logger
from DB import DB

import requests
import os
import time
import traceback
import signal
from ossapi import Ossapi, RoomSearchMode, Scope, Grant, Room


def identity(type, value, **args):
    return value

class TimeoutException(BaseException):
    # needs to be BaseException to not get caught in a try except block from the api
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("The operation took too long and was forced to abort.")

signal.signal(signal.SIGALRM, timeout_handler)


class OsuMultiTracker:
    
    def __init__(self):
        
        self.collection_interval = 60 * 1
        self.api_reconnect_interval = 60 * 60 * 12 # 12h
        self.last_api_connection_time = 0
        
        self.data_folder = "/opt/osu_multi/data"
        
        self.logger = get_logger("Tracker", os.path.join(self.data_folder, "log"))
        
        self.db = DB(data_folder=self.data_folder)
        
        self.client_id = os.environ["CLIENT_ID"]
        self.client_secret = os.environ["CLIENT_SECRET"]
        self.redirect_url = os.environ["REDIRECT_URL"]
        
        self.token_dir = os.path.join(self.data_folder, "token")
        os.makedirs(self.token_dir, exist_ok=True)
        
        if not os.listdir(self.token_dir):
            self.logger.error("No token found. Please copy token file to token/ directory.")
            raise Exception("No token found. Please copy token file to token/ directory.")
        
        self.connect_api()
    
    def connect_api(self):
        self.logger.info("Connecting to API...")
        try:
            self.api = Ossapi(
                self.client_id, 
                self.client_secret, 
                redirect_uri=self.redirect_url, 
                scopes=[Scope.PUBLIC], 
                grant=Grant.AUTHORIZATION_CODE,
                token_directory=self.token_dir
            )
            self.api._instantiate_type = identity
            self.last_api_connection_time = time.time()
        except Exception as e:
            self.logger.error(f"Error connecting to API: {e}", exc_info=True)
    
        
    def collect_lobbies(self):
        params = {
            "mode": "active",
            "sort": "created",
            "type_group": "realtime",
        }
        try:
            signal.alarm(60)
            lobbies = self.api._request(None, "GET", "/rooms", params=params)
            signal.alarm(0)
            self.db.add_lobby(lobbies)
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error occurred in API request: {e}", exc_info=True)
            self.connect_api()
        except Exception as e:
            self.logger.error(f"Error occurred in API request: {e}", exc_info=True)
        finally:
            signal.alarm(0)
        
    
    
    def collect_players(self):
        players = self.db.get_player_ids()
        if not players:
            return
        
        params = {
            "ids": players,
            "exclude_bots": None,
            "ruleset_id": 0,
        }
        try:
            signal.alarm(60)
            users = self.api._request(None, "GET", "/users/lookup", params=params)["users"]
            signal.alarm(0)
            self.db.update_players(users)
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error occurred in API request: {e}", exc_info=True)
            self.connect_api()
        except Exception as e:
            self.logger.error(f"Error occurred in API request: {e}", exc_info=True)
        finally:
            signal.alarm(0)
        
    

    def run(self):
        self.logger.info("Starting tracker")
        
        while True:
            try:
                
                # reconnect api check
                if (time.time() - self.last_api_connection_time) > self.api_reconnect_interval:
                    self.logger.info("Reconnecting to API. Triggered by interval.")
                    self.connect_api()
                    time.sleep(5)
                
                st = time.time()
                self.collect_lobbies()
                time.sleep(30)
                self.collect_players()
                time.sleep(max(0, self.collection_interval - (time.time() - st)))
            except TimeoutException as e:
                self.logger.error("Timeout occured through signal.", exc_info=True)
                self.connect_api()
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)
        
        self.logger.error("Error: Stopping tracker. This should never happen.")
            