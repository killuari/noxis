import discord, random

from knowledge_manager import KnowledgeManager
from level_manager import LevelManager
from user_manager import DEFAULT_KNOWLEDGE


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
                
                await LevelManager.add_experience(interaction.user.id, total_xp, self.interaction)
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
                await LevelManager.add_experience(self.user_id, total_xp, self.interaction)
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
        
        await LevelManager.add_experience(self.user_id, total_xp, self.interaction)        
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
        await LevelManager.add_experience(interaction.user.id, total_xp, self.interaction)
        self.stop()        
        await interaction.response.edit_message(embed=embed, view=None)
