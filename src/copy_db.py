import sqlite3

def create_safe_copy(live_db_path, output_path):
    source = sqlite3.connect(live_db_path)
    dest = sqlite3.connect(output_path)
    
    with dest:
        source.backup(dest)
    
    dest.close()
    source.close()
    print(f"Safe copy created at {output_path}")

create_safe_copy("../data/lobbies.db", "../data/lobbies_copy.db")