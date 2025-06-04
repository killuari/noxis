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
    id: int
    name: str
    description: str
    rarity: Rarity
    value: int = 0
    stackable: bool = True
    max_stack: int = 99
    usable: bool = False
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

# Alle verfügbaren Items - hier können neue Items einfach hinzugefügt werden
ITEMS = {
    1: Item(
        id=1,
        name="Eisenschwert",
        description="Ein solides Eisenschwert für Anfänger",
        rarity=Rarity.COMMON,
        value=100,
        stackable=False,
        max_stack=1,
        usable=False,
        metadata={"damage": 15, "durability": 100, "type": "sword"}
    )
}

class ItemManager:
    """Helper-Klasse für Item-Operationen"""
    
    @staticmethod
    def item_exists(item_id: int) -> bool:
        """Prüft ob Item existiert"""
        return item_id in ITEMS

    @staticmethod
    def get_item(item_id: int) -> Optional[Item]:
        """Holt Item-Definition aus dem ITEMS Dict"""
        if ItemManager.item_exists(item_id):
            return ITEMS.get(item_id)
    
    @staticmethod
    def get_items_by_rarity(rarity: Rarity) -> List[Item]:
        """Holt alle Items einer Kategorie"""
        return [item for item in ITEMS.values() if item.rarity == rarity]
    
    @staticmethod
    def get_all_items() -> List[Item]:
        """Holt alle verfügbaren Items"""
        return list(ITEMS.values())
