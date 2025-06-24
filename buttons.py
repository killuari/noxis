import discord, aiosqlite, asyncio, random
from database_manager import *
from user_manager import UserManager
from level_manager import *
from economy_manager import *
from inventory_manager import *
from knowledge_manager import *


class GetStarted(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)       
    
    @discord.ui.button(label="Get Started",style=discord.ButtonStyle.primary, disabled=False)
    async def get_started(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await UserManager.user_exists(interaction.user.id):
            await interaction.response.send_message("You already haven an account :)", ephemeral=True, delete_after=5.0)
        else:
            await UserManager.add_user(interaction.user.id)
            await interaction.response.send_message(embed=discord.Embed(title="**Success!**", description="You have an account now. Have fun!", color=discord.Color.green()), delete_after=5.0)


class HigherLower(discord.ui.View):
    def __init__(self, secret_num, comparison_num, user_id, webhool_url, interaction, *, timeout=25): # 25 sec timeout
        super().__init__(timeout=timeout)      
        self.secret_num = secret_num
        self.comparison_num = comparison_num
        self.user_id = user_id
        self.webhook_url = webhool_url
        self.interaction = interaction
        self.exp_award = random.randrange(10, 45)
        self.money = random.randint(200, 400) 
    
    async def on_timeout(self):
        embed = discord.Embed(
            title="⏰ Time's up!",
            description=f"You were too slow!",
            color=discord.Color.red()
        ).set_footer(text="You have to be faster!")          
            
        
        embed.add_field(name="**Secret number:**",
                        value=f"`{self.secret_num}`",
                        inline=True)

        embed.add_field(name="**Comparison number:**",
                        value=f"`{self.comparison_num}`",
                        inline=True)
        
        await self.interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="Higher", style=discord.ButtonStyle.green, disabled=False)
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            await interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)    
            return 
                
        if self.comparison_num in range(1,150):
            difficulty_factor = 1
        elif self.comparison_num in range(150, 301):
            difficulty_factor = 1.5
        elif self.comparison_num in range(700, 850):
            difficulty_factor = 6
        elif self.comparison_num in range(850, 1001):
            difficulty_factor = 8
        else:
            difficulty_factor = 2
            
        if self.secret_num > self.comparison_num:
            self.money = int(self.money * difficulty_factor)
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)
            await EconomyManager.add_money(self.user_id, self.money, False)
            
            embed=discord.Embed(title="Correct! It was higher!",
                                description=f"You gained:\n`{self.money:,}$`",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")
            
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
        
        else:
            state = ""
            if self.secret_num < self.comparison_num:
                state = "lower than"
            elif self.secret_num == self.comparison_num:
                state = "equal to"
                
            embed=discord.Embed(title="Incorrect!",
                                description=f"{self.secret_num} is {state} {self.comparison_num}!",
                                color=discord.Color.red()
            ).set_footer(text="Good luck next time!")          
                
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            
    @discord.ui.button(label="Lower", style=discord.ButtonStyle.red, disabled=False)
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            await interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)    
            return  
                    
        if self.comparison_num in range(1,150):
            difficulty_factor = 8
        elif self.comparison_num in range(150, 301):
            difficulty_factor = 6
        elif self.comparison_num in range(700, 850):
            difficulty_factor = 1.5
        elif self.comparison_num in range(850, 1001):
            difficulty_factor = 1
        else:
            difficulty_factor = 2
            
        if self.secret_num < self.comparison_num:
            self.money = int(self.money * difficulty_factor)
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)
            await EconomyManager.add_money(self.user_id, self.money, False)
                
            embed=discord.Embed(title="Correct! It was lower!",
                                description=f"You gained:\n`{self.money:,}$`",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")
                
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            
        else:
            state = ""
            if self.secret_num > self.comparison_num:
                state = "higher than"
            elif self.secret_num == self.comparison_num:
                state = "equal to"
        
            embed=discord.Embed(title="Incorrect!",
                                description=f"{self.secret_num} is {state} {self.comparison_num}!",
                                color=discord.Color.red()
            ).set_footer(text="Good luck next time!")          
                
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            
    @discord.ui.button(label="Close Range (+-50)", style=discord.ButtonStyle.secondary, disabled=False)
    async def close_range(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            await interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)    
            return 
                                        
        if self.secret_num in range(self.comparison_num-50, self.comparison_num+51):
            self.money = int(self.money * 10) 
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)                
            await EconomyManager.add_money(self.user_id, self.money, False)
            item = random.choice(await ItemManager.get_items_by_rarity(Rarity.UNCOMMON))
            quantity = random.randint(1,3)
            await InventoryManager.add_item(self.user_id, item.item_id, quantity)
            answer_choice = random.choice(["Very good", "Nice guess", "Good job"])
            
            embed=discord.Embed(title=f"CORRECT! {answer_choice}! It was in the range of +-50!",
                                description=f"You gained:\n`{self.money:,}$`\n`{quantity}x {item.name}`",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")        
                
            
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            
        else:
            state = ""
            if self.secret_num < self.comparison_num and self.secret_num not in range(self.comparison_num-50, self.comparison_num+51):
                state = "much lower than"
            elif self.secret_num > self.comparison_num and self.secret_num not in range(self.comparison_num-50, self.comparison_num+51):
                state = "much higher than"
                
            embed=discord.Embed(title="Incorrect!",
                                description=f"{self.secret_num} is {state} {self.comparison_num}!",
                                color=discord.Color.red()
            ).set_footer(text="Good luck next time!")          
            
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Same", style=discord.ButtonStyle.primary, disabled=False)
    async def same_num(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            await interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)    
            return 
                    
        if self.secret_num == self.comparison_num:
            self.money = int(self.money * 100) 
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)
            await EconomyManager.add_money(self.user_id, self.money, False)
            item = random.choice(await ItemManager.get_items_by_rarity(Rarity.EPIC))
            quantity = random.randint(1,3)            
            await InventoryManager.add_item(self.user_id, item.item_id, quantity)
            answer_choice = random.choice(["Big Win", "Lucky guess"])

            embed=discord.Embed(title=f"INSANE! {answer_choice}! The numbers were the same!",
                                description=f"You gained:\n`{self.money:,}$`\n`{quantity}x {item.name}`",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")        
                
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
        
        else:
            state = ""
            if self.secret_num < self.comparison_num:
                state = "lower than"
            elif self.secret_num > self.comparison_num:
                state = "higher than"
                
            embed=discord.Embed(title="Incorrect!",
                                description=f"{self.secret_num} is {state} {self.comparison_num}!",
                                color=discord.Color.red()
            ).set_footer(text="Good luck next time!")          
                
            embed.add_field(name="**Secret number:**",
                            value=f"`{self.secret_num}`",
                            inline=True)

            embed.add_field(name="**Comparison number:**",
                            value=f"`{self.comparison_num}`",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)


class Quiz(discord.ui.View):
    def __init__(self, user_id, question, answer_choices, answer, category, interaction, *, timeout=25):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.question = question
        self.answer_choices = answer_choices
        self.answer = answer
        self.category = category
        self.interaction = interaction
        
        
        self.award = random.randint(10, 20)
        self.experience = random.randint(75, 150)        
        
        for choice in answer_choices:
            button = discord.ui.Button(label=choice, style=discord.ButtonStyle.primary, disabled=False)
            button.callback = self.handle_field(choice)
            self.add_item(button)
            
    def handle_field(self, choice):
        async def move(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("You are not the player.",ephemeral=True, delete_after=5.0)
                return

            if choice == self.answer:
                bonus_award = random.randint(20, 35)
                bonus_xp = random.randint(50, 75)
                
                total_award = self.award + bonus_award
                total_xp = self.experience + bonus_xp

                knowledge = DEFAULT_KNOWLEDGE.copy()
                knowledge[self.category] = total_award
                await KnowledgeManager.add_knowledge(interaction.user.id, knowledge=knowledge)
                await KnowledgeManager.update_total_knowledge(self.user_id)
                total_knowledge = await KnowledgeManager.get_knowledge(interaction.user.id)
                
                await LevelManager.add_experience(interaction.user.id, total_xp, self.interaction.followup.url)
                self.stop()                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                    title=f"✅ Correct! **{self.answer}** is the right answer", 
                    description=f"📖 You gained {self.award} + {bonus_award} Bonus Knowledge in {self.category.capitalize()}!\n🧠 Your total {self.category.capitalize()} Knowledge: {total_knowledge[self.category]} ({(await KnowledgeManager.get_knowledge_threshold(total_knowledge[self.category])).capitalize()})",
                    color=discord.Color.green()), view=None)
            else:
                bonus_award = 0
                bonus_xp = 0
                
                total_award = self.award + bonus_award
                total_xp = self.experience + bonus_xp

                knowledge = DEFAULT_KNOWLEDGE.copy()
                knowledge[self.category] = total_award
                await LevelManager.add_experience(self.user_id, total_xp, self.interaction.followup.url)
                await KnowledgeManager.add_knowledge(interaction.user.id, knowledge=knowledge)
                await KnowledgeManager.update_total_knowledge(self.user_id)
                total_knowledge = await KnowledgeManager.get_knowledge(interaction.user.id)
                self.stop()                
                await interaction.response.edit_message(
                    embed=discord.Embed(
                    title=f"❌ Incorrect. The correct answer was: {self.answer}",
                    description=f"📖 You gained {self.award} Knowledge in {self.category.capitalize()}!\n🧠 Your total {self.category.capitalize()} Knowledge: {total_knowledge[self.category]} ({(await KnowledgeManager.get_knowledge_threshold(total_knowledge[self.category])).capitalize()})", 
                    color=discord.Color.red()), view=None)
                
        return move
    
    
    async def on_timeout(self):
        bonus_award = 0
        bonus_xp = 0
        
        total_award = self.award + bonus_award
        total_xp = self.experience + bonus_xp

        knowledge = DEFAULT_KNOWLEDGE.copy()
        knowledge[self.category] = total_award
        await KnowledgeManager.add_knowledge(self.user_id, knowledge=knowledge)
        await KnowledgeManager.update_total_knowledge(self.user_id)
        total_knowledge = await KnowledgeManager.get_knowledge(self.user_id)

        embed = discord.Embed(
                title="⏰ Time's up!\n📖 Study complete!",
                description=f"📖 You gained {self.award} Knowledge in {self.category.capitalize()}!\n🧠 Your total {self.category.capitalize()} Knowledge: {total_knowledge[self.category]} ({(await KnowledgeManager.get_knowledge_threshold(total_knowledge[self.category])).capitalize()})",
                color=discord.Color.yellow())
        embed.set_footer(text="You have to be faster!")          
        
        await LevelManager.add_experience(self.user_id, total_xp, self.interaction.followup.url)        
        await self.interaction.edit_original_response(embed=embed, view=None)
            
    
    @discord.ui.button(label="No Bonus", style=discord.ButtonStyle.secondary, emoji="❌", row=2)
    async def no_bonus(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You are not the player.",ephemeral=True, delete_after=5.0)
            return
                
        bonus_award = 0
        bonus_xp = 0
        
        total_award = self.award + bonus_award
        total_xp = self.experience + bonus_xp

        knowledge = DEFAULT_KNOWLEDGE.copy()
        knowledge[self.category] = total_award
        await KnowledgeManager.add_knowledge(interaction.user.id, knowledge=knowledge)
        total_knowledge = await KnowledgeManager.get_knowledge(interaction.user.id)

        embed = discord.Embed(
                title="⏭ You chose to skip the bonus question.",
                description=f"📖 You gained {self.award} Knowledge in {self.category.capitalize()}!\n🧠 Your total {self.category.capitalize()} Knowledge: {total_knowledge[self.category]} ({(await KnowledgeManager.get_knowledge_threshold(total_knowledge[self.category])).capitalize()})",
                color=discord.Color.yellow())
        await LevelManager.add_experience(interaction.user.id, total_xp, self.interaction.followup.url)
        self.stop()        
        await interaction.response.edit_message(embed=embed, view=None)


class Inventory(discord.ui.View):
    def __init__(self, interaction, inventory, page, *, timeout=None):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.page = page
        self.inventory = inventory
        self.cur_page = page

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary, disabled=False)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        self.cur_page = 1  
        total_pages = round(len(self.inventory)/10)
        
        embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", colour=6702).set_thumbnail(url=self.interaction.user.avatar.url.split("?")[0])
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

        start_idx = 0
        end_idx = 10

        for item in self.inventory[start_idx:end_idx]:
                embed.add_field(
                    name=f"{item.quantity}x {item.name}",
                    value=(
                        f"{item.description}\n"
                        f"Max_stack: `{item.max_stack}`\n"
                        f"Usable: `{item.usable}`\n"
                        f"Value: `{item.value:,}`"),
                    inline=True)
    
        await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.cur_page))

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, disabled=False)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        if self.cur_page > 1:
            self.cur_page -= 1
            total_pages = round(len(self.inventory)/10)
            
            start_idx = (self.cur_page - 1) * 10
            end_idx = start_idx + 10

            embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", colour=6702).set_thumbnail(url=self.interaction.user.avatar.url.split("?")[0])
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

            for item in self.inventory[start_idx:end_idx]:
                embed.add_field(
                    name=f"{item.quantity}x {item.name}",
                    value=(
                        f"{item.description}\n"
                        f"Max_stack: `{item.max_stack}`\n"
                        f"Usable: `{item.usable}`\n"
                        f"Value: `{item.value:,}`"),
                    inline=True)

            await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.cur_page))
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, disabled=False)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        total_pages = round(len(self.inventory)/10)
        
        if self.cur_page < total_pages:
            self.cur_page += 1
            
            start_idx = (self.cur_page - 1) * 10
            end_idx = start_idx + 10

            embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", colour=6702).set_thumbnail(url=self.interaction.user.avatar.url.split("?")[0])
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

            for item in self.inventory[start_idx:end_idx]:
                embed.add_field(
                    name=f"{item.quantity}x {item.name}",
                    value=(
                        f"{item.description}\n"
                        f"Max_stack: `{item.max_stack}`\n"
                        f"Usable: `{item.usable}`\n"
                        f"Value: `{item.value:,}`"),
                    inline=True)

            await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.cur_page))
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary, disabled=False)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        total_pages = round(len(self.inventory)/10)
        self.cur_page = total_pages  

        start_idx = (self.cur_page - 1) * 10
        end_idx = start_idx + 10

        embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", colour=6702).set_thumbnail(url=self.interaction.user.avatar.url.split("?")[0])
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

        for item in self.inventory[start_idx:end_idx]:
            embed.add_field(
                name=f"{item.quantity}x {item.name}",
                value=(
                    f"{item.description}\n"
                    f"Max_stack: `{item.max_stack}`\n"
                    f"Usable: `{item.usable}`\n"
                    f"Value: `{item.value:,}`"),
                inline=True)

        await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.cur_page))