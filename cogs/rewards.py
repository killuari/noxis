import aiosqlite
import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from managers.economy import EconomyManager
from managers.inventory import InventoryManager
from managers.items import ItemManager
from models.item import Rarity
from managers.knowledge import KnowledgeManager
from managers.level import LevelManager
from managers.user import UserManager


class RewardCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Your daily reward")
    async def daily(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT daily FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_daily = result[0]
            claim_available = False
            current_time = datetime.datetime.now()
            
            if result is None or result[0] is None:
                claim_available = True
            else:
                last_daily = datetime.datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_daily + datetime.timedelta(days=1))
                
            if claim_available:
                await cursor.execute("UPDATE last_used SET daily=? WHERE user_id=?", (current_time, interaction.user.id))
                await db.commit()
                await EconomyManager.add_money(interaction.user.id, 1000)
                await interaction.response.send_message(embed=discord.Embed(
                    title="You successfully claimed your daily Reward!", 
                    description="`1,000$` have been added to your Wallet", 
                    color=discord.Color.green()))
                await LevelManager.add_experience(interaction.user.id, 200, interaction)
                await DatabaseManager.update_cmd_used(interaction.user.id)
            else:
                next_daily_time = last_daily + datetime.timedelta(days=1)
                timestamp = int(next_daily_time.timestamp())
                embed=discord.Embed(title="You already claimed your daily.", description=f"Time left until available: <t:{timestamp}:R>", color=discord.Color.red()).set_footer(text= await KnowledgeManager.get_random_tip())
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="weekly", description="Your weekly reward")
    async def weekly(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT weekly FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_daily = result[0]

            claim_available = False
            current_time = datetime.datetime.now()

            if result is None or result[0] is None:
                claim_available = True
            else:
                last_daily = datetime.datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_daily + datetime.timedelta(weeks=1))
            
            if claim_available:
                await cursor.execute("UPDATE last_used SET weekly=? WHERE user_id=?", (current_time, interaction.user.id))
                await db.commit()
                await EconomyManager.add_money(interaction.user.id, 15000)
                await interaction.response.send_message(embed=discord.Embed(
                    title="You successfully claimed your weekly Reward!", 
                    description="`15,000$` have been added to your Wallet", 
                    color=discord.Color.green()))
                await LevelManager.add_experience(interaction.user.id, 1000, interaction)
                await DatabaseManager.update_cmd_used(interaction.user.id)
            else:
                next_daily_time = last_daily + datetime.timedelta(weeks=1)
                timestamp = int(next_daily_time.timestamp())
                embed=discord.Embed(
                    title="You already claimed your weekly.", 
                    description=f"Time left until available: <t:{timestamp}:R>", 
                    color=discord.Color.red()).set_footer(text= await KnowledgeManager.get_random_tip())
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scavenge", description="Investigate your surroundings and try your luck finding coins or items.")
    async def scavenge(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT scavenge FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_scavenge = result[0]
            claim_available = False
            current_time = datetime.datetime.now()
            
            if result is None or last_scavenge is None:
                claim_available = True
            else:
                last_scavenge = datetime.datetime.strptime(last_scavenge, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_scavenge + datetime.timedelta(seconds=35))
                
            if claim_available:
                await cursor.execute("UPDATE last_used SET scavenge=? WHERE user_id=?", (current_time, interaction.user.id))
                await db.commit()

                reward_chance = random.random()
                found_msg = ""
                experience = 0
                # 40% chance to get nothing
                if reward_chance <= 0.4:
                    found_msg = "😔 **Found nothing valuable this time**"
                    experience = 10

                # 30% chance to get some money
                elif reward_chance <= 0.7:
                    money = random.randint(200, 500)
                    found_msg = f"💰 **Found** `{money}$`**!**"
                    await EconomyManager.add_money(interaction.user.id, money)
                    experience = 15

                # 15% chance to get more money 
                elif reward_chance <= 0.85:
                    money = random.randint(750, 1500)
                    found_msg = f"💰 **Found** `{money}$`**!**"
                    await EconomyManager.add_money(interaction.user.id, money)
                    experience = 25

                # 10% chance to get money and a common item
                elif reward_chance <= 0.95:
                    money = random.randint(1500, 2500)
                    found_msg = f"💰 **Found** `{money}$`**!**"
                    await EconomyManager.add_money(interaction.user.id, money)

                    item = random.choice(await ItemManager.get_findable_items_by_rarity(Rarity.COMMON))
                    quantity = random.randint(1,3)
                    emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                    found_msg += f"\n**Also found** {quantity}x {emoji_str} {item.name}**!**"
                    await InventoryManager.add_item(interaction.user.id, item.item_id, quantity)
                    experience = 50

                # 5% change to get rare item
                else:
                    money = random.randint(2000, 3000)
                    found_msg = f"💰 **Found** `{money}$`**!**"
                    await EconomyManager.add_money(interaction.user.id, money)
                    item = random.choice(await ItemManager.get_findable_items_by_rarity(Rarity.RARE))
                    emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                    found_msg += f"\n🍎 ** Also found** 1x {emoji_str} {item.name}**!**"
                    await InventoryManager.add_item(interaction.user.id, item.item_id)
                    experience = 100

                await interaction.response.send_message(embed=discord.Embed(
                    title="🔍 Scavenging Results", 
                    description=f"""
                    {random.choice(["🏚️ You search through an abandoned building...", 
                                "🌳 While exploring the forest floor...",
                                "🗑️ You dig through some dumpsters..."])}\n
                    {found_msg}""", 
                    color=discord.Color.green()))
                
                await LevelManager.add_experience(interaction.user.id, experience, interaction)
                await DatabaseManager.update_cmd_used(interaction.user.id)
                
            else:
                next_scavenge_time = last_scavenge + datetime.timedelta(seconds=35)
                timestamp = int(next_scavenge_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(
                    title="⏰ Scavenging Cooldown", 
                    description=f"🛑 You're still tired from your last search!\n⏰ Next scavenge: <t:{timestamp}:R>", 
                    color=discord.Color.red()
                    ).set_footer(text= await KnowledgeManager.get_random_tip()))
