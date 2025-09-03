import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class Rarity(Enum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5

    def __lt__(self, obj):
        return self.value < obj.value
    
    def __str__(self):
        return self.name.capitalize()

@dataclass
class Item:
    """Item-Definition als Python Dataclass"""
    item_id: int
    name: str
    description: str
    rarity: Rarity
    value: int = 0
    quantity: int = 0
    usable: bool = False
    sellable: bool = True
    unique: bool = False
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ItemManager:
    """Helper-Klasse für Item-Operationen"""
    items: Dict[str, Dict] = {}

    @classmethod
    async def load_all(cls):
        path = "items.json"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item_data in data:
                item_id = str(item_data["item_id"])
                cls.items[item_id] = item_data

        except json.JSONDecodeError as e:
            print(f"[ERROR] Fehler in {path}: {e}")  
        except Exception as e:
            print(f"[ERROR] Konnte {path} nicht laden: {e}")
            
        print("Successfully loaded all items!")

    @staticmethod
    async def item_exists(item_id: str) -> bool:
        """Prüft ob Item existiert"""
        return item_id in ItemManager.items

    @staticmethod
    async def get_item(item_id: str) -> Optional[Item]:
        """Holt Item-Definition aus dem items Dict und wandelt es in ein Item-Objekt um"""
        item_dict = ItemManager.items.get(item_id)
        if item_dict:
            return Item(
                item_id=item_dict["item_id"],
                name=item_dict["name"],
                description=item_dict["description"],
                rarity=Rarity[item_dict["rarity"].upper()],
                value=item_dict.get("value", 0),
                quantity=item_dict.get("quantity", 0),
                usable=item_dict.get("usable", False),
                metadata=item_dict.get("metadata", {}),
            )
        return None
    
    @staticmethod
    async def get_item_by_name(name: str) -> Optional[Item]:
        """Holt das komplette Item-Objekt anhand des Namens"""
        for item in ITEMS.values():
            if item.name.lower() == name.lower():
                return item
        return None
    
    @staticmethod
    async def get_items_by_rarity(rarity: Rarity) -> List[Item]:
        """Holt alle Items einer Kategorie"""
        return [item for item in ITEMS.values() if item.rarity == rarity]
    
    @staticmethod
    async def get_all_items() -> List[Item]:
        """Holt alle verfügbaren Items"""
        return list(ITEMS.values())
