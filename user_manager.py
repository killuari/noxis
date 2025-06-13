import aiosqlite

class UserManager:

    @staticmethod
    async def user_exists(user_id: int) -> bool:
        """Prüft ob user existiert"""
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            return await cursor.fetchone() is not None
        
    @staticmethod
    async def add_user(user_id: int):
        """Fügt user hinzu wenn nicht existent"""
        if not await UserManager.user_exists(user_id):
            async with aiosqlite.connect("database.db") as db:
                cursor = await db.cursor()
                await cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
                await cursor.execute("INSERT INTO last_used (user_id) VALUES (?)", (user_id,))
                await db.commit()