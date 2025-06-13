import discord, aiosqlite, typing, time, random, datetime
from discord import app_commands
from discord.ext import commands
from user_manager import *
from buttons import *
from items import *
from inventory_manager import InventoryManager
from economy_manager import EconomyManager


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
                        max_bank_balance = await EconomyManager.get_max_bank_capacity(user_id)
                        await interaction.response.send_message(embed=discord.Embed(title=f"{interaction.user.name}'s balance", description=f"Global Ranking: {rank} out of {len(leaderboard)}\n\n💵: {balance:,}$\n\n🏦: {bank_balance:,}$ / {max_bank_balance:,}$", color=discord.Color.green()))
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
                        max_bank_balance = await EconomyManager.get_max_bank_capacity(user_id)
                        await interaction.response.send_message(embed=discord.Embed(title=f"{user.name}'s balance", description=f"Global Ranking: {rank} out of {len(leaderboard)}\n\n💵: {balance:,}$\n\n🏦: {bank_balance:,}$ / {max_bank_balance:,}$", color=discord.Color.green()))
                        return
                    else:
                        user_found = False
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
            await interaction.response.send_message(embed=discord.Embed(title=f"Successfully deposited {(amount-money_left):,}$" + (" (Max bank capacity reached)" if money_left > 0 else ""), description=f"💵: {balance:,}$\n\n🏦: {bank_balance:,}$ / {max_bank_balance:,}$", color=discord.Color.green()))

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
            await interaction.response.send_message(embed=discord.Embed(title=f"Successfully withdrawn {amount:,}$", description=f"💵: {balance:,}$\n\n🏦: {bank_balance:,}$ / {max_bank_balance:,}$", color=discord.Color.green()))

        except ValueError:
            await interaction.response.send_message(embed=discord.Embed(title="Invalid amount. Please enter a number or 'max'.", color=discord.Color.red()), ephemeral=True)
            return
        
    @app_commands.command(name="daily", description="Your daily reward")
    async def daily(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT daily FROM users WHERE user_id=?", (interaction.user.id,))
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
                await cursor.execute("UPDATE users SET daily=? WHERE user_id=?", (current_time, interaction.user.id))
                await db.commit()
                await EconomyManager.add_money(interaction.user.id, 1000)
                await interaction.response.send_message(embed=discord.Embed(title="You successfully claimed your daily Reward!", description="1,000$ have been added to your Wallet", color=discord.Color.green()))
            else:
                next_daily_time = last_daily + datetime.timedelta(days=1)
                timestamp = int(next_daily_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(title="You already claimed your daily.", description=f"Time left until available: <t:{timestamp}:R>", color=discord.Color.red()))

    @app_commands.command(name="weekly", description="Your weekly reward")
    async def weekly(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT weekly FROM users WHERE user_id=?", (interaction.user.id,))
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
                await cursor.execute("UPDATE users SET weekly=? WHERE user_id=?", (current_time, interaction.user.id))
                await db.commit()
                await EconomyManager.add_money(interaction.user.id, 15000)
                await interaction.response.send_message(embed=discord.Embed(title="You successfully claimed your weekly Reward!", description="15,000$ have been added to your Wallet", color=discord.Color.green()))
            else:
                next_daily_time = last_daily + datetime.timedelta(weeks=1)
                timestamp = int(next_daily_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(
                    title="You already claimed your weekly.", 
                    description=f"Time left until available: <t:{timestamp}:R>", 
                    color=discord.Color.red()))

    @app_commands.command(name="scavenge", description="Investigate your surroundings and try your luck finding coins or items.")
    async def scavenge(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT last_scavenge FROM users WHERE user_id=?", (interaction.user.id,))
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
                await cursor.execute("UPDATE users SET last_scavenge=? WHERE user_id=?", (current_time, interaction.user.id))
                await db.commit()

                reward_chance = random.random()
                found_msg = ""
                # 40% chance to get nothing
                if reward_chance <= 0.4:
                    found_msg = "😔 **Found nothing valuable this time**"
                # 25% chance to get some money
                elif reward_chance <= 0.65:
                    money = random.randint(100, 500)
                    found_msg = f"💰 **Found {money}$!**"
                    await EconomyManager.add_money(interaction.user.id, money)
                # 20% chance to get more money 
                elif reward_chance <= 0.85:
                    money = random.randint(500, 1500)
                    found_msg = f"💰 **Found {money}$!**"
                    await EconomyManager.add_money(interaction.user.id, money)
                # 10% chance to get money and a common item
                elif reward_chance <= 0.95:
                    money = random.randint(750, 2000)
                    found_msg = f"💰 **Found {money}$!**"
                    await EconomyManager.add_money(interaction.user.id, money)

                    item = random.choice(await ItemManager.get_items_by_rarity(Rarity.COMMON))
                    found_msg += f"\n🍎 ** Also found one {item.name}!**"
                    await InventoryManager.add_item(interaction.user.id, item.item_id)
                # 5% change to get rare item
                else:
                    item = random.choice(await ItemManager.get_items_by_rarity(Rarity.RARE))
                    found_msg = f"🍎 ** Found one {item.name}!**"
                    await InventoryManager.add_item(interaction.user.id, item.item_id)

                await interaction.response.send_message(embed=discord.Embed(
                    title="🔍 Scavenging Results", 
                    description=f"""
                    {random.choice(["🏚️ You search through an abandoned building...", 
                                "🌳 While exploring the forest floor...",
                                "🗑️ You dig through some dumpsters..."])}\n
                    {found_msg}""", 
                    color=discord.Color.green()))
            else:
                next_scavenge_time = last_scavenge + datetime.timedelta(seconds=35)
                timestamp = int(next_scavenge_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(
                    title="⏰ Scavenging Cooldown", 
                    description=f"🛑 You're still tired from your last search!\n⏰ Next scavenge: <t:{timestamp}:R>", 
                    color=discord.Color.red()
                    ).set_footer(text="💡 Try /work or /daily while you wait!"))