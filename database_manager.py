import sqlite3

class DatabaseManager:
    
    async def init_database(self):
        """Initialisiert die Datenbank mit allen benötigten Tabellen"""
        async with sqlite3.connect("database.db") as db:
            # Users Tabelle für Grunddaten
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER NOT NULL,
                    balance INTEGER DEFAULT 0,
                    bank_balance INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id)
                )
            """)
            
            # Inventory Tabelle
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)