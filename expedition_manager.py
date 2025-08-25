import os, json, discord, random
from typing import List
from economy_manager import EconomyManager
from dataclasses import dataclass
from mini_games import *

@dataclass
class Expedition:
    expedition_id: int
    name: str
    description: str
    allowed_items: List[str]
    cost: int
    events: dict = None
    start_events: dict = None

    def get_event_callbacks(self, event_id: str) -> List:
        event = self.events[event_id]
        if event is None:
            return None
        
        callbacks = []
        for choice in event.choices:
            if random.random() <= choice["chance"]:
                outcome = random.choice(choice["success_outcomes"])
            else:
                outcome = random.choice(choice["fail_outcomes"])

            callbacks.append(self.create_event_callback(outcome))
        
        return callbacks
    
    def get_minigame_callbacks(self, event_id: str) -> Dict:
        event = self.events[event_id]
        if event is None:
            return None
        
        outcomes = (random.choice(event.outcomes["success_outcomes"]), random.choice(event.outcomes["fail_outcomes"]))
        callbacks = []
        for outcome in outcomes:
            callbacks.append(self.create_event_callback(outcome))

        return {"success_callback": callbacks[0], "fail_callback": callbacks[1]}

    def create_event_callback(self, event_id: str):
        event = self.events[event_id]
        if event is None:
            return None
        
        async def event_callback(interaction: discord.Interaction):
            embed, view = event.event_to_message(interaction=interaction)
            await interaction.response.edit_message(embed=embed, view=view)

        return event_callback
            
@dataclass
class ExpeditionEvent:
    expedition_id: int
    event_id: str
    type: str
    description: str
    title: str = ""
    outcomes: Dict = None
    choices: List[dict] = None
    rewards: List[dict] = None

    def event_to_message(self, interaction: discord.Interaction):
        if self.type != "minigame":
            embed = discord.Embed(title=self.description)
            view = EventView(event=self)
        else:
            embed = discord.Embed(title=self.title, description=self.description)
            view = EventView(event=self, interaction=interaction)
        return (embed, view)
            

class ExpeditionDropdown(discord.ui.Select):
    def __init__(self, author_id: int, current_expedition_id: int = 0, options = ...):
        self.author_id = author_id
        options = [
            discord.SelectOption(label=ExpeditionManager.expeditions[id]["name"], 
                                 value=id, 
                                 description=ExpeditionManager.expeditions[id]["description"], 
                                 default=id==current_expedition_id)
            for id in range(len(ExpeditionManager.expeditions.keys()))
        ]
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your expedition.", ephemeral=True)
            return
        
        await ExpeditionManager.send_expedition_embed(interaction=interaction, expedition_id=int(self.values[0]), update=True)

