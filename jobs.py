import discord, json, aiosqlite, datetime
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands
from user_manager import UserManager
from commands import *
from typing import Optional, List, Dict
from discord import ui
from economy_manager import EconomyManager
from database_manager import DatabaseManager
from knowledge_manager import KnowledgeManager
from level_manager import LevelManager
from buttons import *

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
        return [await cls.get_job(job["job_id"]) for job in cls.jobs.values()]
    

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
        self.work_group = app_commands.Group(name="work", description="Job related commands")
        self.work_group.command(name="list", description="Shows all available jobs")(self.work_list)
        self.work_group.command(name="start", description="Start a work shift at your job")(self.work_start)
        self.bot.tree.add_command(self.work_group)

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
                        value=f"`{job.salary:,}$` every {job.cooldown} mins",
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

    async def work_start(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()

            await cursor.execute("SELECT job FROM users WHERE user_id=?", (interaction.user.id,))
            job_row = await cursor.fetchone()
            
            if not job_row or not job_row[0]:
                await interaction.response.send_message(embed=discord.Embed(title="No job found", description="You don't have a job yet. Use `/work apply` to get one!", color=discord.Color.red()), ephemeral=True)
                return
            
            job_id = job_row[0]
            job = await JobManager.get_job(job_id)
            if not job:
                await interaction.response.send_message(embed=discord.Embed(title="Job not found", description="Your job could not be found. Please contact an admin.", color=discord.Color.red()), ephemeral=True)
                return

            await cursor.execute("SELECT job, job_daily, job_shifts FROM last_used WHERE user_id=?", (interaction.user.id,))
            last_used = await cursor.fetchone()
            new_shift_time = datetime.datetime.now()

            last_job = None
            last_job_daily = None
            job_shifts = 0
            
            if last_used:
                last_job = last_used[0]
                last_job_daily = last_used[1]
                job_shifts = last_used[2] or 0
                
            # Check job cooldown
            if last_job:
                last_shift_time = datetime.datetime.strptime(last_job, "%Y-%m-%d %H:%M:%S.%f")
                cooldown = datetime.timedelta(minutes=job.cooldown)
                if new_shift_time < last_shift_time + cooldown:
                    next_time = last_shift_time + cooldown
                    timestamp = int(next_time.timestamp())
                    await interaction.response.send_message(embed=discord.Embed(
                        title="⏰ Work Cooldown",
                        description=f"You need to wait before your next shift!\nNext available: <t:{timestamp}:R>",
                        color=discord.Color.red()))
                    return
                
            # Check daily shift limit
            reset_daily = False
            if last_job_daily:
                last_job_daily_dt = datetime.datetime.strptime(last_job_daily, "%Y-%m-%d %H:%M:%S.%f")
                if new_shift_time >= last_job_daily_dt + datetime.timedelta(days=1):
                    reset_daily = True
                    
            else:
                reset_daily = True
                
            if reset_daily:
                job_shifts = 0
                last_job_daily = new_shift_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                await cursor.execute("UPDATE last_used SET job_daily=?, job_shifts=? WHERE user_id=?", (last_job_daily, 0, interaction.user.id))
                await db.commit()
            
            if job_shifts >= 5:
                if last_job_daily:
                    last_job_daily_dt = datetime.datetime.strptime(last_job_daily, "%Y-%m-%d %H:%M:%S.%f")
                    next_reset = last_job_daily_dt + datetime.timedelta(days=1)
                    timestamp = int(next_reset.timestamp())
                    await interaction.response.send_message(embed=discord.Embed(
                        title="Daily Shift Limit Reached",
                        description=f"You have already worked 5 shifts today.\nNext reset: <t:{timestamp}:R>",
                        color=discord.Color.red()))
                    return

            await EconomyManager.add_money(interaction.user.id, job.salary)
            job_shifts += 1
            now_str = new_shift_time.strftime("%Y-%m-%d %H:%M:%S.%f")
            await cursor.execute("UPDATE last_used SET job=?, job_shifts=? WHERE user_id=?", (now_str, job_shifts, interaction.user.id))
            await db.commit()
            
            embed = discord.Embed(
                title="Work Shift Complete!",
                description=f"You worked as a **{job.name}** and earned **{job.salary:,}$**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Total Shifts today", value=f"`{job_shifts}/5`", inline=True)
            embed.add_field(name="Next shift available", value=f"<t:{int((new_shift_time + datetime.timedelta(minutes=job.cooldown)).timestamp())}:R>", inline=True)
           
            if job_shifts >= 5:
                if last_job_daily:
                    last_job_daily_dt = datetime.datetime.strptime(last_job_daily, "%Y-%m-%d %H:%M:%S.%f")
                    next_reset = last_job_daily_dt + datetime.timedelta(days=1)
                    embed.add_field(name="Next daily reset", value=f"<t:{int(next_reset.timestamp())}:R>", inline=False)
                    
            await interaction.response.send_message(embed=embed)
            await DatabaseManager.update_cmd_used(interaction.user.id)