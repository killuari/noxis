import discord, aiosqlite
from user_manager import UserManager

class LevelManager:
    
    @staticmethod
    async def add_experience(user_id: int, amount: int) -> None:
        if not UserManager.user_exists(user_id):
            print("Invalid user_id. User not found")
            return 
        
        async with aiosqlite.connect("database.db") as db: 
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET experience=experience+? WHERE user_id=?", (abs(amount), user_id))
            
    
    @staticmethod
    async def set_experience(user_id: int, amount: int) -> None:
        if not UserManager.user_exists(user_id):
            print("Invalid user_id. User not found")
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET experience=?`WHERE user_id=?", (abs(amount), user_id))