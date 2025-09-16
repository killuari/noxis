import discord, aiohttp, json, os, aiosqlite
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands, tasks
from user_manager import UserManager
from commands import *
from statistics import mean
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict
from discord import ui, TextStyle
from economy_manager import EconomyManager
from database_manager import DatabaseManager
from knowledge_manager import KnowledgeManager
from level_manager import LevelManager


@dataclass
class Job:
    job_id: str 
    name: str 
    salary: int 
    cooldown: int
    required_level: int  
    required_knowledge: dict 


class JobManager:
    jobs: Dict[str, Dict] = {}
    
    @classmethod
    async def load_all(cls):
        path = "jobs.json"
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for job_data in data:
                job_id = str(job_data["job_id"])
                cls.jobs[job_id] = job_data

        except json.JSONDecodeError as e:
            print(f"[ERROR] Fehler in {path}: {e}")  
        except Exception as e:
            print(f"[ERROR] Konnte {path} nicht laden: {e}")
            
        print("Successfully loaded all jobs!")
     
    
    @classmethod
    async def get_job(cls, job_id: str) -> Optional[Job]:
        job_dict = cls.jobs.get(job_id)
        
        if job_dict:
            return Job(
                job_id = job_dict["job_id"],
                name = job_dict["name"],
                salary = job_dict["salary"],
                cooldown = job_dict["cooldown"],
                required_level = job_dict["required_level"],
                required_knowledge =job_dict["required_knowledge"]
            )
        return None
    
    @classmethod
    async def get_all_jobs(cls) -> List[Job]:
        """Holt alle verfügbaren jobs"""        
        return [await cls.get_job(job["job_id"]for job in cls.jobs.values())]
    

class JobResign(ui.View):
    def __init__(self, interaction, timeout=60):
        super().__init__(timeout=timeout)
        self.interaction = interaction

    @ui.button(label="Sign", style=discord.ButtonStyle.danger)
    async def resign(self, interaction: discord.Interaction, button: ui.Button):

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET job=NULL WHERE user_id=?", (interaction.user.id,))
            await db.commit()

        embed = discord.Embed(title="Job resignation successful", description="You have successfully resigned from your job.", color=discord.Color.orange())
        embed.set_footer(text="If you want to apply for a new job, use /work apply")
        await interaction.response.edit_message(embed=embed, view=None)


class JobCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="work_apply", description="Apply for a job")
    async def work_apply(self, interaction: discord.Interaction, job: str):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return

        user_knowledge = await KnowledgeManager.get_knowledge(interaction.user.id)
        user_level = (await LevelManager.get_lvl_exp(interaction.user.id))[0]
        job = await JobManager.get_job(job)
        
        if not job:
            await interaction.response.send_message("Job existiert nicht.", ephemeral=True)
            return

        if user_level < job.required_level:
            await interaction.response.send_message(f"Du benötigst mindestens Level {job.required_level} für diesen Job.", ephemeral=True)
            return


        missing = []
        for category, required in job.required_knowledge.items():
            if user_knowledge.get(category, 0) < required:
                missing.append(f"{category}: {required}")
                
        if missing:
            await interaction.response.send_message(f"You lack the following knowledge: {', '.join(missing)}", ephemeral=True)
            return

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET job=? WHERE user_id=?", (job.job_id, interaction.user.id))
            await db.commit()

        embed = discord.Embed(title="Job application successful",
                              description=f"You have successfully applied for **{job.name}**!",
                              color=discord.Color.green())
        
        embed.add_field(name="Salary",
                        value=f"`{job.salary:,}$` every {job.cooldown} hours",
                        inline=False)
        
        embed.set_footer(text="If you want to resign, use /work resign")
        await interaction.response.send_message(embed=embed)


    @work_apply.autocomplete("job")
    async def job_autocomplete(self, interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=job["name"], value=job["job_id"])
            for job in JobManager.jobs.values()
            if current.lower() in job["name"].lower()
        ][:25]  # Discord erlaubt max. 25 Vorschläge


    @app_commands.command(name="work_resign", description="Resign from your current job")
    async def work_resign(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return

        embed = discord.Embed(title="Job resignation",
                              description="Are you sure you want to resign from your job?\nSign below to confirm:",
                              color=discord.Color.orange())
        
        await interaction.response.send_message(embed=embed, view=JobResign(interaction))