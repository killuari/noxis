import aiosqlite, math
from typing import Tuple
from user_manager import UserManager


class EconomyManager:
    # Get the balance and bank_balance
    @staticmethod
    async def get_balance(user_id: int) -> Tuple[int, int]:
        """Get a tuple of balance, bank_balance"""
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()   
            await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user_id,))
            return await cursor.fetchone()
    
    @staticmethod
    async def get_total_balance(user_id: int):
        if not await UserManager.user_exists(user_id):
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
    async def add_money(user_id: int, amount: int, bank: bool=False) -> int:
        """Adds money to specified user and returns amount of money which would be over the max_bank_limit of user if money added to bank"""
        if not await UserManager.user_exists(user_id):
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
                max_bank_balance = await EconomyManager.get_max_bank_capacity(user_id)
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
    async def remove_money(user_id: int, amount: int, bank: bool=False) -> int: #returns amount of money that couldnt be removed
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        money_left = 0
        current_balance = await EconomyManager.get_balance(user_id)
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            if not bank:
                current_balance = current_balance[0]
                balance = "balance"
            else:
                current_balance = current_balance[1]
                balance = "bank_balance"

            if (current_balance - amount) < 0:
                new_balance = 0
                money_left = abs(current_balance - amount)
                await cursor.execute(f"UPDATE users SET {balance}=? WHERE user_id=?", (new_balance, user_id))
            else:
                await cursor.execute(f"UPDATE users SET {balance}={balance}-? WHERE user_id=?", (abs(amount), user_id))
            await db.commit()

            total = await EconomyManager.get_total_balance(user_id)
            await cursor.execute("UPDATE users SET total_balance=? WHERE user_id=?", (total, user_id)) 
            await db.commit()
        return money_left                              
    
    @staticmethod
    async def round_one_significant(n: int) -> int:
        """ Rundet einen int auf eine signifikante Stelle."""
        if n == 0:
            return 0
        
        # Anzahl der Stellen bestimmen
        digits = int(math.floor(math.log10(n))) + 1
        factor = 10 ** (digits - 1)
        leading = n / factor
        floored = math.floor(leading)

        if (leading - floored) >= 0.5:
            rounded_leading = floored + 1
        else:
            rounded_leading = floored

        return rounded_leading * factor

    @staticmethod
    async def get_max_bank_capacity(user_id: int) -> int:
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return None
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT level FROM users WHERE user_id=?", (user_id,)) 
            level = (await cursor.fetchone())[0]

        base_capacity = 1000
        scaling_factor = 2
        return await EconomyManager.round_one_significant(int(base_capacity * (level ** scaling_factor)))