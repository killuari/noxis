import aiosqlite
import datetime

import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from managers.economy import EconomyManager
from managers.inventory import InventoryManager
from managers.knowledge import KnowledgeManager
from managers.level import LevelManager
from managers.user import UserManager
from views import LeaderboardView


class ProfileCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Show your or someones profile")
    async def profile(self, interaction: discord.Interaction, player: discord.User=None):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        
        
        user = interaction.user
         
        if player is not None:
            user = player
            
        if not await UserManager.user_exists(user.id):
            await interaction.response.send_message(f"{user} doesn't have an account. Try again.", ephemeral=True, delete_after=8.0)
            return

        level, experience = await LevelManager.get_lvl_exp(user.id)
        inv = await InventoryManager.get_inventory(user.id)
        total = sum([item.quantity for item in inv])
        inv_value = await InventoryManager.get_inventory_value(user.id)
        balance, bank_balance = await EconomyManager.get_balance(user.id)
        total_balance = await EconomyManager.get_total_balance(user.id)
        req_exp = LevelManager.calculate_exp_for_level(level+1)

        url = "https://cdn.pixabay.com/photo/2022/10/09/17/21/discord-7509681_1280.png" if user.avatar == None else user.avatar.url.split("?")[0]

        embed = discord.Embed(title=user.name, color=discord.Color.from_str("#607bff")).set_thumbnail(url=url)
        
        rank, leaderboard, _ = await DatabaseManager.get_ranking(user.id, "users", "level")                  
        progess_curr = round(experience/req_exp, 1)
        progess_curr = round(progess_curr * 5) 
        green_bars = progess_curr * "🟩"
        progress_left = int(5 - progess_curr)
        black_bars = progress_left * "⬛"
        progress_bar = green_bars + black_bars
        embed.add_field(name="Level", value=f"Rank: `{rank}/{leaderboard}`\nLevel: `{level}`\nXP: `{experience}/{req_exp}`\n{progress_bar}", inline=True)
        
        rank, leaderboard, _ = await DatabaseManager.get_ranking(user.id, "users", "total_balance")                  
        embed.add_field(name="Balance", value=f"Rank: `{rank}/{leaderboard}`\n💵: `{balance:,}$`\n🏦: `{bank_balance:,}$`\nTotal: `{total_balance:,}$`", inline=True)
                       
        rank, leaderboard, _ = await DatabaseManager.get_ranking(user.id, "users", "inv_value")                  
        embed.add_field(name="Inventory", value=f"Rank: `{rank}/{leaderboard}`\nTotal items: `{total}`\nUnique items: `{len(inv)}`\nValue: `{inv_value:,}$`", inline=True)
                       
        knowledge = await KnowledgeManager.get_knowledge(user.id)
        science = knowledge["science"]
        stat_science = (await KnowledgeManager.get_knowledge_threshold(science)).capitalize()
        medicine = knowledge["medicine"]
        stat_medicine = (await KnowledgeManager.get_knowledge_threshold(medicine)).capitalize()
        economics = knowledge["economics"]
        stat_economics = (await KnowledgeManager.get_knowledge_threshold(economics)).capitalize()
        literature = knowledge["literature"]
        stat_literature = (await KnowledgeManager.get_knowledge_threshold(literature)).capitalize()
        rank, leaderboard, _ = await DatabaseManager.get_ranking(user.id, "users", "total_knowledge")  
        embed.add_field(name="Knowledge", value=f"""
                        Rank: `{rank}/{leaderboard}`
                        Science: `{stat_science}`
                        Medicine: `{stat_medicine}`
                        Economics: `{stat_economics}`
                        Literature: `{stat_literature}`""",
                        inline=True)
                              
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT cmd_used FROM users WHERE user_id=?", (user.id,))
            result = await cursor.fetchone()
            await cursor.execute("SELECT created_at FROM users WHERE user_id=?", (user.id,))
            created_at= (await cursor.fetchone())[0]
        
        timestamp = int((datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")).timestamp())
        embed.add_field(name="Info", value=f"Commands used: `{result[0]}`\nStarted playing: <t:{timestamp}:R>", inline=True)   
  
        await interaction.response.send_message(embed=embed)
        await DatabaseManager.update_cmd_used(interaction.user.id)
        
    @app_commands.command(name="tip", description="You get a random tip for the game")
    async def get_random_tip(self, interaction: discord.Interaction):
        tip = await KnowledgeManager.get_random_tip()
        await interaction.response.send_message(embed=discord.Embed(title=tip,
                                                                    color=discord.Color.from_str("#607bff")))

    async def send_leaderboard_embed(self, interaction, category_value, update=False, view=None):
        title = ""
        msg = ""
        _, _, leaderboard = await DatabaseManager.get_ranking(interaction.user.id, "users", category_value)

        if category_value == "total_balance":
            for idx, (user_id,) in enumerate(leaderboard, start=1):
                if idx <= 5:
                    user = await self.bot.fetch_user(user_id)
                    balance, bank_balance = await EconomyManager.get_balance(user_id)
                    total_balance = await EconomyManager.get_total_balance(user_id)
                    msg += f"`{idx}` **{user.name}** - **{total_balance:,}**$ | 💵 {balance:,}$ | 🏦 {bank_balance:,}$\n\n"
                
                if user_id == interaction.user.id:
                    author_rank = idx
                
            author_balance, author_bank_balance = await EconomyManager.get_balance(interaction.user.id)      
            author_total_balance = await EconomyManager.get_total_balance(interaction.user.id)
            msg += f"\n**Compare with your stats:**\n\n`{author_rank}` **{interaction.user.name}** - **{author_total_balance:,}**$ | 💵 {author_balance:,}$ | 🏦 {author_bank_balance:,}$\n\n"
                    
            title = "Leaderboard - Balance"
            
        elif category_value == "level":
            for idx, (user_id,) in enumerate(leaderboard, start=1):
                if idx <= 5:
                    user = await self.bot.fetch_user(user_id)
                    level, _ = await LevelManager.get_lvl_exp(user_id)
                    msg += f"`{idx}` **{user.name}** - 🏅 Level **{level}**\n\n"
                
                if user_id == interaction.user.id:
                    author_rank = idx
            
            author_level, _ = await LevelManager.get_lvl_exp(interaction.user.id)
            msg += f"\n**Compare with your stats:**\n\n`{author_rank}` **{interaction.user.name}** - 🏅 Level **{author_level}**\n\n"
            
            title = "Leaderboard - Level"
            
        elif category_value == "inv_value":
            for idx, (user_id,) in enumerate(leaderboard, start=1):
                if idx <= 5:
                    user = await self.bot.fetch_user(user_id)
                    inventory_value = await InventoryManager.get_inventory_value(user_id)
                    items = await InventoryManager.get_inventory(user_id)
                    count = sum(item.quantity for item in items)
                    unique_items = len(items)
                    msg += f"`{idx}` **{user.name}** - **{inventory_value:,}**$ | 🎒 {count} items ({unique_items} unique)\n\n"
                    
                if user_id == interaction.user.id:
                    author_rank = idx
                    
            author_inv_value = await InventoryManager.get_inventory_value(interaction.user.id)
            author_items = await InventoryManager.get_inventory(interaction.user.id)
            total = sum(item.quantity for item in author_items)
            author_unique_items = len(author_items)   
            msg += f"\n**Compare with your stats:**\n\n`{author_rank}` **{interaction.user.name}** - **{author_inv_value:,}**$ | 🎒 {total} items ({author_unique_items} unique)"
            
            title = "Leaderboard - Inventory Value"

        embed = discord.Embed(title=title, description=msg, color=discord.Color.from_str("#607bff"))
        embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v13.1/512px/1f4ca.png")

        if view is None:
            view = LeaderboardView(self, interaction.user.id, category_value)

        if update:
            await interaction.response.edit_message(embed=embed, view=view)
            view.message = interaction.message
            
        else:
            await interaction.response.send_message(embed=embed, view=view)
            
            try:
                msg = await interaction.original_response()
                view.message = msg
                
            except Exception:
                pass
            
    @app_commands.command(name="leaderboard", description="Shows leaderboard of top 5 users for selected category")
    async def leaderboard(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return

        await self.send_leaderboard_embed(interaction, "total_balance", view=LeaderboardView(self, interaction.user.id, "total_balance"))
        await DatabaseManager.update_cmd_used(interaction.user.id)
