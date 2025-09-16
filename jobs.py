import discord, aiohttp, json, os, aiosqlite
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands, tasks
from user_manager import UserManager
from commands import get_started
from statistics import mean
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict
from discord import ui, TextStyle
from economy_manager import EconomyManager
from database_manager import DatabaseManager

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
    
    
class JobCommands(commands.Cg):
    def __init__(self, bot):
        self.bot = bot
        work_group = app_commands.Group(name="work", description="Job related commands")    
        work_group.command(name="work apply", description="Apply for a job")(self.work_apply)
        work_group.command(name="work resign")(self.work_resign)
        self.bot.tree.add_command(self.work_group)
    

    @app_commands.choices(category=[
        app_commands.Choice(name=job.name, value=job.value) for job in await JobManager.get_all_jobs()])
                      
                                  
    async def work_apply(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return        
        
        
    async def work_resign(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        