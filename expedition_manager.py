import os, json, discord
from economy_manager import EconomyManager

class ExpeditionDropdown(discord.ui.Select):
    def __init__(self, author_id: int, current_expedition_id: int = 0, options = ...):
        self.author_id = author_id
        options = [
            discord.SelectOption(label=ExpeditionManager.get_expedition(id)["name"], 
                                 value=id, 
                                 description=ExpeditionManager.get_expedition(id)["description"], 
                                 default=ExpeditionManager.get_expedition(id)["id"]==current_expedition_id)
            for id in range(len(ExpeditionManager.expeditions.keys()))
        ]
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your expedition.", ephemeral=True)
            return
        
        print(self.values)
        await ExpeditionManager.send_expedition_embed(interaction=interaction, expedition_id=int(self.values[0]), update=True)

class ExpeditionView(discord.ui.View):
    def __init__(self, author_id: int, author_balance: int, current_expedition_id: int = 0, timeout = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.author_balance = author_balance
        self.selected_expedition = ExpeditionManager.get_expedition(current_expedition_id)

        self.add_item(ExpeditionDropdown(author_id=author_id, current_expedition_id=current_expedition_id))

        start_button = discord.ui.Button(
            label=f"Start Expedition! Cost: {self.selected_expedition["cost"]}" if author_balance > self.selected_expedition["cost"] else f"Too Expensive! Cost: {self.selected_expedition["cost"]}",
            style=discord.ButtonStyle.green if author_balance > self.selected_expedition["cost"] else discord.ButtonStyle.red
        )
        start_button.callback = self.start_expedition_callback

        self.add_item(start_button)

    async def start_expedition_callback(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use this button!", ephemeral=True)
            return
        
        if (await EconomyManager.get_balance(self.author_id))[0] < self.selected_expedition["cost"]:
            await interaction.response.send_message(f"You dont have enough money on your wallet!", ephemeral=True)
            return
        
        print("expedition starts here")

class ExpeditionManager:
    expeditions = {}

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
    def get_expedition(cls, expedition_id: int):
        return cls.expeditions.get(expedition_id)
    
    @staticmethod
    async def send_expedition_embed(interaction: discord.Interaction, expedition_id: int, update: bool = False):
        expedition = ExpeditionManager.get_expedition(expedition_id)
        if expedition is None:
            print("Expedition doesnt exist")
            return

        embed = discord.Embed(
            title="Choose an Expedition",
            color=discord.Color.from_str("#607bff"),
        ).add_field(name="Name", value=expedition["name"], inline=False
        ).add_field(name="Description", value=expedition["description"], inline=False
        ).add_field(name="Allowed Items", value=", ".join(expedition["allowed_items"]), inline=False)

        if not update:
            await interaction.response.send_message(embed=embed, view=ExpeditionView(author_id=interaction.user.id, 
                                                                                     author_balance=(await EconomyManager.get_balance(interaction.user.id))[0]))
        else:
            await interaction.response.edit_message(embed=embed, 
                                                    view=ExpeditionView(author_id=interaction.user.id, 
                                                                        author_balance=(await EconomyManager.get_balance(interaction.user.id))[0], 
                                                                        current_expedition_id=expedition_id))

    def start_expedition(self, user_id, expedition_id):
        # State initialisieren, erste Event-ID starten
        pass

    def handle_event_choice(self, user_id, choice_id):
        # Nächstes Event oder Outcome ausführen
        pass

