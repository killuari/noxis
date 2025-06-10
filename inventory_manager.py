import aiosqlite, json
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

            # Add item if not stackable
            if item.max_stack == 1:
                for i in range(quantity):
                    await cursor.execute("INSERT INTO inventory (user_id, item_id, item_metadata) VALUES (?, ?, ?)", (user_id, item_id, json.dumps(item.metadata)))
                await db.commit()
                return

            item_quantity = await InventoryManager.get_user_item_quantity(user_id, item_id)
            max_stack = (await ItemManager.get_item(item_id)).max_stack
            
            # Add quantity if user already has item
            if item_quantity + quantity > max_stack:
                print("Quantity exceeds max stack of specified item")
                return item_quantity + quantity - max_stack
            
            if item_quantity > 0:
                await cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?", (quantity, user_id, item_id))
            else:
                await cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, quantity))

            await db.commit()
            return 0

    @staticmethod
    async def remove_item(inv_id: int = None, quantity: int = 1):
        """Entfernt anzahl an item von einem user inv"""
        if not await InventoryManager.record_exists(inv_id):
            print("Inventory record not found")
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT quantity FROM inventory WHERE (inv_id) = (?)", (inv_id,))
            remaining = (await cursor.fetchone())[0]

            if remaining <= quantity:
                await cursor.execute("DELETE FROM inventory WHERE (inv_id) = (?)", (inv_id,))
            else:
                await cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE inv_id = ?", (quantity, inv_id))
                
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
    async def record_exists(inv_id: int) -> bool:
        """Checks for specific inventory record"""
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM inventory WHERE (inv_id) = (?)", (inv_id,))
            
            result = await cursor.fetchone()
            if result:
                return True
            return False

    @staticmethod
    async def get_item_metadata(inv_id: int) -> dict:
        """Get metadata of specific item by inventory id"""
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT item_metadata FROM inventory WHERE (inv_id) = ?", (inv_id,))

            result = await cursor.fetchone()
            if result:
                if result[0]:
                    return json.loads(result[0])
            
            return {}

    @staticmethod
    async def update_item_metadata(inv_id: int, new_metadata: dict) -> None:
        """Update metadata of specific item by inventory id"""
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE inventory SET item_metadata = ? WHERE (inv_id) = ?", (json.dumps(new_metadata), inv_id))
            await db.commit()

    @staticmethod
    async def get_inventory(user_id: int) -> List[Item]:
        """Get List of all Items of an Inventory"""
        items = []
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM inventory WHERE user_id = ?", (user_id,))
            result = await cursor.fetchall()
            
            if not result:
                print("User doesnt have items")
                return []
            
            for item_values in result:
                item = await ItemManager.get_item(item_values[2])
                item.inv_id = item_values[0]
                item.acquired_at = datetime.strptime(item_values[-1], "%Y-%m-%d %H:%M:%S").timestamp()
                item.metadata = json.loads(item_values[-2]) if item_values[-2] else {}

                items.append(item)

        return items


    @staticmethod
    async def get_inventory_value():
        pass