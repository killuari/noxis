import os, json, discord

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
    def __init__(self, author_id: int, current_expedition_id: int = 0, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(ExpeditionDropdown(author_id=author_id, current_expedition_id=current_expedition_id))

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

        print("Successfully loaded all expedition!")
    
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
            await interaction.response.send_message(embed=embed, view=ExpeditionView(interaction.user.id))
        else:
            await interaction.response.edit_message(embed=embed, view=ExpeditionView(interaction.user.id, current_expedition_id=expedition_id))

    def start_expedition(self, user_id, expedition_id):
        # State initialisieren, erste Event-ID starten
        pass

    def handle_event_choice(self, user_id, choice_id):
        # Nächstes Event oder Outcome ausführen
        pass

