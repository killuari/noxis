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
    value: int = 0
    max_stack: int = 99
    quantity: int = 0
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
        name="Bread",
        description="A fresh piece of bread for sustenance",
        rarity=Rarity.COMMON,
        value=3,
        max_stack=50,
        usable=True,
        metadata={
            "nutrition": 20,      # satiety value
        }
    ),
    2: Item(
        item_id=2,
        name="Water Bottle",
        description="A bottle of drinking water",
        rarity=Rarity.COMMON,
        value=5,
        max_stack=20,
        usable=True,
    ),
    3: Item(
        item_id=3,
        name="Rope",
        description="Sturdy rope useful for climbing or securing",
        rarity=Rarity.UNCOMMON,
        value=15,
        max_stack=40,
        usable=False,
    ),
    4: Item(
        item_id=4,
        name="Iron Sword",
        description="A solid iron sword",
        rarity=Rarity.UNCOMMON,
        value=75,
        max_stack=5,
        usable=False,
        metadata={
            "damage": 12,
        }
    ),
    5: Item(
        item_id=5,
        name="Wooden Shield",
        description="A sturdy wooden shield for protection",
        rarity=Rarity.UNCOMMON,
        value=60,
        max_stack=5,
        usable=False,
    ),
    6: Item(
        item_id=6,
        name="Hammer",
        description="A basic hammer, also useful for building",
        rarity=Rarity.RARE,
        value=50,
        max_stack=5,
        usable=False,
    ),
    7: Item(
        item_id=7,
        name="Nails Pack",
        description="A bundle of nails for building and repairs",
        rarity=Rarity.COMMON,
        value=5,
        max_stack=100,
        usable=False,
    ),
    8: Item(
        item_id=8,
        name="Tent",
        description="A simple tent for overnight stays outdoors",
        rarity=Rarity.RARE,
        value=200,
        max_stack=5,
        usable=True,
    ),
    9: Item(
        item_id=9,
        name="Blanket",
        description="Keeps you warm during cold nights",
        rarity=Rarity.COMMON,
        value=20,
        max_stack=5,
        usable=False,
    ),
    10: Item(
        item_id=10,
        name="Cooking Pot",
        description="Pot for cooking over an open fire",
        rarity=Rarity.UNCOMMON,
        value=45,
        max_stack=1,
        usable=False,
    ),
    11: Item(
        item_id=11,
        name="Food Rations",
        description="Prepackaged rations for traveling",
        rarity=Rarity.UNCOMMON,
        value=25,
        max_stack=20,
        usable=True,
    ),
    12: Item(
        item_id=12,
        name="Flint and Steel",
        description="Used to start a fire",
        rarity=Rarity.UNCOMMON,
        value=30,
        max_stack=10,
        usable=True,
    ),
    13: Item(
        item_id=13,
        name="Backpack",
        description="qdh",
        rarity=Rarity.RARE,
        value=150,
        max_stack=10,
        usable=False,
    ),
    14: Item(
        item_id=14,
        name="Map",
        description="Map of the surrounding area",
        rarity=Rarity.COMMON,
        value=10,
        max_stack=10,
        usable=False,
    ),
    15: Item(
        item_id=15,
        name="Compass",
        description="Shows cardinal directions",
        rarity=Rarity.UNCOMMON,
        value=40,
        max_stack=15,
        usable=False,
    ),
    16: Item(
        item_id=16,
        name="Lantern",
        description="Oil lantern for dark areas",
        rarity=Rarity.UNCOMMON,
        value=50,
        max_stack=20,
        usable=True,
    ),
    17: Item(
        item_id=17,
        name="Bow",
        description="A simple bow for ranged combat",
        rarity=Rarity.UNCOMMON,
        value=80,
        max_stack=5,
        usable=False,
    ),
    18: Item(
        item_id=18,
        name="Arrows",
        description="Standard arrows for the bow",
        rarity=Rarity.COMMON,
        value=3,
        max_stack=100,
        usable=False,
    ),
    19: Item(
        item_id=19,
        name="Torch",
        description="A torch that provides light for a while",
        rarity=Rarity.COMMON,
        value=10,
        max_stack=20,
        usable=True,
    ),
    20: Item(
        item_id=20,
        name="Mystery Box",
        description="Contains a random reward (mostly practical items)",
        rarity=Rarity.EPIC,
        value=200,
        max_stack=5,
        usable=True,
        metadata={
            # possible rewards are kept realistic items
            "possible_rewards": ["Bread", "Water Bottle", "Nails Pack", "Flint and Steel", "Arrows"],
        }
    ),
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
