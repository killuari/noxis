import aiosqlite
from items import *
from user_manager import UserManager

class InventoryManager:
    @staticmethod
    async def add_item(user_id: int, item_id: int, quantity: int = 1):
        """Fügt anzahl an item einem user inventar hinzu"""
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()

            # Check if item and user exists
            if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
                return

            # Add item if not stackable
            if not (await ItemManager.get_item(item_id)).stackable:
                await cursor.execute("INSERT INTO inventory (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
                return

            # Add quantity if user already has item
            if await InventoryManager.user_has_item(user_id, item_id):
                # check if user has already reached max_stack
                if await InventoryManager.user_has_item(user_id, item_id, (await ItemManager.get_item(item_id)).max_stack):
                    print("User already has max stack of specified item")
                else:
                    await cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?", (quantity, user_id, item_id))
            else:
                await cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, quantity))

            await db.commit()

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