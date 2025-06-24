import discord, aiosqlite, typing, time, random, datetime, aiofiles
from discord import app_commands
from discord.ext import commands
from user_manager import *
from buttons import *
from items import *
from inventory_manager import InventoryManager
from economy_manager import EconomyManager
from level_manager import LevelManager
from knowledge_manager import KnowledgeManager


# This function creates an account through button interaction
async def get_started(interaction: discord.Interaction, user_id: int):       
    await interaction.response.send_message(embed=discord.Embed(title="Wait something's wrong... Noxis is thinking...\n", description="Seems like you have never used a Noxis-Command before.\nIf you want to start playing click on **Get Started**.", color=discord.Color.red()), view=GetStarted(), ephemeral=True)

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
                await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (interaction.user.id,))
                balance, bank_balance = await cursor.fetchone()                             
               
                rank, leaderboard = await DatabaseManager.get_ranking(interaction.user.id, "users", "total_balance")
                max_bank_balance = await EconomyManager.get_max_bank_capacity(interaction.user.id)
               
                await interaction.response.send_message(embed=discord.Embed(title=f"{interaction.user.name}'s balance", description=f"Global Ranking: `{rank}/{leaderboard}`\n\n💵: `{balance:,}$`\n\n🏦: `{bank_balance:,}$ / {max_bank_balance:,}$`", color=discord.Color.green()))
                return
                    
            # get balance of other user
            else:
                await cursor.execute("SELECT balance, bank_balance FROM users WHERE user_id=?", (user.id,))
                result = await cursor.fetchone()  
               
                if result is None or result[0] is None:
                    user_found = False
               
                else:
                    balance, bank_balance = result                        
                    rank, leaderboard = await DatabaseManager.get_ranking(user.id, "users", "total_balance")
                    max_bank_balance = await EconomyManager.get_max_bank_capacity(user.id)
               
                    await interaction.response.send_message(embed=discord.Embed(title=f"{user.name}'s balance", description=f"Global Ranking: `{rank}/{leaderboard}`\n\n💵: `{balance:,}$`\n\n🏦: `{bank_balance:,}$ / {max_bank_balance:,}$`", color=discord.Color.green()))
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

    async def autocomplete_items_in_inventory(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        if not await UserManager.user_exists(interaction.user.id):
            return []
        
        # wir müssens btw mit autocomplete statt richtigen choices hier machen
        # weil wir ja live wissen müssen was der jeweilige user im inv hat
        # also kann mans nicht vordefinieren, auch nicht mit nem Literal oder so
        # dank memer hats hier in dem fall auch mit autocomplete gelöst

        suggestions = [ # diesmal die comprehension auf mehrere zeilen aufgeteilt
            app_commands.Choice(name=item.name, value=item.name) 
            for item in await InventoryManager.get_inventory(interaction.user.id) 
            if current.lower() in item.name.lower()
        ]

        # Discord erlaubt max. 25 Vorschläge
        return suggestions[:25]

    @app_commands.command(name="sell", description="Sell items from your inventory")
    @app_commands.autocomplete(item=autocomplete_items_in_inventory)
    async def sell(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        item = await ItemManager.get_item_by_name(item)
        if not item:
            await interaction.response.send_message(embed=discord.Embed(title="This Item doesn't exist!", color=discord.Color.red()), ephemeral=True)
            return
        
        user_item_quantity = await InventoryManager.get_item_quantity(interaction.user.id, item.item_id)
        if user_item_quantity == 0:
            await interaction.response.send_message(embed=discord.Embed(title="You don't have this item!", color=discord.Color.red()), ephemeral=True)
            return
        elif user_item_quantity < quantity:
            await interaction.response.send_message(embed=discord.Embed(title=f"You don't have enough `{item.name}!`", color=discord.Color.red()), ephemeral=True)
            return
        
        percentage_range = (0.8, 2)
        sell_value = random.randint(int(percentage_range[0]*item.value), int(percentage_range[1]*item.value))

        await EconomyManager.add_money(interaction.user.id, sell_value * quantity)
        await InventoryManager.remove_item(interaction.user.id, item.item_id, quantity=quantity)
        await interaction.response.send_message(embed=discord.Embed(title="💸 Item sold!", description=f"Sold `{quantity:,} {item.name} for: {sell_value*quantity:,}$`", color=discord.Color.gold()))
        await DatabaseManager.update_cmd_used(interaction.user.id)

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
                await LevelManager.add_experience(interaction.user.id, 200, interaction.followup.url)
                await DatabaseManager.update_cmd_used(interaction.user.id)
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
                await LevelManager.add_experience(interaction.user.id, 1000, interaction.followup.url)
                await DatabaseManager.update_cmd_used(interaction.user.id)
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

                    item = random.choice(await ItemManager.get_items_by_rarity(Rarity.COMMON))
                    quantity = random.randint(1,3)
                    found_msg += f"\n🍎 ** Also found** `{quantity} {item.name}`**!**"
                    await InventoryManager.add_item(interaction.user.id, item.item_id, quantity)
                    experience = 50

                # 5% change to get rare item
                else:
                    money = random.randint(2000, 3000)
                    found_msg = f"💰 **Found** `{money}$`**!**"
                    await EconomyManager.add_money(interaction.user.id, money)
                    item = random.choice(await ItemManager.get_items_by_rarity(Rarity.RARE))
                    found_msg += f"\n🍎 ** Also found** `one {item.name}`**!**"
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
                
                await LevelManager.add_experience(interaction.user.id, experience, interaction.followup.url)
                await DatabaseManager.update_cmd_used(interaction.user.id)
                
            else:
                next_scavenge_time = last_scavenge + datetime.timedelta(seconds=35)
                timestamp = int(next_scavenge_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(
                    title="⏰ Scavenging Cooldown", 
                    description=f"🛑 You're still tired from your last search!\n⏰ Next scavenge: <t:{timestamp}:R>", 
                    color=discord.Color.red()
                    ).set_footer(text="💡 Try /work or /daily while you wait!"))
                
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
                        money_left = await EconomyManager.remove_money(interaction.user.id, lost_money, bank=True)
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
                
                await LevelManager.add_experience(interaction.user.id, experience, interaction.followup.url)
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
                    ).set_footer(text="💡 Try /work or /daily while you wait!"))
    
    @app_commands.command(name="study", description="Choose a category for extra points")
    @app_commands.choices(category=[
        app_commands.Choice(name="Science", value="science"),
        app_commands.Choice(name="Medicine", value="medicine"),
        app_commands.Choice(name="Economics", value="economics"),
        app_commands.Choice(name="Literature", value="literature")
    ])
    async def study(self, interaction: discord.Interaction, category: app_commands.Choice[str]): #  mini_game: str = None für die mini_game implementierung
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        current_time = datetime.datetime.now()
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT study FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_study = result[0]
            claim_available = False

            if result is None or last_study is None:
                claim_available = True
            else:
                last_study = datetime.datetime.strptime(last_study, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_study + datetime.timedelta(minutes=15))

            if not claim_available:
                next_study_time = last_study + datetime.timedelta(minutes=15)
                timestamp = int(next_study_time.timestamp())
                await interaction.response.send_message(embed=discord.Embed(
                    title="⏰ Study Cooldown",
                    description=f"🛑 You need to take a break before studying again!\n\n⏰ Next study: <t:{timestamp}:R>",
                    color=discord.Color.red()))
                return

            # Update last used time for study
            await cursor.execute("UPDATE last_used SET study=? WHERE user_id=?", (current_time, interaction.user.id))
            await db.commit()
        
        
        async with aiofiles.open("study_questions.json", "r", encoding="UTF-8") as file:
            content = await file.read()
            questions = json.loads(content)
            num = random.randint(0,50)
            
            questions = [question for question in questions if question["category"] == category.value]
            
            questions = questions[num]
            question = questions["question"]
            answer_choices = questions["options"] 
            answer = questions["correct"]
            view = Quiz(interaction.user.id, question, answer_choices, answer, category.value, interaction)
            
            await interaction.response.send_message(embed=discord.Embed(title=f"🧠 Category: {category.value.capitalize()}\nYou've chosen to study! Answer the following bonus question for extra rewards:\n\n❓ """+ question,
                                                                        description=f"A) {answer_choices[0]}\nB) {answer_choices[1]}\nC) {answer_choices[2]}\nD) {answer_choices[3]}",colour=6702), view=view)           
                                                    
                                                    
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
                await interaction.response.send_message(embed=discord.Embed(title="WOOOOOOW", description=f"🛑 Slow down! It's available <t:{timestamp}:R>", color=discord.Color.yellow()))
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

        webhook_url = interaction.followup.url
        view = HigherLower(secret_num, comparison_num, interaction.user.id, webhook_url, interaction)
        await interaction.response.send_message(embed=embed, view=view)
        await DatabaseManager.update_cmd_used(interaction.user.id)

    @app_commands.command(name="profile", description="Show your or someones profile")
    async def profile(self, interaction: discord.Interaction, player: discord.User=None):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        
        
        user = interaction.user
         
        if player is not None:
            user = player
            
            async with aiosqlite.connect("database.db") as db:
                cursor = await db.cursor()
                await cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
                result = await cursor.fetchone()  
                
                if result is None or result[0] is None:
                    await interaction.response.send_message(f"{user} doesn't have an account. Try again.", ephemeral=True, delete_after=8.0)
                    return

        level, experience = await LevelManager.get_lvl_exp(user.id)
        inv = await InventoryManager.get_inventory(user.id)
        total = sum([item.quantity for item in inv])
        inv_value = await InventoryManager.get_inventory_value(user.id)
        balance, bank_balance = await EconomyManager.get_balance(user.id)
        total_balance = await EconomyManager.get_total_balance(user.id)
        req_exp = LevelManager.calculate_exp_for_level(level+1)

        embed = discord.Embed(title=user.name, colour=6702).set_thumbnail(url=user.avatar.url.split("?")[0])
        
        rank, leaderboard = await DatabaseManager.get_ranking(user.id, "users", "level")                  
        progess_curr = round(experience/req_exp, 1)
        progess_curr = round(progess_curr * 5) 
        green_bars = progess_curr * "🟩"
        progress_left = int(5 - progess_curr)
        black_bars = progress_left * "⬛"
        progress_bar = green_bars + black_bars
        embed.add_field(name="Level", value=f"Rank: `{rank}/{leaderboard}`\nLevel: `{level}`\nXP: `{experience}/{req_exp}`\n{progress_bar}", inline=True)
        
        rank, leaderboard = await DatabaseManager.get_ranking(user.id, "users", "total_balance")                  
        embed.add_field(name="Balance", value=f"Rank: `{rank}/{leaderboard}`\nTotal: `{total_balance:,}$`\n💵: `{balance:,}$`\n🏦: `{bank_balance:,}$`", inline=True)
                       
        rank, leaderboard = await DatabaseManager.get_ranking(user.id, "users", "inv_value")                  
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
        rank, leaderboard = await DatabaseManager.get_ranking(user.id, "users", "total_knowledge")  
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
        await DatabaseManager.update_cmd_used(interaction.user.id)    
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="Displays your or someones inventory")
    async def inventory(self, interaction: discord.Interaction, user: discord.User = None): 
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return  
        
        user = interaction.user if user is None else user 
    
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
            result = await cursor.fetchone()  
            
            if result is None or result[0] is None:
                await interaction.response.send_message(f"{user} doesn't have an account. Try again.", ephemeral=True, delete_after=8.0)
                return
    
        inventory = await InventoryManager.get_inventory(user.id)
        
        if inventory == []:
            embed = discord.Embed(title="It's pretty empty around here...", 
                                  description=f"{user.name} doesn't have any items yet. I think a few of my commands would come in handy 😉", 
                                  color=discord.Color.dark_gray())
            embed.set_footer(text="Try /higherlower or /scavenge")
            await interaction.response.send_message(embed=embed)
            return 

        pages_req = True if len(inventory) > 9 else False

        embed = discord.Embed(title=f"{user.name}'s inventory", colour=6702).set_thumbnail(url=user.avatar.url.split("?")[0])
        embed.set_footer(text=f"Page 1/{round(len(inventory)/10)}")

        for idx, item in enumerate(inventory):
            if idx <= 9:
                embed.add_field(name=f"{item.quantity}x {item.name}", value=f"{item.description}\nMax_stack: `{item.max_stack}`\nUsable: `{item.usable}`\nValue: `{item.value:,}`", inline=True)

        view = Inventory(interaction, inventory, page=1) if pages_req else discord.utils.MISSING

        await interaction.response.send_message(embed=embed, view=view)
        await DatabaseManager.update_cmd_used(interaction.user.id)