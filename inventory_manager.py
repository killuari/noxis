import aiosqlite
from items import *
from user_manager import UserManager

class InventoryManager:
    @staticmethod
    async def add_item(user_id: int, item_id: int, quantity: int = 1):
        """Fügt anzahl an item einem user inventar hinzu"""
        async with aiosqlite.connect("database.db") as db:
            if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
                return
            
            cursor = await db.cursor()
            await cursor.execute("SELECT ")
            await cursor.execute("UPDATE inventory SET (item_id)")

    @staticmethod
    async def remove_item(user_id: int, item_id: int, quantity: int = 1):
        pass

    @staticmethod
    async def user_has_item(user_id: int, item_id: int, quantity: int = 1) -> bool:
        """Prüft ob user bestimmtes item besitzt"""
        async with aiosqlite.connect("database.db") as db:
            if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
                return
            
            cursor = await db.cursor()
            await cursor.execute("SELECT quantity FROM inventory WHERE (user_id, item_id) = (?, ?)", (user_id, item_id))
            
            if (await ItemManager.get_item(item_id)).stackable:
                result = await cursor.fetchone()
                if result:
                    return result[0] >= quantity
                else:
                    return False
            else:
                result = await cursor.fetchall()
                if result:
                    return len(result)
                else:
                    return False

    @staticmethod
    async def get_inventory():
        pass

    @staticmethod
    async def get_inventory_value():
        pass