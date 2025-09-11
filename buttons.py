import discord, random
from database_manager import *
from user_manager import UserManager
from level_manager import *
from economy_manager import *
from inventory_manager import *
from knowledge_manager import *
from mini_games import *


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
            
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            embed=discord.Embed(title=f"CORRECT! {answer_choice}! It was in the range of +-50!",
                                description=f"You gained:\n`{self.money:,}$`\n{quantity}x {emoji_str} {item.name}",
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

            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            embed=discord.Embed(title=f"INSANE! {answer_choice}! The numbers were the same!",
                                description=f"You gained:\n`{self.money:,}$`\n{quantity}x {emoji_str} {item.name}",
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
    def __init__(self, interaction, inventory, url, page, *, timeout=None):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.inventory = inventory
        self.url = url
        self.cur_page = page

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary, disabled=False)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        self.cur_page = 1  
        total_pages = max(1, (len(self.inventory)+8)//9)
        embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

        start_idx = 0
        end_idx = 9
        for item in self.inventory[start_idx:end_idx]:
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            value = f"{item.value}$" if not item.unique else "Unique"
            embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                            value=f"""
                                Rarity: `{item.rarity}`
                                Value: `{value}`
                            """,
                            inline=True)
        await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, disabled=False)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        if self.cur_page > 1:
            self.cur_page -= 1
            total_pages = max(1, (len(self.inventory)+8)//9)
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

            for item in self.inventory[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                value = f"{item.value}$" if not item.unique else "Unique"
                embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                                value=f"""
                                    Rarity: `{item.rarity}`
                                    Value: `{value}`
                                """,
                                inline=True)

            await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, disabled=False)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        total_pages = max(1, (len(self.inventory)+8)//9)
        if self.cur_page < total_pages:
            self.cur_page += 1
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")
            
            for item in self.inventory[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                value = f"{item.value}$" if not item.unique else "Unique"
                embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                                value=f"""
                                    Rarity: `{item.rarity}`
                                    Value: `{value}`
                                """,
                                inline=True)
                
            await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary, disabled=False)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        total_pages = max(1, (len(self.inventory)+8)//9)
        self.cur_page = total_pages
        start_idx = (self.cur_page - 1) * 9
        end_idx = start_idx + 9
        embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")
        
        for item in self.inventory[start_idx:end_idx]:
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            value = f"{item.value}$" if not item.unique else "Unique"
            embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                            value=f"""
                                Rarity: `{item.rarity}`
                                Value: `{value}`
                            """,
                            inline=True)

        await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))
        
        
class LeaderboardDropdown(discord.ui.Select):
    def __init__(self, leaderboard_handler, author_id, current_value):
        self.leaderboard_handler = leaderboard_handler
        self.author_id = author_id
        options = [
            discord.SelectOption(label="Balance", value="total_balance", description="Top users by balance", default=(current_value=="total_balance")),
            discord.SelectOption(label="Level", value="level", description="Top users by level", default=(current_value=="level")),
            discord.SelectOption(label="Inventory", value="inv_value", description="Top users by inventory value", default=(current_value=="inv_value"))
        ]
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your leaderboard.", ephemeral=True)
            return
        
        new_view = LeaderboardView(self.leaderboard_handler, self.author_id, self.values[0])
        await self.leaderboard_handler.send_leaderboard_embed(interaction, self.values[0], update=True, view=new_view)


class LeaderboardView(discord.ui.View):
    def __init__(self, leaderboard_handler, author_id, current_value, timeout=120):
        super().__init__(timeout=timeout)
        self.message = None  
        self.add_item(LeaderboardDropdown(leaderboard_handler, author_id, current_value))

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception:
                pass
            
