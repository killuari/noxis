import aiosqlite
from items import *
from user_manager import UserManager

class InventoryManager:
    @staticmethod
    async def add_item(user_id: int, item_id: int, quantity: int = 1):
        """Fügt anzahl an item einem user inventar hinzu"""
        # Check if item and user exists
        if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            item = await ItemManager.get_item(item_id)

            # Add item if not stackable
            if item.max_stack == 1:
                await cursor.execute("INSERT INTO inventory (user_id, item_id, item_metadata) VALUES (?, ?, ?)", (user_id, item_id, item.metadata))
                return

            # Add quantity if user already has item
            # if await InventoryManager.user_has_item(user_id, item_id):
            #     # check if user has already reached max_stack
            #     if await InventoryManager.user_has_item(user_id, item_id, (await ItemManager.get_item(item_id)).max_stack):
            #         print("User already has max stack of specified item")
            #     else:
            #         await cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?", (quantity, user_id, item_id))
            # else:
            #     await cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, quantity))

            # await db.commit()

    @staticmethod
    async def remove_item(user_id: int, item_id: int, quantity: int = 1):
        """Entfernt anzahl an item von einem user inv"""
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()

            # TODO: wird erst hinzugefügt wenn non stackable items eindeutig sind
            if not (await ItemManager.get_item(item_id)).stackable:
                return
            
            if await InventoryManager.user_has_item(user_id, item_id, quantity):
                await cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?", (quantity, user_id, item_id))
                
                # Entfern ganzen Eintrag aus Inventory wenn quantity = 0
                await cursor.execute("SELECT quantity FROM inventory WHERE (user_id, item_id) = (?, ?)", (user_id, item_id))
                remaining = (await cursor.fetchone())[0]
                if remaining == 0:
                    await cursor.execute("DELETE FROM inventory WHERE (user_id, item_id) = (?, ?)", (user_id, item_id))
                
                await db.commit()
                
    @staticmethod
    async def get_user_item_quantity(user_id: int, item_id: int) -> int:
        """Get quantity of specified item in user inventory"""
        if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT quantity FROM inventory WHERE (user_id, item_id) = (?, ?)", (user_id, item_id))
            result = await cursor.fetchone()
            if result:
                return result[0]
            
            return 0

    @staticmethod
    async def get_inventory():
        pass

    @staticmethod
    async def get_inventory_value():
        pass