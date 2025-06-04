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

