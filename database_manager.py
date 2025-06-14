import aiosqlite

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
                    PRIMARY KEY (user_id)
                )
            """)
            
            # Inventory Tabelle
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    inv_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    item_metadata JSON DEFAULT NULL,
                    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

            print("Database initialized!")