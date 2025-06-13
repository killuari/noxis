from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

class Rarity(Enum):
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5

    def __lt__(self, obj):
        return self.value < obj.value

@dataclass
class Item:
    """Item-Definition als Python Dataclass"""
    item_id: int
    name: str
    description: str
    rarity: Rarity
    inv_id: int = 0
    value: int = 0
    max_stack: int = 99
    usable: bool = False
    metadata: Dict = None
    acquired_at: float = 0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

# Alle verfügbaren Items - hier können neue Items einfach hinzugefügt werden
# Hier sind ein paar items zum testen
ITEMS = {
    1: Item(
        item_id=1,
        name="Alkohol",
        description="Alkohol zum Trinken",
        rarity=Rarity.COMMON,
        value=100,
        max_stack=50,
        usable=True,
    ),
    2: Item(
        item_id=2,
        name="Apfel",
        description="Ein solides Essen für Anfänger",
        rarity=Rarity.UNCOMMON,
        value=5,
        max_stack=999,
        usable=True,
    ),
    3: Item(
        item_id=3,
        name="Eisenschwert",
        description="Ein solides Eisenschwert für Anfänger",
        rarity=Rarity.RARE,
        value=100,
        max_stack=1,
        usable=False,
        metadata={"damage": 15, "durability": 100}
    )
}

class ItemManager:
    """Helper-Klasse für Item-Operationen"""
    
    @staticmethod
    async def item_exists(item_id: int) -> bool:
        """Prüft ob Item existiert"""
        return item_id in ITEMS

    @staticmethod
    async def get_item(item_id: int) -> Item:
        """Holt Item-Definition aus dem ITEMS Dict"""
        if await ItemManager.item_exists(item_id):
            return ITEMS.get(item_id)
    
    @staticmethod
    async def get_items_by_rarity(rarity: Rarity) -> List[Item]:
        """Holt alle Items einer Kategorie"""
        return [item for item in ITEMS.values() if item.rarity == rarity]
    
    @staticmethod
    async def get_all_items() -> List[Item]:
        """Holt alle verfügbaren Items"""
        return list(ITEMS.values())
