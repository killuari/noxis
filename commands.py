import discord, aiosqlite, typing
from discord import app_commands
from discord.ext import commands
from user_manager import *
from buttons import *


# This function creates an account through button interaction
async def get_started(interaction: discord.Interaction, user_id: int):       
    await interaction.response.send_message(embed=discord.Embed(title="You don't have an account yet.",description="Click on **Get Started** to create one!", color=discord.Color.red()), view=GetStarted(), ephemeral=True)

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="balance", description="Shows your or someones balance and bank_balance")
    async def balance(self, interaction: discord.Interaction, user: discord.User=None):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return

        user_found = True
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            
            # get balance of user who used the command
            if user is None:
                await cursor.execute("SELECT user_id, balance, bank_balance FROM users ORDER BY total_balance DESC")
                leaderboard = await cursor.fetchall()                             
                if not leaderboard:
                    await interaction.response.send_message(embed=discord.Embed(title="No ranking found.", color=discord.Color.red()), ephemeral=True)
                    return
                for idx, (user_id, balance, bank_balance) in enumerate(leaderboard, start=1):
                    if user_id == interaction.user.id:
                        rank = idx 
                        await interaction.response.send_message(embed=discord.Embed(title=f"{interaction.user.name} balance", description=f"Global Ranking: {rank} out of {len(leaderboard)}\n\n💵: {balance}$\n\n🏦: {bank_balance}$", color=discord.Color.green()))
                        return
                    
            # get balance of other user
            else:
                await cursor.execute("SELECT user_id, balance, bank_balance FROM users ORDER BY total_balance DESC")
                leaderboard = await cursor.fetchall()                             
                if not leaderboard:
                    await interaction.response.send_message(embed=discord.Embed(title="No ranking found.", color=discord.Color.red()), ephemeral=True)
                    return
                for idx, (user_id, balance, bank_balance) in enumerate(leaderboard, start=1):
                    if user_id == user.id:                
                        rank = idx 
                        await interaction.response.send_message(embed=discord.Embed(title=f"{user.name} balance", description=f"Global Ranking: {rank} out of {len(leaderboard)}\n\n💵: {balance}$\n\n🏦: {bank_balance}$", color=discord.Color.green()))
                        return
                    else:
                        user_found = False
                if not user_found:
                    await interaction.response.send_message(f"{user} doesn't have an account. Try again.", ephemeral=True, delete_after=8.0)

    @app_commands.command(name="deposit", description="Deposits given amount to bank")
    async def deposit(self, interaction: discord.Interaction, amount: typing.Union[int, str]):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        if amount == "max":
            pass
        else:
            pass