import aiosqlite, discord
from typing import Tuple
from user_manager import UserManager


class EconomyManager:
    # Get the balance and bank_balance
    @staticmethod
    async def get_balance(user_id: int) -> Tuple[int, int]:
        if not UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()   
            await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user_id,))
            return await cursor.fetchone()
    
    @staticmethod
    async def get_total_balance(user_id: int):
        if not UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user_id,)) 
            balance, bank_balance = await cursor.fetchone()
            total = balance + bank_balance
            
        return total 
    
    
    # Add money to a specific users balance/bank_balance
    @staticmethod
    async def add_money(user_id: int, amount: int, bank: bool=False) -> int: # returns amount of money which would be over the max_bank_limit of user
        if not UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        money_left = 0

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            if not bank:
                await cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (abs(amount), user_id))
                await db.commit()

                total = await EconomyManager.get_total_balance(user_id)
                await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                await db.commit()
            else:
                current_bank_balance = (await EconomyManager.get_balance(user_id))[1]
                max_bank_balance = EconomyManager.get_max_bank_capacity(user_id)
                if max_bank_balance <= current_bank_balance + amount:
                    money_left = current_bank_balance + amount - max_bank_balance
                    await cursor.execute("UPDATE users SET bank_balance=? WHERE user_id=?", (max_bank_balance, user_id))
                    await db.commit()
                else:
                    await cursor.execute("UPDATE users SET bank_balance=bank_balance+? WHERE user_id=?", (abs(amount), user_id))
                    await db.commit()

                total = await EconomyManager.get_total_balance(user_id)
                await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                await db.commit()
        
        return money_left
    
    
    # Remove money from a specific users balance/bank_balance, balance/bank_balance can not go below zero    
    @staticmethod
    async def remove_money(user_id: int, amount: int, bank: bool=False):
        if not UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
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

                total = await EconomyManager.get_total_balance(user_id)
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

                total = await EconomyManager.get_total_balance(user_id)
                await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
                await db.commit()                                    
    
    @staticmethod
    async def get_max_bank_capacity(user_id: int) -> int:
        if not UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT level FROM users WHERE user_id=?", (user_id,)) 
            level = await cursor.fetchone()

        # Option 2: Exponential scaling
        base_capacity = 10000
        scaling_factor = 1.2
        return int(base_capacity * (level ** scaling_factor))