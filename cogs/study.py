import aiosqlite
import aiofiles
import datetime
import json
import random

import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from managers.knowledge import KnowledgeManager
from managers.user import UserManager
from views import Quiz


class StudyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                embed=discord.Embed(
                    title="⏰ Study Cooldown",
                    description=f"🛑 You need to take a break before studying again!\n\n⏰ Next study: <t:{timestamp}:R>",
                    color=discord.Color.red()).set_footer(text= await KnowledgeManager.get_random_tip())
                await interaction.response.send_message(embed=embed)
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

        await DatabaseManager.update_cmd_used(interaction.user.id)
