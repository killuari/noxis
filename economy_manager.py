import aiosqlite, discord
from typing import Tuple
from user_manager import UserManager


class EconomyManager:
    # Get the balance and bank_balance
    @staticmethod
    async def get_user_balance(user_id: int) -> Tuple[int, int]:
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            if await UserManager.user_exists(user_id):            
                await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user_id,))
                return await cursor.fetchone()
            else:
                print("User not found")        
    
    
    # Add money to a specific users balance/bank_balance
    @staticmethod
    async def add_money(user_id: int, amount: int, bank: bool=False):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            if await UserManager.user_exists(user_id):
                if not bank:
                    await cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (abs(amount), user_id))
                    await db.commit()
                    total = await EconomyManager.update_total_balance(user_id)
                    await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                    await db.commit()
                else:
                    await cursor.execute("UPDATE users SET bank_balance=bank_balance+? WHERE user_id=?", (abs(amount), user_id))
                    await db.commit()
                    total = await EconomyManager.update_total_balance(user_id)
                    await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                    await db.commit()
            else:
                print("User not found")    
    
    
    # Remove money from a specific users balance/bank_balance, balance/bank_balance can not go below zero    
    @staticmethod
    async def remove_money(user_id: int, amount: int, bank: bool=False):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            if await UserManager.user_exists(user_id):
                if not bank:
                    await cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
                    current_balance = await cursor.fetchone()
                    if current_balance is None:
                        print("balance not found")
                        return 
                    if (current_balance[0] - amount) < 0:
                        new_balance = 0
                        await cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
                        await db.commit()
                    else:
                        await cursor.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (abs(amount), user_id))
                        await db.commit()
                    total = await EconomyManager.update_total_balance(user_id)
                    await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                    await db.commit() 
                else:
                    await cursor.execute("SELECT bank_balance FROM users WHERE user_id=?", (user_id,))
                    current_balance = await cursor.fetchone()
                    if current_balance is None:
                        print("bank_balance not found")
                        return  
                    if (current_balance[0]  - amount) < 0:
                        new_balance = 0
                        await cursor.execute("UPDATE users SET bank_balance=? WHERE user_id=?", (new_balance, user_id))
                        await db.commit()    
                    else:
                        await cursor.execute("UPDATE users SET bank_balance=bank_balance-? WHERE user_id=?", (abs(amount), user_id))
                        await db.commit()
                    total = await EconomyManager.update_total_balance(user_id)
                    await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                    await db.commit()                                   
            else:
                print("User not found") 


    @staticmethod
    async def get_total_balance(user_id: int):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user_id,)) 
            balance, bank_balance = await cursor.fetchone()
            total = balance + bank_balance
            
        return total 