class JobList(discord.ui.View):
    def __init__(self, interaction, jobs, user_level, user_knowledge, page=1, *, timeout=300):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.jobs = jobs
        self.user_level = user_level
        self.user_knowledge = user_knowledge
        self.cur_page = page
        
    def get_embed(self):
        total_pages = max(1, (len(self.jobs)+4)//5)
        embed = discord.Embed(title="Available Jobs", description="Here are the jobs you can apply for:", color=discord.Color.from_str("#607bff"))
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages} | Use /work apply to apply for a job")
        start_idx = (self.cur_page - 1) * 5
        end_idx = start_idx + 5

        for job in self.jobs[start_idx:end_idx]:
            requirements_list = []
            requirements_met = True

            if self.user_level < job.required_level:
                requirements_list.append(f"Level {job.required_level}")
                requirements_met = False

            for category, required_value in job.required_knowledge.items():
                if required_value > 0:
                    user_knowledge_value = self.user_knowledge.get(category, 0)
                   
                    if user_knowledge_value < required_value:
                        requirements_list.append(f"{required_value} Knowledge in {category.capitalize()}")
                        requirements_met = False

            requirements = ", ".join(requirements_list) if requirements_list else "None"
            cooldown = f"Cooldown: `{job.cooldown} min`"

            if requirements_met:
                req_met = "✅ Available"
                
            else:
                req_met = "❌ Requirements not met"

            embed.add_field(
                name=f"{job.name}",
                value=(
                    f"💰 Salary: `{job.salary:,}$`\n"
                    f"⏰ {cooldown}\n"
                    f"📋 Requirements: {requirements}\n"
                    f"{req_met}"),
                inline=False
            )
            
        return embed

    async def on_timeout(self):
        try:
            embed = self.get_embed()
            await self.interaction.edit_original_response(embed=embed, view=None)
        except Exception:
            pass

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary, disabled=False)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
       
        self.cur_page = 1
        embed = self.get_embed()
        await interaction.response.edit_message(embed=embed, view=JobList(self.interaction, self.jobs, self.user_level, self.user_knowledge, self.cur_page))

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, disabled=False)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
       
        if self.cur_page > 1:
            self.cur_page -= 1
            embed = self.get_embed()            
            await interaction.response.edit_message(embed=embed, view=JobList(self.interaction, self.jobs, self.user_level, self.user_knowledge, self.cur_page))
       
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, disabled=False)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
       
        total_pages = max(1, (len(self.jobs)+4)//5)
       
        if self.cur_page < total_pages:
            self.cur_page += 1
            embed = self.get_embed()
            await interaction.response.edit_message(embed=embed, view=JobList(self.interaction, self.jobs, self.user_level, self.user_knowledge, self.cur_page))
       
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary, disabled=False)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        total_pages = max(1, (len(self.jobs)+4)//5)
        self.cur_page = total_pages
        embed = self.get_embed() 
        await interaction.response.edit_message(embed=embed, view=JobList(self.interaction, self.jobs, self.user_level, self.user_knowledge, self.cur_page))

class SelectItems(discord.ui.View):
    def __init__(self, user_id: int, allowed_item_ids: Tuple[str], remove_items = True): 
        super().__init__(timeout=None)
        self.user_id = user_id
        self.remove_items = remove_items
        self.allowed_item_ids = allowed_item_ids
        self.button_mapping = {}

    async def add_buttons(self, callback: callable): # das callback kriegt als argument die interaction und die items_used
        for item_id in self.allowed_item_ids:
            item = await ItemManager.get_item(item_id)
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            button = discord.ui.Button(
                label=item.name,
                emoji=emoji_str,
                style=discord.ButtonStyle.secondary, 
                disabled=(await InventoryManager.get_item_quantity(user_id=self.user_id, item_id=item_id)) == 0
            )

            button.callback = self.create_callback(button)
            self.add_item(button)

            self.button_mapping[button.label] = item_id

        self.callback = callback

        self.items_used = {item_id: False for item_id in self.allowed_item_ids}

        self.start_button = discord.ui.Button(label="Start", style=discord.ButtonStyle.green)
        self.start_button.callback = self.create_start_callback()
        self.add_item(self.start_button)

    def create_callback(self, button):
        async def click(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(embed=discord.Embed(title="You are not the player.", color=discord.Color.red()))
                return
            
            button.style = discord.ButtonStyle.blurple if button.style == discord.ButtonStyle.secondary else discord.ButtonStyle.secondary
            
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    if child.style == discord.ButtonStyle.blurple:
                        self.items_used[self.button_mapping[child.label]] = True

            await interaction.response.edit_message(view=self)
        return click
    
    def create_start_callback(self):
        async def start_callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(embed=discord.Embed(title="You are not the player.", color=discord.Color.red()))
                return

            if self.remove_items:
                for item_id, used in self.items_used.items():
                    if used:
                        await InventoryManager.remove_item(interaction.user.id, item_id)

            await self.callback(interaction=interaction, items_used=self.items_used)

        return start_callback
    
class ShopModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction, item: Item):
        title = f"Buy {item.name}"
        super().__init__(title=title, timeout=None)

        self.interaction = interaction
        self.item = item

        self.text_input = discord.ui.TextInput(label=f"How much {self.item.name} do you wanna buy?", placeholder="1", required=True)
        self.add_item(self.text_input)
         
    async def on_submit(self, interaction: discord.Interaction):
        user_balance = (await EconomyManager.get_balance(self.interaction.user.id))[0]

        if not self.text_input.value.isdigit():
            await interaction.response.send_message(embed=discord.Embed(title="You need to input a number!", color=discord.Color.red()), ephemeral=True)
            return
        
        quantity = int(self.text_input.value)

        if not quantity > 0:
            await interaction.response.send_message(embed=discord.Embed(title="You need to input a number greater than zero!", color=discord.Color.red()), ephemeral=True)
            return

        if user_balance < quantity*self.item.value:
            await interaction.response.send_message(embed=discord.Embed(title="You dont have enough money on your wallet!", color=discord.Color.red()), ephemeral=True)
            return
        
        await InventoryManager.add_item(user_id=self.interaction.user.id, item_id=self.item.item_id, quantity=quantity)
        await EconomyManager.remove_money(user_id=self.interaction.user.id, amount=quantity*self.item.value)
        await LevelManager.add_experience(user_id=self.interaction.user.id, amount=min(1000, quantity*random.randrange(10, 25)), webhook_url=interaction.followup.url)

        emoji_str = f"<:{self.item.item_id}:{self.item.custom_emoji_id}>"
        await interaction.response.send_message(embed=discord.Embed(title="Success", description=f"You successfully bought {quantity}x {emoji_str} {self.item.name}", color=discord.Color.green()), ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self, interaction, items, page, timeout=None):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.items = items
        self.cur_page = page

    async def add_buttons(self): # buttons wieder per factory method wegen async
        start_idx = (self.cur_page - 1) * 9
        end_idx = start_idx + 9

        user_balance = (await EconomyManager.get_balance(self.interaction.user.id))[0]
        
        for idx, item in enumerate(self.items[start_idx:end_idx]):
            disabled = not user_balance >= item.value

            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            button = discord.ui.Button(
                label=f"Buy {item.name}",
                emoji=emoji_str,
                style=discord.ButtonStyle.green if not disabled else discord.ButtonStyle.gray,
                row=int(idx/3),
                disabled=disabled
            )
            button.callback = await self.buy_item_wrapper(item=item)
            self.add_item(button)

    async def buy_item_wrapper(self, item: Item):
        async def buy_item(interaction: discord.Interaction):
            if self.interaction.user.id != interaction.user.id:
                await interaction.response.send_message(f"Only {self.interaction.user.mention} can use these buttons", ephemeral=True)
                return
            
            await interaction.response.send_modal(ShopModal(interaction=interaction, item=item))
        
        return buy_item

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, row=4, disabled=False)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.mention} can use these buttons", ephemeral=True)
            return
        
        if self.cur_page > 1:
            self.cur_page -= 1
            total_pages = max(1, (len(self.items)+8)//9)
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"Noxis Shop", color=discord.Color.from_str("#607bff"))
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

            for item in self.items[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                embed.add_field(
                    name=f"{emoji_str} {item.name}",
                    value=f"""
                        Rarity: {item.rarity}
                        Cost: {item.value}$
                    """,
                    inline=True
                )

            shop_view = ShopView(interaction=interaction, items=self.items, page=self.cur_page)
            await shop_view.add_buttons()

            await interaction.response.edit_message(embed=embed, view=shop_view)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, row=4, disabled=False)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.mention} can use these buttons", ephemeral=True)
            return
        
        total_pages = max(1, (len(self.items)+8)//9)
        if self.cur_page < total_pages:
            self.cur_page += 1
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"Noxis Shop", color=discord.Color.from_str("#607bff"))
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")
            
            for item in self.items[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                embed.add_field(
                    name=f"{emoji_str} {item.name}",
                    value=f"""
                        Rarity: {item.rarity}
                        Cost: {item.value}$
                    """,
                    inline=True
                )
                
            await interaction.response.edit_message(embed=embed, view=ShopView(self.interaction, self.items, self.cur_page))
        else:
            await interaction.response.defer()