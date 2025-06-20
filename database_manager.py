import aiosqlite, os, discord
from typing import Tuple

class DatabaseManager:
    
    @staticmethod
    async def init_database():
        """Initialisiert die Datenbank mit allen benötigten Tabellen"""
        async with aiosqlite.connect("database.db") as db:
            # Users Tabelle für Grunddaten
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER NOT NULL,
                    balance INTEGER DEFAULT 0,
                    bank_balance INTEGER DEFAULT 0,
                    total_balance INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    knowledge JSON DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    inv_value INTEGER DEFAULT 0,
                    cmd_used INTEGER DEFAULT 0,
                    total_knowledge DEFAULT 0,
                    PRIMARY KEY (user_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS last_used (
                    user_id INTEGER NOT NULL,
                    daily TIMESTAMP,
                    weekly TIMESTAMP,
                    scavenge TIMESTAMP,
                    rob TIMESTAMP,
                    study TIMESTAMP,
                    higherlower TIMESTAMP,
                    PRIMARY KEY (user_id)
                )
            """)
            
            # Inventory Tabelle
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, item_id)
                )
            """)

            await db.commit()

            print("Database initialized!")

            
    @staticmethod            
    async def add_column_to_table(db_path, table_name, column_name, column_type="TEXT", default_value=None):
        """
        Fügt eine neue Spalte zu einer bestehenden SQLite-Tabelle hinzu.
        
        Args:
            db_path (str): Pfad zur SQLite-Datenbankdatei
            table_name (str): Name der Tabelle
            column_name (str): Name der neuen Spalte
            column_type (str): Datentyp der Spalte (TEXT, INTEGER, REAL, BLOB)
            default_value: Standardwert für die neue Spalte (optional)
        
        Returns:
            bool: True wenn erfolgreich, False bei Fehler
        """
        
        # Prüfen ob Datenbankdatei existiert
        if not os.path.exists(db_path):
            print(f"Fehler: Datenbankdatei '{db_path}' nicht gefunden.")
            return False
        
        try:
            # Verbindung zur Datenbank herstellen
            async with aiosqlite.connect(db_path) as conn:
                cursor = await conn.cursor()
                
                # Prüfen ob Tabelle existiert
                await cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                if not await cursor.fetchone():
                    print(f"Fehler: Tabelle '{table_name}' existiert nicht.")
                    await conn.close()
                    return False
                
                # Prüfen ob Spalte bereits existiert
                await cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in await cursor.fetchall()]
                
                if column_name in columns:
                    print(f"Spalte '{column_name}' existiert bereits in Tabelle '{table_name}'.")
                    await conn.close()
                    return False
                
                # ALTER TABLE Statement zusammenbauen
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                
                if default_value is not None:
                    if isinstance(default_value, str):
                        alter_query += f" DEFAULT '{default_value}'"
                    else:
                        alter_query += f" DEFAULT {default_value}"
                
                # Spalte hinzufügen
                await cursor.execute(alter_query)
                await conn.commit()
                
                print(f"Spalte '{column_name}' erfolgreich zu Tabelle '{table_name}' hinzugefügt.")
                
                # Tabellenschema anzeigen zur Bestätigung
                await cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                print("\nAktuelles Tabellenschema:")
                for col in columns_info:
                    print(f"  {col[1]} ({col[2]})")
                
                conn.close()
                return True
            
        except aiosqlite.Error as e:
            print(f"SQLite-Fehler: {e}")
            if 'conn' in locals():
                await conn.close()
            return False
        except Exception as e:
            print(f"Unerwarteter Fehler: {e}")
            if 'conn' in locals():
                await conn.close()
            return False
        
    @staticmethod
    async def get_ranking(player_id: discord.User, table: str, sort_by: str) -> Tuple[int, int]:
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute(f"SELECT user_id FROM {table} ORDER BY {sort_by} DESC")
            leaderboard = await cursor.fetchall()                           
            if not leaderboard:
                print("No ranking found")
                return
            for idx, (user_id,) in enumerate(leaderboard, start=1):
                if user_id == player_id:
                    rank = idx
                    
        return (rank, len(leaderboard))
    
    @staticmethod
    async def update_cmd_used(user_id: int):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET cmd_used=cmd_used+? WHERE user_id=?", (1, user_id))
            await db.commit()