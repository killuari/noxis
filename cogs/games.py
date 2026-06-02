import aiosqlite
import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from managers.knowledge import KnowledgeManager
from managers.user import UserManager
from views import HigherLower


class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="higherlower", description="Play higher or lower")
    async def highlower(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT higherlower FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_game = result[0]
            claim_available = False
            current_time = datetime.datetime.now()

            if result is None or last_game is None:
                claim_available = True
            else:
                last_game = datetime.datetime.strptime(last_game, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_game + datetime.timedelta(seconds=25))
            
            if not claim_available:
                next_available = last_game + datetime.timedelta(seconds=25)
                timestamp = int(next_available.timestamp())
                embed=discord.Embed(title="WOOOOOOW", description=f"🛑 Slow down! It's available <t:{timestamp}:R>", color=discord.Color.yellow()).set_footer(text= await KnowledgeManager.get_random_tip())
                await interaction.response.send_message(embed=embed)
                return
            
            await cursor.execute("UPDATE last_used SET higherlower=? WHERE user_id=?", (current_time, interaction.user.id))
            await db.commit()

        secret_num = random.randint(1,1000)
        comparison_num = random.randint(1, 1000)
    
        embed = discord.Embed(title="Higher or Lower",
                        color=discord.Color.dark_teal())
        
        embed.add_field(name="Game instruction:",
                        value="""You are given a comparison number.
                        Your task is to decide whether the secret number is **higher** or **lower** than the comparison number.
                        The secret number is randomly chosen between 1 to 1000.""",
                        inline=False)
        
        embed.add_field(name="**Secret number**",
                        value=f"`   `",
                        inline=True)

        embed.add_field(name="**Comparison number**:",
                        value=f"`{comparison_num}`",
                        inline=True)      

        view = HigherLower(secret_num, comparison_num, interaction.user.id, interaction)

        await interaction.response.send_message(embed=embed, view=view)
        await DatabaseManager.update_cmd_used(interaction.user.id)
