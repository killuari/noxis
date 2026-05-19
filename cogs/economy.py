import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from database_manager import DatabaseManager
from economy_manager import EconomyManager
from user_manager import UserManager


class EconomyCommands(commands.Cog):
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
                await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (interaction.user.id,))
                balance, bank_balance = await cursor.fetchone()                             
               
                rank, leaderboard, _ = await DatabaseManager.get_ranking(interaction.user.id, "users", "total_balance")
                max_bank_balance = await EconomyManager.get_max_bank_capacity(interaction.user.id)
               
                await interaction.response.send_message(embed=discord.Embed(title=f"{interaction.user.name}'s balance", description=f"Global Ranking: `{rank}/{leaderboard}`\n\n💵: `{balance:,}$`\n\n🏦: `{bank_balance:,}$ / {max_bank_balance:,}$`", color=discord.Color.from_str("#607bff")))
                return
                    
            # get balance of other user
            else:
                await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user.id,))
                result = await cursor.fetchone()  
               
                if result is None or result[0] is None:
                    user_found = False
               
                else:
                    balance, bank_balance = result                        
                    rank, leaderboard, _ = await DatabaseManager.get_ranking(user.id, "users", "total_balance")
                    max_bank_balance = await EconomyManager.get_max_bank_capacity(user.id)
               
                    await interaction.response.send_message(embed=discord.Embed(title=f"{user.name}'s balance", description=f"Global Ranking: `{rank}/{leaderboard}`\n\n💵: `{balance:,}$`\n\n🏦: `{bank_balance:,}$ / {max_bank_balance:,}$`", color=discord.Color.from_str("#607bff")))
                    await DatabaseManager.update_cmd_used(interaction.user.id)
               
                if not user_found:
                    await interaction.response.send_message(f"{user} doesn't have an account. Try again.", ephemeral=True, delete_after=8.0)

    @app_commands.command(name="deposit", description="Deposits given amount from wallet to bank")
    async def deposit(self, interaction: discord.Interaction, amount: str):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        if amount == "max":
            amount = (await EconomyManager.get_balance(interaction.user.id))[0]
        
        # if amount != "max" try to convert it to integer
        try:
            amount = int(amount)
            if amount <= 0:
                await interaction.response.send_message(embed=discord.Embed(title="Amount must be greater than 0.", color=discord.Color.red()), ephemeral=True)
                return
            
            balance = (await EconomyManager.get_balance(interaction.user.id))[0]
            if amount > balance:
                await interaction.response.send_message(embed=discord.Embed(title="You don't have enough money in wallet", color=discord.Color.red()), ephemeral=True)
                return

            money_left = await EconomyManager.add_money(interaction.user.id, amount, bank=True)

            if amount == money_left:
                await interaction.response.send_message(embed=discord.Embed(title="Your bank is already full!", color=discord.Color.red()), ephemeral=True)
                return
            
            await EconomyManager.remove_money(interaction.user.id, amount-money_left)

            balance, bank_balance = await EconomyManager.get_balance(interaction.user.id)
            max_bank_balance = await EconomyManager.get_max_bank_capacity(interaction.user.id)
            await interaction.response.send_message(embed=discord.Embed(title=f"Successfully deposited `{(amount-money_left):,}$`" + (" (Max bank capacity reached)" if money_left > 0 else ""), description=f"💵: `{balance:,}$`\n\n🏦: `{bank_balance:,}$ / {max_bank_balance:,}$`", color=discord.Color.green()))
            await DatabaseManager.update_cmd_used(interaction.user.id)

        except ValueError:
            await interaction.response.send_message(embed=discord.Embed(title="Invalid amount. Please enter a number or 'max'.", color=discord.Color.red()), ephemeral=True)
            return
        
    @app_commands.command(name="withdraw", description="Withdraws given amount from bank")
    async def withdraw(self, interaction: discord.Interaction, amount: str):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        if amount == "max":
            amount = (await EconomyManager.get_balance(interaction.user.id))[1]

        # if amount != "max" try to convert it to integer
        try:
            amount = int(amount)
            if amount <= 0:
                await interaction.response.send_message(embed=discord.Embed(title="Amount must be greater than 0.", color=discord.Color.red()), ephemeral=True)
                return
            
            bank_balance = (await EconomyManager.get_balance(interaction.user.id))[1]
            if amount > bank_balance:
                await interaction.response.send_message(embed=discord.Embed(title="You don't have enough money in bank!", color=discord.Color.red()), ephemeral=True)
                return

            await EconomyManager.add_money(interaction.user.id, amount)
            await EconomyManager.remove_money(interaction.user.id, amount, bank=True)

            balance, bank_balance = await EconomyManager.get_balance(interaction.user.id)
            max_bank_balance = await EconomyManager.get_max_bank_capacity(interaction.user.id)
            await interaction.response.send_message(embed=discord.Embed(title=f"Successfully withdrawn `{amount:,}$`", description=f"💵: `{balance:,}$`\n\n🏦: `{bank_balance:,}$ / {max_bank_balance:,}$`", color=discord.Color.green()))
            await DatabaseManager.update_cmd_used(interaction.user.id)

        except ValueError:
            await interaction.response.send_message(embed=discord.Embed(title="Invalid amount. Please enter a number or 'max'.", color=discord.Color.red()), ephemeral=True)
            return
