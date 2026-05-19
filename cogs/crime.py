import aiosqlite
import datetime
import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from database_manager import DatabaseManager
from economy_manager import EconomyManager
from inventory_manager import InventoryManager
from knowledge_manager import KnowledgeManager
from level_manager import LevelManager
from mini_games import LockpickGame
from user_manager import UserManager
from views import SelectItems


class CrimeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rob", description="Try your luck and rob someone.")
    async def rob(self, interaction: discord.Interaction, user: discord.User):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        if not await UserManager.user_exists(user.id) or not (await EconomyManager.get_balance(user.id))[0] >= 15000:
            await interaction.response.send_message(embed=discord.Embed(title="The user must at least have 15000$ in their wallet!", color=discord.Color.red()), ephemeral=True)
            return

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT rob FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_rob = result[0]
            claim_available = False
            current_time = datetime.datetime.now()
            
            if result is None or last_rob is None:
                claim_available = True
            else:
                last_rob = datetime.datetime.strptime(last_rob, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_rob + datetime.timedelta(minutes=5))
                
            if claim_available:
                last_used = current_time
                rob_chance = random.random()
                experience = 100
                robbed_percentage = random.randint(5, 15) * 0.01
                robbed_money = int((await EconomyManager.get_balance(user.id))[0] * robbed_percentage)

                # 60% chance to get nothing
                if rob_chance <= 0.6:
                    experience = 50

                    lost_money = int(robbed_money * 0.4)
                    # add 3 hours to last_used so that the cooldown is 3 hours
                    last_used = current_time + datetime.timedelta(hours=3)
                    money_left = await EconomyManager.remove_money(interaction.user.id, lost_money)

                    # if user doesnt have enough money in wallet, try to take it from bank
                    if money_left > 0: 
                        money_left = await EconomyManager.remove_money(interaction.user.id, money_left, bank=True)
                    # TODO: add functionality if user also doesnt have enough money in bank
                    
                    await interaction.response.send_message(embed=discord.Embed(
                    title="🚨 Robbery Failed!", 
                    description=f"""You got caught and now you have to pay a fine.\n\n
                                Penalty paid: `{lost_money:,}$`\n
                                You've been given a 3-hour suspension for robbery.\n""",
                    color=discord.Color.red()
                    ).set_footer(text="Better luck next time, but be careful!"))
                
                # 40% chance for success
                else:
                    await EconomyManager.remove_money(user.id, robbed_money)
                    await EconomyManager.add_money(interaction.user.id, robbed_money)
                    await interaction.response.send_message(embed=discord.Embed(
                    title="💰 Robbery Successful!", 
                    description=f"Stolen amount: `{robbed_money:,}$`",
                    color=discord.Color.green()
                    ).set_footer(text="Stay cautious — word might spread!"))
                
                await LevelManager.add_experience(interaction.user.id, experience, interaction)
                await cursor.execute("UPDATE last_used SET rob=? WHERE user_id=?", (last_used, interaction.user.id))
                await db.commit()
                await DatabaseManager.update_cmd_used(interaction.user.id)

            else:
                next_rob_time = last_rob + datetime.timedelta(minutes=5)
                timestamp = int(next_rob_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(
                    title="⏰ Robbery Cooldown", 
                    description=f"🛑 You're still tired from your last robbery!\n⏰ Next robbery: <t:{timestamp}:R>", 
                    color=discord.Color.red()
                    ).set_footer(text= await KnowledgeManager.get_random_tip()))

    @app_commands.command(name="bankrob", description="Try to bankrob someone")
    async def bankrob(self, interaction: discord.Interaction, target: discord.User):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        if target == interaction.user or target.bot: 
            await interaction.response.send_message("You must enter a valid target.", ephemeral=True, delete_after=8.0)
            return
        
        if await InventoryManager.get_item_quantity(interaction.user.id, "thief_mask") <= 0:
            embed=discord.Embed(title="Error",
                                description="You need the following item to use this command: `thief mask`",
                                color=discord.Color.red()).set_footer(text="Try the vaultbreaker expedition to get a thief mask! (/expedition)")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if (await EconomyManager.get_balance(target.id))[1] < 50000:
            embed=discord.Embed(title="Error",
                                description="Your target doesn't have enough money in their bank account",
                                color=discord.Color.red()).set_footer(text="Try someone else")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT bankrob FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_game = result[0]
            claim_available = False
            current_time = datetime.datetime.now()

            if result is None or last_game is None:
                claim_available = True
            else:
                last_game = datetime.datetime.strptime(last_game, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_game + datetime.timedelta(minutes=30))
            
            if not claim_available:
                next_available = last_game + datetime.timedelta(minutes=30)
                timestamp = int(next_available.timestamp())
                embed=discord.Embed(title="⏰ Bankrob Cooldown", description=f"🛑 Slow down! It's available <t:{timestamp}:R>", color=discord.Color.yellow()).set_footer(text= await KnowledgeManager.get_random_tip())
                await interaction.response.send_message(embed=embed)
                return
            
            await cursor.execute("UPDATE last_used SET bankrob=? WHERE user_id=?", (current_time, interaction.user.id))
            await db.commit()
        
        embed = discord.Embed(
            title="💰 Bank Robbery Attempt!",
            description=(
                f"**{interaction.user.mention}** is trying to rob **{target.mention}**'s bank account!\n\n"
                "To succeed, you must crack a **4-digit security code**.\n\n"
                "🔢 The code uses digits from **0–9** (e.g., `4821`). Each digit **appears only once**\n"
                f"⏳ You have **5 attempts** to guess it.\n"
                "🕵️ After each guess, you'll get feedback:\n"
                "-> 🟩 **Correct digit in the correct place**\n"
                "-> 🟨 **Correct digit in the wrong place**\n"
                "-> 🟥 **Not a correct digit**\n\n"
                "If you crack the code in time, you steal a share of the target's bank funds.\n"
                "If not... the police catches you and you must pay a fine!"
            ),
            color=discord.Color.from_str("#607bff")
        ).add_field(
            name="🛠️ Optional Items",
            value=(
                "- `Lockpick+`: +1 extra attempt\n"
                "- `Insider Tip`: Reveals one digit that's not part of the code\n"
            ),
            inline=False
        ).set_footer(text="Good luck... the vault is waiting!")
        
        lockpick_game = LockpickGame(user=interaction.user, target=target)
        item_selection = SelectItems(interaction.user.id, ("lockpick_plus", "insider_tip"))
        await item_selection.add_buttons(callback=lockpick_game.start_game)

        await interaction.response.send_message(embed=embed, view=item_selection)
        await DatabaseManager.update_cmd_used(interaction.user.id)
