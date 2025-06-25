import aiosqlite, json, datetime
from items import *
from user_manager import UserManager

class InventoryManager:
    @staticmethod
    async def add_item(user_id: int, item_id: int, quantity: int = 1) -> int: # returns quantity that would exceed the max stack of specified item
        """Fügt anzahl an item einem user inventar hinzu"""                   # returns 0 if operation was successful
        # Check if item and user exists
        if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            item = await ItemManager.get_item(item_id)

            item_quantity = await InventoryManager.get_item_quantity(user_id, item_id)
            
            # Add quantity if user already has item
            if item_quantity + quantity > item.max_stack:
                print("Quantity exceeds max stack of specified item")
                return item_quantity + quantity - item.max_stack
            
            if item_quantity > 0:
                await cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?", (quantity, user_id, item_id))
            else:
                await cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, quantity))

            await db.commit()
            await InventoryManager.update_inventory_value(user_id)
            return 0

    @staticmethod
    async def remove_item(user_id: int, item_id: int, quantity: int = 1):
        """Entfernt anzahl an item von einem user inv"""
        if not await ItemManager.item_exists(item_id) or not await UserManager.user_exists(user_id):
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            remaining = await InventoryManager.get_item_quantity(user_id, item_id)

            if remaining <= quantity:
                await cursor.execute("DELETE FROM inventory WHERE (user_id, item_id) = (?, ?)", (user_id, item_id))
            else:
                await cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE (user_id, item_id) = (?, ?)", (quantity, user_id, item_id))
                
            await db.commit()
            await InventoryManager.update_inventory_value(user_id)
                
    @staticmethod
    async def get_item_quantity(user_id: int, item_id: int) -> int:
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
    async def get_inventory(user_id: int) -> List[Item]:
        """Get List of all Items of an Inventory"""
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return
        
        items = []
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (user_id,))
            result = await cursor.fetchall()
            
            if not result:
                print("User doesnt have items")
                return []
            
            for item_values in result:
                item = await ItemManager.get_item(item_values[1])
                item.quantity = item_values[2]
                item.acquired_at = datetime.datetime.strptime(item_values[-1], "%Y-%m-%d %H:%M:%S").timestamp()
                items.append(item)

        return items

    @staticmethod
    async def get_inventory_sorted_by_rarity(user_id: int) -> list:
        """Gibt alle Items eines Inventars sortiert nach Rarity (legendary -> common) zurück"""
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return
        
        items = []
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (user_id,))
            result = await cursor.fetchall()
            
            if not result:
                print("User doesnt have items")
                return []
            
            for item_values in result:
                item = await ItemManager.get_item(item_values[1])
                item.quantity = item_values[2]
                item.acquired_at = datetime.datetime.strptime(item_values[-1], "%Y-%m-%d %H:%M:%S").timestamp()
                items.append(item)

        # Sortiere nach Rarity absteigend (LEGENDARY zuerst)
        items.sort(key=lambda x: x.rarity.value, reverse=True)
        return items

    @staticmethod
    async def get_inventory_value(user_id: int):
        if not await UserManager.user_exists(user_id):
            print("User doesnt exist")
            return
         
        return sum(item.value * item.quantity for item in await InventoryManager.get_inventory(user_id))
    
    
    @staticmethod
    async def update_inventory_value(user_id: int):
        value = await InventoryManager.get_inventory_value(user_id)
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET inv_value=? WHERE user_id=?", (value, user_id))
            await db.commit()
    