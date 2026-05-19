from typing import Tuple

import discord

from managers.inventory import InventoryManager
from items import ItemManager


class SelectItems(discord.ui.View):
    def __init__(self, user_id: int, allowed_item_ids: Tuple[str], remove_items = True): 
        super().__init__(timeout=None)
        self.user_id = user_id
        self.remove_items = remove_items
        self.allowed_item_ids = allowed_item_ids
        self.button_mapping = {}

    async def add_buttons(self, callback: callable): # das callback kriegt als argument die interaction und die items_used
        for item_id in self.allowed_item_ids:
            item = await ItemManager.get_item(item_id)
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            button = discord.ui.Button(
                label=item.name,
                emoji=emoji_str,
                style=discord.ButtonStyle.secondary, 
                disabled=(await InventoryManager.get_item_quantity(user_id=self.user_id, item_id=item_id)) == 0
            )

            button.callback = self.create_callback(button)
            self.add_item(button)

            self.button_mapping[button.label] = item_id

        self.callback = callback

        self.items_used = {item_id: False for item_id in self.allowed_item_ids}

        self.start_button = discord.ui.Button(label="Start", style=discord.ButtonStyle.green)
        self.start_button.callback = self.create_start_callback()
        self.add_item(self.start_button)

    def create_callback(self, button):
        async def click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(embed=discord.Embed(title="You are not the player.", color=discord.Color.red()))
                return
            
            button.style = discord.ButtonStyle.blurple if button.style == discord.ButtonStyle.secondary else discord.ButtonStyle.secondary
            
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    if child.style == discord.ButtonStyle.blurple:
                        self.items_used[self.button_mapping[child.label]] = True

            await interaction.response.edit_message(view=self)
        return click
    
    def create_start_callback(self):
        async def start_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(embed=discord.Embed(title="You are not the player.", color=discord.Color.red()))
                return

            if self.remove_items:
                for item_id, used in self.items_used.items():
                    if used:
                        await InventoryManager.remove_item(interaction.user.id, item_id)

            await self.callback(interaction=interaction, items_used=self.items_used)

        return start_callback
