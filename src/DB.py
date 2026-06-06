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
                
        self.sql_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.sql_cursor = self.sql_connection.cursor()
        
        self._init_sql()
        
        
        
    def _init_sql(self):
        if not (self.sql_connection and self.sql_cursor):
            self.logger.error("Error in init SQL: No SQL connection.")
            return

        self.sql_cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS lobbies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER DEFAULT (strftime('%s', 'now')),
                data BLOB
            );
            
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT UNIQUE,
                username TEXT DEFAULT '<unknown>',
                data TEXT DEFAULT '{}',
                timestamp INTEGER DEFAULT (strftime('%s', 'now'))
            );
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
    
    
    def set_target_players(self, ids:list[str]):
        """
        Adds new ids and remove ids that are not in the list anymore
        """
        
        try:
            self.sql_cursor.execute(
                """
                DELETE FROM players
                WHERE player_id NOT IN ({})
                """.format(",".join("?" for _ in ids)),
                ids
            )
            self.sql_cursor.executemany(
                """
                INSERT OR IGNORE INTO players (player_id)
                VALUES (?)
                """,
                [(player_id,) for player_id in ids]
            )
            self.sql_connection.commit()
        except Exception as e:
            self.logger.error(f"Error while setting target players in DB: {str(e)}", exc_info=True)
            self.sql_connection.rollback()
    
    
    def get_player_ids(self):
        try:
            self.sql_cursor.execute(
                """
                SELECT player_id FROM players
                """
            )
            result = self.sql_cursor.fetchall()
            return [row[0] for row in result]
        except Exception as e:
            self.logger.error(f"Error while fetching player ids from DB: {str(e)}", exc_info=True)
            return []
    
    
    def get_players(self):
        try:
            self.sql_cursor.execute(
                """
                SELECT player_id, data FROM players
                """
            )
            result = self.sql_cursor.fetchall()
            return {row[0]: json.loads(row[1]) for row in result}
        except Exception as e:
            self.logger.error(f"Error while fetching players from DB: {str(e)}", exc_info=True)
            return []
    
    
    def update_players(self, players:list[dict]):
        try:
            self.sql_cursor.executemany(
                """
                INSERT INTO players (player_id, username, data)
                VALUES (?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    username=excluded.username,
                    data=excluded.data,
                    timestamp=strftime('%s', 'now')
                """,
                [(p["id"], p["username"], json.dumps(p)) for p in players]
            )
            self.sql_connection.commit()
        except Exception as e:
            self.logger.error(f"Error while updating players in DB: {str(e)}", exc_info=True)
            self.sql_connection.rollback()
            
            
    def get_last_update_time(self):
        # get the latest timestamp for both tables individually
        
        try:
            self.sql_cursor.execute(
                """
                SELECT MAX(timestamp) FROM lobbies
                """
            )
            lobbies_time = self.sql_cursor.fetchone()[0]

            self.sql_cursor.execute(
                """
                SELECT MAX(timestamp) FROM players
                """
            )
            players_time = self.sql_cursor.fetchone()[0]

            return {
                "last_lobbies_time": lobbies_time,
                "last_players_time": players_time
            }
        except Exception as e:
            self.logger.error(f"Error while fetching last update time from DB: {str(e)}", exc_info=True)
            return None