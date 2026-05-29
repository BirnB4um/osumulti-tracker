import sqlite3
import os
import json
import time
import zlib
from Logger import get_logger


class DB:
    
    def __init__(self, data_folder:str="/opt/osu_multi/data"):
        
        self.logger = get_logger("Tracker", os.path.join(data_folder, "log"))

        self.db_path = os.path.join(data_folder, "lobbies.db")
                
        self.sql_connection = sqlite3.connect(self.db_path, check_same_thread=True)
        self.sql_cursor = self.sql_connection.cursor()
        
        self._init_sql()
        
        
        
    def _init_sql(self):
        if not (self.sql_connection and self.sql_cursor):
            self.logger.error("Error in init SQL: No SQL connection.")
            return

        self.sql_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lobbies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                data BLOB
            )
            """
        )

        self.sql_connection.commit()
        
        
    def add_lobby(self, lobby_data:list[dict]):
        try:
            compressed_data = zlib.compress(json.dumps(lobby_data).encode("utf-8"), level=9)
            self.sql_cursor.execute(
                """
                INSERT INTO lobbies (data)
                VALUES (?)
                """, 
                (compressed_data,)
            )
            self.sql_connection.commit()
        except Exception as e:
            self.logger.error(f"Error while saving results to DB: {str(e)}", exc_info=True)
            self.sql_connection.rollback()
            
            
    def get_latest_lobbies(self) -> dict:
        try:
            self.sql_cursor.execute(
                """
                SELECT timestamp, data FROM lobbies
                ORDER BY timestamp DESC
                LIMIT 1
                """
            )
            result = self.sql_cursor.fetchone()
            if result:
                timestamp = result[0]
                compressed_data = result[1]
                decompressed_data = zlib.decompress(compressed_data).decode("utf-8")
                return {"timestamp": timestamp, "lobbies": json.loads(decompressed_data)}
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error while fetching latest lobbies from DB: {str(e)}", exc_info=True)
            return None