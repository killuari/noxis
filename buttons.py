import discord, aiosqlite, asyncio, random
from database_manager import *
from user_manager import UserManager
from level_manager import *
from economy_manager import *
from inventory_manager import *


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
        self.money = random.randint(100, 500) 
    
    async def on_timeout(self):
        embed = discord.Embed(
            title="⏰ Time's up!",
            description=f"You were too slow!",
            color=discord.Color.red()
        ).set_footer(text="You have to be faster!")          
            
        
        embed.add_field(name="The **secret** number is:",
                        value=f"{self.secret_num}",
                        inline=True)

        embed.add_field(name="The **comp-number** is:",
                        value=f"{self.comparison_num}",
                        inline=True)
        
        await self.interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="Higher", style=discord.ButtonStyle.green, disabled=False)
    async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)
            
        if self.comparison_num in range(1,201):
            difficulty_factor = 0.8
        elif self.comparison_num in self.comparison_num in range(800, 1001):
            difficulty_factor = random.randint(4, 5) 
        else:
            difficulty_factor = random.randint(1, 2)
            
        if self.secret_num > self.comparison_num:
            self.money *= difficulty_factor
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)
            await EconomyManager.add_money(self.user_id, self.money, False)
            
            embed=discord.Embed(title="Correct! It was higher!",
                                description=f"You gained:\n{self.money:,}$",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")
            
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
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
                
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            
    @discord.ui.button(label="Lower", style=discord.ButtonStyle.red, disabled=False)
    async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)
            
        if self.comparison_num in range(1,201):
            difficulty_factor = random.randint(4, 5) 
        elif self.comparison_num in self.comparison_num in range(800, 1001):
            difficulty_factor = 0.8
        else:
            difficulty_factor = random.randint(1, 2)
            
        if self.secret_num < self.comparison_num:
            money = difficulty_factor * self.money
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)
            await EconomyManager.add_money(self.user_id, money, False)
                
            embed=discord.Embed(title="Correct! It was lower!",
                                description=f"You gained:\n{money:,}$",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")
                
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
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
                
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            
    @discord.ui.button(label="Close Range (+-50)", style=discord.ButtonStyle.secondary, disabled=False)
    async def close_range(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)
                                
        if self.secret_num in range(self.comparison_num-50, self.comparison_num+51):
            money = 6.5 * self.exp_award
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)                
            await EconomyManager.add_money(self.user_id, money, False)
            item = random.choice(await ItemManager.get_items_by_rarity(Rarity.UNCOMMON))
            quantity = random.randint(1,5)
            await InventoryManager.add_item(self.user_id, item.item_id, quantity)
            answer_choice = random.choice(["Very good", "Nice guess", "Good job"])
            
            embed=discord.Embed(title=f"CORRECT! {answer_choice}! It was in the range of +-50!",
                                description=f"You gained:\n{money:,}$\n{quantity}x {item.name}",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")        
                
            
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
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
            
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Same", style=discord.ButtonStyle.primary, disabled=False)
    async def same_num(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id != interaction.user.id:
            interaction.response.send_message("You are not the player", ephemeral=True, delete_after=5.0)    
            
        if self.secret_num == self.comparison_num:
            money = 10 * self.money
            await LevelManager.add_experience(self.user_id, self.exp_award, self.webhook_url)
            await EconomyManager.add_money(self.user_id, money, False)
            item = random.choice(await ItemManager.get_items_by_rarity(Rarity.EPIC))
            quantity = random.randint(1,3)            
            await InventoryManager.add_item(self.user_id, item.item_id, quantity)
            answer_choice = random.choice(["Big Win", "Lucky guess"])

            embed=discord.Embed(title=f"INSANE! {answer_choice}! The numbers were the same!",
                                description=f"You gained:\n{money:,}$\n{quantity}x {item.name}",
                                color=discord.Color.green()
            ).set_footer(text="Let's see if you guess correctly again ;)")        
                
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
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
                
            embed.add_field(name="The **secret** number is:",
                            value=f"{self.secret_num}",
                            inline=True)

            embed.add_field(name="The **comp-number** is:",
                            value=f"{self.comparison_num}",
                            inline=True)
            
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)