class ExpeditionView(discord.ui.View):
    def __init__(self, author_id: int, author_balance: int, current_expedition_id: int = 0, timeout = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.author_balance = author_balance
        self.selected_expedition_id = current_expedition_id
        self.selected_expedition = ExpeditionManager.get_expedition(self.selected_expedition_id)

        self.add_item(ExpeditionDropdown(author_id=author_id, current_expedition_id=current_expedition_id))

        start_button = discord.ui.Button(
            label=f"Start Expedition! Cost: {self.selected_expedition.cost}" if author_balance > self.selected_expedition.cost else f"Too Expensive! Cost: {self.selected_expedition.cost}",
            style=discord.ButtonStyle.green if author_balance > self.selected_expedition.cost else discord.ButtonStyle.red
        )
        start_button.callback = self.start_expedition_callback

        self.add_item(start_button)

    async def start_expedition_callback(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use this button!", ephemeral=True)
            return
        
        if (await EconomyManager.get_balance(self.author_id))[0] < self.selected_expedition.cost:
            await interaction.response.send_message(f"You dont have enough money on your wallet!", ephemeral=True)
            return
        
        await ExpeditionManager.start_expedition(interaction=interaction, expedition_id=self.selected_expedition_id)

class EventView(discord.ui.View):
    def __init__(self, event: ExpeditionEvent, interaction: discord.Interaction = None, timeout = 180):
        super().__init__(timeout=timeout)
        self.event = event
        self.expedition = ExpeditionManager.get_expedition(expedition_id=event.expedition_id)

        if event.type == "start" or event.type == "choice":
            button_callbacks = self.expedition.get_event_callbacks(event.event_id)

            for idx, choice in enumerate(event.choices):
                button = discord.ui.Button(label=choice["label"])
                button.callback = button_callbacks[idx]
                self.add_item(button)

        elif event.type == "minigame":
            button = discord.ui.Button(label="Start")
            button.callback = self.create_minigame_callback(minigame=event.event_id, interaction=interaction)
            self.add_item(button)

        elif event.type == "end":
            print("end")

    def create_minigame_callback(self, minigame: str, interaction: discord.Interaction):
        callbacks = self.expedition.get_minigame_callbacks(self.event.event_id)
        game = ExpeditionManager.games[minigame](user=interaction.user, callbacks=callbacks, expedition=True)

        async def callback(interaction: discord.Interaction):
            await game.start_game(interaction=interaction)

        return callback

class ExpeditionManager:
    expeditions = {}
    games = {
        "lockpick_minigame": LockpickGame
    }

    @classmethod
    async def load_all(cls, folder="expeditions"):
        cls.expeditions.clear()
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                path = os.path.join(folder, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    exp_id = data["id"]
                    cls.expeditions[exp_id] = data

                except json.JSONDecodeError as e:
                    print(f"[ERROR] Fehler in {filename}: {e}")
                except Exception as e:
                    print(f"[ERROR] Konnte {filename} nicht laden: {e}")

        print("Successfully loaded all expeditions!")
    
    @classmethod
    def get_expedition(cls, expedition_id: int) -> Expedition:
        expedition_dict = cls.expeditions.get(expedition_id)

        events = {}
        start_events = {}
        for event_dict in expedition_dict["events"]:
            event = ExpeditionEvent(
                expedition_id=expedition_dict["id"],
                event_id=event_dict["id"],
                type=event_dict["type"],
                description=event_dict["description"],
            )

            if event.type == "start":
                event.choices = event_dict["choices"]
                events[event.event_id] = event
                start_events[event.event_id] = event
            elif event.type == "choice":
                event.choices = event_dict["choices"]
                events[event.event_id] = event
            elif event.type == "minigame":
                event.title = event_dict["title"]
                event.outcomes = {"success_outcomes": event_dict["success_outcomes"], "fail_outcomes": event_dict["fail_outcomes"]}
                events[event.event_id] = event
            elif event.type == "end":
                event.rewards = event_dict["rewards"]
                events[event.event_id] = event

        expedition = Expedition(
            expedition_id=expedition_dict["id"],
            name=expedition_dict["name"],
            description=expedition_dict["description"],
            allowed_items=expedition_dict["allowed_items"],
            cost=expedition_dict["cost"],
            events=events,
            start_events=start_events
        )
        return expedition
    
    @staticmethod
    async def send_expedition_embed(interaction: discord.Interaction, expedition_id: int, update: bool = False):
        expedition = ExpeditionManager.get_expedition(expedition_id)
        if expedition is None:
            print("Expedition doesnt exist")
            return

        embed = discord.Embed(
            title="Choose an Expedition",
            color=discord.Color.from_str("#607bff"),
        ).add_field(name="Name", value=expedition.name, inline=False
        ).add_field(name="Description", value=expedition.description, inline=False
        ).add_field(name="Allowed Items", value=", ".join(expedition.allowed_items), inline=False)

        if not update:
            await interaction.response.send_message(embed=embed, view=ExpeditionView(author_id=interaction.user.id, 
                                                                                     author_balance=(await EconomyManager.get_balance(interaction.user.id))[0]))
        else:
            await interaction.response.edit_message(embed=embed, 
                                                    view=ExpeditionView(author_id=interaction.user.id, 
                                                                        author_balance=(await EconomyManager.get_balance(interaction.user.id))[0], 
                                                                        current_expedition_id=expedition_id))
    @staticmethod
    async def start_expedition(interaction: discord.Interaction, expedition_id: int):
        expedition = ExpeditionManager.get_expedition(expedition_id=expedition_id)
        start_event = random.choice(list(expedition.start_events.values()))
        embed, view = start_event.event_to_message(interaction=interaction)

        await interaction.response.edit_message(embed=embed, view=view)