import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from jobs import JobManager
from managers.knowledge import KnowledgeManager
from managers.level import LevelManager
from managers.user import UserManager
from views import JobList


class WorkCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.work_group = app_commands.Group(name="work", description="Job related commands") # Create work group and register subcommand
        self.work_group.command(name="list", description="Shows all available jobs")(self.work_list) # Register the work list command
        self.bot.tree.add_command(self.work_group)

    async def work_list(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return

        jobs = await JobManager.get_all_jobs()
        user_level, _ = await LevelManager.get_lvl_exp(interaction.user.id)
        user_knowledge = await KnowledgeManager.get_knowledge(interaction.user.id)
        pages_req = len(jobs) > 5
        
        if pages_req:
            view = JobList(interaction, jobs, user_level, user_knowledge, page=1)
            embed = view.get_embed()
        
        else:
            view = discord.utils.MISSING
            embed = discord.Embed(title="Available Jobs", description="Here are the jobs you can apply for:", color=discord.Color.from_str("#607bff"))
            embed.set_footer(text="Page 1/1 | Use /work apply to apply for a job")
          
            for job in jobs:
                requirements_list = []
                requirements_met = True
               
                if user_level < job.required_level:
                    requirements_list.append(f"Level {job.required_level}")
                    requirements_met = False
              
                for category, required_value in job.required_knowledge.items():
                    if required_value > 0:
                        user_knowledge_value = user_knowledge.get(category, 0)
                    
                        if user_knowledge_value < required_value:
                            requirements_list.append(f"{required_value} Knowledge in {category.capitalize()}")
                            requirements_met = False
              
                requirements = ", ".join(requirements_list) if requirements_list else "None"
                cooldown = f"Cooldown: `{job.cooldown} min`"
                req_met = "✅ Available" if requirements_met else "❌ Requirements not met"
             
                embed.add_field(
                    name=f"{job.name}",
                    value=(
                        f"💰 Salary: `{job.salary:,}$`\n"
                        f"⏰ {cooldown}\n"
                        f"📋 Requirements: {requirements}\n"
                        f"{req_met}"),
                    inline=False
                )
                
        await interaction.response.send_message(embed=embed, view=view)
        await DatabaseManager.update_cmd_used(interaction.user.id)
