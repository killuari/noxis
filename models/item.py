from dataclasses import dataclass
from enum import Enum
from typing import Dict


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
    custom_emoji_id: int = 0
    usable: bool = False
    sellable: bool = True
    unique: bool = False
    findable: bool = True
    buyable: bool = False
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
