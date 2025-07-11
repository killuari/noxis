import aiosqlite, discord, aiohttp, math
from user_manager import UserManager
from typing import Tuple


class LevelManager:
    @staticmethod
    def round_level_requirement(n: int) -> int:
        """ Rundet einen int, dass die letzten beiden stellen 0 werden"""
        if n < 100:
            return 100
        
        leading = n / 100
        floored = math.floor(leading)

        if (leading - floored) >= 0.5:
            rounded_leading = floored + 1
        else:
            rounded_leading = floored

        return rounded_leading * 100

    # calculates the experience required for a given level
    @staticmethod
    def calculate_exp_for_level(level: int) -> int:
        base_exp = 100
        scaling_factor = 1.5
        return LevelManager.round_level_requirement(base_exp * (level ** scaling_factor))

    # calculates the level and remaining experience from a given total experience
    @staticmethod
    def calculate_level_from_exp(exp: int) -> Tuple[int, int]:
        level = 1
        remaining_exp = exp
        
        while remaining_exp >= LevelManager.calculate_exp_for_level(level+1):
            remaining_exp -= LevelManager.calculate_exp_for_level(level+1)
            level += 1
            
        return (level, remaining_exp)
    
    # adds experience to a user and updates their level  
    @staticmethod
    async def add_experience(user_id: int, amount: int, webhook_url: str = None) -> None:
        """Adds experience to a specific user and sends level up message if user levels up and webhook_url is given"""
        if not await UserManager.user_exists(user_id):
            print("Invalid user_id. User not found")
            return 
        
        async with aiosqlite.connect("database.db") as db: 
            cursor = await db.cursor()
            await cursor.execute("SELECT level, experience FROM users WHERE user_id=?", (user_id,))
            data = await cursor.fetchone()
            cur_level, cur_experience = data
            total_exp = cur_experience + abs(amount)
            new_exp, new_level = total_exp, cur_level
            
            while new_exp >= LevelManager.calculate_exp_for_level(new_level+1):
                new_exp -= LevelManager.calculate_exp_for_level(new_level+1)
                new_level += 1
            
            await cursor.execute("UPDATE users SET level=?, experience=? WHERE user_id=?", (new_level, new_exp, user_id))
            await db.commit()

            if new_level > cur_level and webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(webhook_url, session=session)
                    while new_level > cur_level:
                        cur_level += 1
                        await webhook.send(embed=discord.Embed(title="Level Up", description=f"You reached level **{cur_level}**!", color=discord.Color.gold()))
            
    # sets the experience of a user to a specific amount and updates their level           
    @staticmethod
    async def set_experience(user_id: int, amount: int) -> None:
        if not await UserManager.user_exists(user_id):
            print("Invalid user_id. User not found")
            return

        async with aiosqlite.connect("database.db") as db: 
            cursor = await db.cursor()
            new_level, new_exp = LevelManager.calculate_level_from_exp(amount)

            await cursor.execute("UPDATE users SET experience=?, level=? WHERE user_id=?", (new_exp, new_level, user_id))
            await db.commit()            

            
    @staticmethod
    async def get_lvl_exp(user_id: int) -> Tuple[int, int]:
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT level, experience FROM users WHERE user_id=?", (user_id,))            
            level, experience = await cursor.fetchone()
            
        return (level, experience)