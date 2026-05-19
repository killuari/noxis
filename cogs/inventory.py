import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from managers.economy import EconomyManager
from managers.inventory import InventoryManager
from items import ItemManager
from managers.level import LevelManager
from managers.user import UserManager
from views import Inventory


class InventoryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def autocomplete_sellable_items_in_inventory(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not await UserManager.user_exists(interaction.user.id):
            return []
        
        # wir müssens btw mit autocomplete statt richtigen choices hier machen
        # weil wir ja live wissen müssen was der jeweilige user im inv hat
        # also kann mans nicht vordefinieren, auch nicht mit nem Literal oder so
        # dank memer hats hier in dem fall auch mit autocomplete gelöst

        suggestions = [ # diesmal die comprehension auf mehrere zeilen aufgeteilt
            app_commands.Choice(name=item.name, value=item.name) 
            for item in await InventoryManager.get_inventory(interaction.user.id)
            if current.lower() in item.name.lower() and item.sellable
        ]

        # Discord erlaubt max. 25 Vorschläge
        return suggestions[:25]

    @app_commands.command(name="sell", description="Sell items from your inventory")
    @app_commands.autocomplete(item=autocomplete_sellable_items_in_inventory)
    async def sell(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        item = await ItemManager.get_item_by_name(item)
        if not item:
            await interaction.response.send_message(embed=discord.Embed(title="This Item doesn't exist!", color=discord.Color.red()), ephemeral=True)
            return
        
        if not item.sellable:
            await interaction.response.send_message(embed=discord.Embed(title="You can't sell this item!", color=discord.Color.red()), ephemeral=True)
            return

        user_item_quantity = await InventoryManager.get_item_quantity(interaction.user.id, item.item_id)
        if user_item_quantity == 0:
            await interaction.response.send_message(embed=discord.Embed(title="You don't have this item!", color=discord.Color.red()), ephemeral=True)
            return
        elif user_item_quantity < quantity:
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            await interaction.response.send_message(embed=discord.Embed(title=f"You don't have enough {emoji_str} {item.name}!", color=discord.Color.red()), ephemeral=True)
            return
        
        percentage_range = (0.7, 1)
        sell_value = random.randint(int(percentage_range[0]*item.value), int(percentage_range[1]*item.value))

        await EconomyManager.add_money(interaction.user.id, sell_value * quantity)
        await InventoryManager.remove_item(interaction.user.id, item.item_id, quantity=quantity)

        emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
        await interaction.response.send_message(embed=discord.Embed(title="💸 Item sold!", description=f"Sold {quantity:,}x {emoji_str} {item.name} for: `{sell_value*quantity:,}$`", color=discord.Color.gold()))
        await DatabaseManager.update_cmd_used(interaction.user.id)

    @app_commands.command(name="inventory", description="Displays your or someones inventory")
    async def inventory(self, interaction: discord.Interaction, user: discord.User = None): 
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return  
        
        user = interaction.user if user is None else user 
    
        if not await UserManager.user_exists(user.id):
            await interaction.response.send_message(f"{user} doesn't have an account. Try again.", ephemeral=True, delete_after=8.0)
            return
    
        inventory = await InventoryManager.get_inventory_sorted_by_rarity(user.id)
        
        if inventory == []:
            embed = discord.Embed(title="It's pretty empty around here...", 
                                  description=f"{user.name} doesn't have any items yet. I think a few of my commands would come in handy 😉", 
                                  color=discord.Color.red())
            embed.set_footer(text="Try /higherlower or /scavenge")
            await interaction.response.send_message(embed=embed)
            return 

        pages_req = len(inventory) > 9

        url = "https://cdn.pixabay.com/photo/2022/10/09/17/21/discord-7509681_1280.png" if user.avatar == None else user.avatar.url.split("?")[0]

        embed = discord.Embed(title=f"{user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=url)
        embed.set_footer(text=f"Page 1/{max(1, (len(inventory)+8)//9)} | Use /item <item> to get more detailed info on an item!")

        for idx, item in enumerate(inventory):
            if idx < 9:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                value = f"{item.value}$" if not item.unique else "Unique"
                embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                                value=f"""
                                    Rarity: `{item.rarity}`
                                    Value: `{value}`
                                """,
                                inline=True)

        view = Inventory(interaction, inventory, url, page=1) if pages_req else discord.utils.MISSING

        await interaction.response.send_message(embed=embed, view=view)
        await DatabaseManager.update_cmd_used(interaction.user.id)
        
    async def autocomplete_items(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        suggestions = [ 
            app_commands.Choice(name=item.name, value=item.name) 
            for item in (await ItemManager.get_all_items()) 
            if current.lower() in item.name.lower()
        ]

        # Discord erlaubt max. 25 Vorschläge
        return suggestions[:25]

    @app_commands.command(name="item", description="Shows all the info about an item")
    @app_commands.autocomplete(item=autocomplete_items)
    async def item(self, interaction: discord.Interaction, item: str):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
                    
        item = await ItemManager.get_item_by_name(item)
        if not item:
            await interaction.response.send_message(embed=discord.Embed(title="This Item doesn't exist!", color=discord.Color.red()), ephemeral=True)
            return
        
        item.quantity = await InventoryManager.get_item_quantity(interaction.user.id, item.item_id)
        
        emoji_map = {
            True: "✅",
            False: "❌"
        }
        emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"

        embed = discord.Embed(
            title=f"{emoji_str} {item.name}",
            description=f"{item.description}\n\n" \
                        f"You have a total of **{item.quantity}**",
            color=discord.Color.from_str("#607bff"))
        
        value = f"{item.value}$" if not item.unique else "Unique"
        embed.add_field(name="Value", value=f"`{value}`", inline=True)
        embed.add_field(name="Rarity", value=f"`{item.rarity}`", inline=True)
        embed.add_field(name="Usable", value=f"`{emoji_map[item.usable]}`", inline=False)
        embed.add_field(name="Buyable", value=f"`{emoji_map[item.buyable]}`", inline=True)
        embed.add_field(name="Sellable", value=f"`{emoji_map[item.sellable]}`", inline=True)
        
        await interaction.response.send_message(embed=embed)
        await DatabaseManager.update_cmd_used(interaction.user.id)

    async def autocomplete_usable_items_in_inventory(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not await UserManager.user_exists(interaction.user.id):
            return []

        suggestions = [ 
            app_commands.Choice(name=item.name, value=item.name) 
            for item in await InventoryManager.get_inventory(interaction.user.id)
            if current.lower() in item.name.lower() and item.usable
        ]

        # Discord erlaubt max. 25 Vorschläge
        return suggestions[:25]

    @app_commands.command(name="use", description="Use one of your items")
    @app_commands.autocomplete(item=autocomplete_usable_items_in_inventory)
    async def use(self, interaction: discord.Interaction, item: str):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        item = await ItemManager.get_item_by_name(item)
        if not item:
            await interaction.response.send_message(embed=discord.Embed(title="This Item doesn't exist!", color=discord.Color.red()), ephemeral=True)
            return
        
        if not item.usable:
            await interaction.response.send_message(embed=discord.Embed(title="You can't use this item!", color=discord.Color.red()), ephemeral=True)
            return

        user_item_quantity = await InventoryManager.get_item_quantity(interaction.user.id, item.item_id)
        if user_item_quantity == 0:
            await interaction.response.send_message(embed=discord.Embed(title="You don't have this item!", color=discord.Color.red()), ephemeral=True)
            return

        if item.item_id == "mystery_box":
            possible_rewards = item.metadata["possible_rewards"]

            items = [entry["item_id"] for entry in possible_rewards]
            weights = [int(entry.get("weight", 0)) for entry in possible_rewards]

            if not items:
                raise ValueError("possible_rewards is empty.")
            if not any(weights):
                raise ValueError("All weights are zero.")

            got_item_id = random.choices(items, weights=weights, k=1)[0]
            got_item = await ItemManager.get_item(got_item_id)
            await InventoryManager.add_item(interaction.user.id, got_item_id)

            emoji_str = f"<:{got_item.item_id}:{got_item.custom_emoji_id}>"
            embed = discord.Embed(
                title="Opened Mystery Box",
                description=f"You got `1x {emoji_str} {got_item.name}`!",
                color=discord.Color.from_str("#607bff")
            )

            await LevelManager.add_experience(user_id=interaction.user.id, amount=random.randrange(50, 100), interaction=interaction)

        else: # falls wir ein item usable = True machen aber es hier noch nicht implementiert haben
            embed = discord.Embed(
                title="This item currently does nothing",
                description="You still lost it haha",
                color=discord.Color.orange()
            )

        await InventoryManager.remove_item(interaction.user.id, item.item_id)
        await interaction.response.send_message(embed=embed)
        await DatabaseManager.update_cmd_used(interaction.user.id)
