import discord, json, aiosqlite, datetime, random
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands
from user_manager import UserManager
from commands import *
from typing import Optional, List, Dict
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
            print(f"[ERROR] Error in {path}: {e}")  
        except Exception as e:
            print(f"[ERROR] Could not load {path}: {e}")
            
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
    

class JobResign(discord.ui.View):
    def __init__(self, interaction, timeout=15):
        super().__init__(timeout=timeout)
        self.interaction = interaction

    @discord.ui.button(label="Resign", style=discord.ButtonStyle.danger)
    async def resign(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.interaction.user.id:
            await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
            return

        now = datetime.datetime.now()
        cooldown_until = now + datetime.timedelta(days=1)
        cooldown_str = cooldown_until.strftime("%Y-%m-%d %H:%M:%S.%f")
        
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("UPDATE users SET job=NULL WHERE user_id=?", (interaction.user.id,))
            await cursor.execute("UPDATE last_used SET resign_cooldown=?, job=NULL WHERE user_id=?", (cooldown_str, interaction.user.id))
            await db.commit()

        embed = discord.Embed(title="Job resignation successful", description="You have successfully resigned from your job.", color=discord.Color.orange())
        embed.set_footer(text="If you want to apply for a new job, use /work apply")
        await interaction.response.edit_message(embed=embed, view=None)
        
    async def on_timeout(self):
        try:
            embed = self.get_embed()
            await self.interaction.edit_original_response(embed=embed, view=None)
        except Exception:
            pass


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

        current_time = datetime.datetime.now()
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT resign_cooldown FROM last_used WHERE user_id=?", (interaction.user.id,))
            row = await cursor.fetchone()
            if row and row[0]:
                try:
                    cooldown_until = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")
                    if current_time < cooldown_until:
                        timestamp = int(cooldown_until.timestamp())
                        embed = discord.Embed(
                            title="Resignation Cooldown",
                            description=f"You can only apply for a new job after your resignation cooldown! Try again: <t:{timestamp}:R>",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                except Exception:
                    pass

            await cursor.execute("SELECT job FROM users WHERE user_id=?", (interaction.user.id,))
            user_job_row = await cursor.fetchone()
            
            if user_job_row and user_job_row[0]:
                if user_job_row[0] == job:
                    embed = discord.Embed(
                        title="Already Employed",
                        description="You already have this job.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                else:
                    embed = discord.Embed(
                        title="Already Employed",
                        description="You already have a job. Please resign first before applying for a new one.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

        user_knowledge = await KnowledgeManager.get_knowledge(interaction.user.id)
        user_level = (await LevelManager.get_lvl_exp(interaction.user.id))[0]
        job = await JobManager.get_job(job)
        
        if not job:
            await interaction.response.send_message("Job does not exist.", ephemeral=True)
            return

        if user_level < job.required_level:
            await interaction.response.send_message(f"You need at least level {job.required_level} for this job.", ephemeral=True)
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
                        value=f"`{job.salary:,}$` per shift",
                        inline=True)
        
        embed.add_field(name="Cooldown",
                        value=f"`{job.cooldown} min` between shifts",
                        inline=True)

        embed.set_footer(text="💡The more knowledge you obtain, the more jobs you can apply for!")
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

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT job FROM users WHERE user_id=?", (interaction.user.id,))
            job_row = await cursor.fetchone()
            if not job_row or not job_row[0]:
                embed = discord.Embed(
                    title="No job found",
                    description="You don't have a job to resign from.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
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

        current_time = datetime.datetime.now()
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT job FROM users WHERE user_id=?", (interaction.user.id,))
            job_row = await cursor.fetchone()
            
            if not job_row or not job_row[0]:
                await interaction.response.send_message(embed=discord.Embed(
                    title="No job found", description="You don't have a job yet. Use `/work apply` to get one!", color=discord.Color.red()), ephemeral=True)
                return

            job_id = job_row[0]
            job = await JobManager.get_job(job_id)
            
            if not job:
                await interaction.response.send_message(embed=discord.Embed(
                    title="Job not found", description="Your job could not be found. Please contact an admin.", color=discord.Color.red()), ephemeral=True)
                return

            await cursor.execute("SELECT job FROM last_used WHERE user_id=?", (interaction.user.id,))
            result = await cursor.fetchone()
            last_job = result[0] if result else None
            claim_available = False

            if result is None or last_job is None:
                claim_available = True
                
            else:
                last_job_dt = datetime.datetime.strptime(last_job, "%Y-%m-%d %H:%M:%S.%f")
                claim_available = current_time >= (last_job_dt + datetime.timedelta(minutes=job.cooldown))

            if not claim_available:
                next_time = last_job_dt + datetime.timedelta(minutes=job.cooldown)
                timestamp = int(next_time.timestamp())
                embed = discord.Embed(
                    title="⏰ Work Cooldown",
                    description=f"You need to wait before your next shift!\nNext available: <t:{timestamp}:R>",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed)
                return

        knowledge_categories = [cat for cat, val in job.required_knowledge.items() if val > 0]
        quiz_category = knowledge_categories[0] if knowledge_categories else None
        bonus_money = int(job.salary * 0.20) if quiz_category else 0

        if quiz_category:
            async with aiofiles.open("study_questions.json", "r", encoding="UTF-8") as file:
                content = await file.read()
                questions = json.loads(content)
                questions = [q for q in questions if q["category"] == quiz_category]
                if questions:
                    question = random.choice(questions)
                    q_text = question["question"]
                    answer_choices = question["options"]
                    answer = question["correct"]

                    view = Quiz(
                        interaction.user.id,
                        q_text,
                        answer_choices,
                        answer,
                        quiz_category,
                        interaction,
                        timeout=25
                    )

                    new_shift_time = datetime.datetime.now()

                    for item in view.children:
                        if isinstance(item, discord.ui.Button):
                            async def wrapped_callback(inter, orig_callback=item.callback, label=item.label):
                                if inter.user.id != interaction.user.id:
                                    await inter.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
                                    return
                                
                                view.stop()
                                
                                if label == answer:
                                    async with aiosqlite.connect("database.db") as db:
                                        cursor = await db.cursor()
                                        await EconomyManager.add_money(inter.user.id, job.salary + bonus_money)
                                        now_str = new_shift_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                                        await cursor.execute("UPDATE last_used SET job=? WHERE user_id=?", (now_str, inter.user.id))
                                        await db.commit()

                                    embed = discord.Embed(
                                        title="Work Shift Complete!",
                                        description=(
                                            f"**Salary:** `{job.salary:,}$`\n"
                                            f"**Bonus:** `{bonus_money:,}$`\n"
                                            f"**Total:** `{job.salary + bonus_money:,}$`\n\n"
                                            f"You worked as a **{job.name}** and earned extra for answering the quiz correctly!"
                                        ),
                                        color=discord.Color.green()
                                    )
                                    embed.add_field(name="Next shift available", value=f"<t:{int((new_shift_time + datetime.timedelta(minutes=job.cooldown)).timestamp())}:R>", inline=True)
                                    await inter.response.edit_message(embed=embed, view=None)
                                    await DatabaseManager.update_cmd_used(inter.user.id)
                                    
                                else:
                                    async with aiosqlite.connect("database.db") as db:
                                        cursor = await db.cursor()
                                        await EconomyManager.add_money(inter.user.id, job.salary)
                                        now_str = new_shift_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                                        await cursor.execute("UPDATE last_used SET job=? WHERE user_id=?", (now_str, inter.user.id))
                                        await db.commit()

                                    embed = discord.Embed(
                                        title="Work Shift Complete!",
                                        description=f"You worked as a **{job.name}** and earned **{job.salary:,}$**.\n\n❌ You answered the quiz incorrectly and received no bonus.",
                                        color=discord.Color.yellow()
                                    )
                                    embed.add_field(name="Next shift available", value=f"<t:{int((new_shift_time + datetime.timedelta(minutes=job.cooldown)).timestamp())}:R>", inline=True)
                                    await inter.response.edit_message(embed=embed, view=None)
                                    await DatabaseManager.update_cmd_used(inter.user.id)
                            item.callback = wrapped_callback

                    for item in view.children:
                        if isinstance(item, discord.ui.Button) and getattr(item, "label", None) == "No Bonus":
                            async def no_bonus_callback(inter):
                                if inter.user.id != interaction.user.id:
                                    await inter.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
                                    return
                                
                                view.stop()
                                
                                new_shift_time = datetime.datetime.now()
                                async with aiosqlite.connect("database.db") as db:
                                    cursor = await db.cursor()
                                    await EconomyManager.add_money(inter.user.id, job.salary)
                                    now_str = new_shift_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                                    await cursor.execute("UPDATE last_used SET job=? WHERE user_id=?", (now_str, inter.user.id))
                                    await db.commit()

                                embed = discord.Embed(
                                    title="Work Shift Complete!",
                                    description=f"You worked as a **{job.name}** and earned **{job.salary:,}$**.\n\n⏭ You skipped the bonus question.",
                                    color=discord.Color.yellow()
                                )
                                embed.add_field(name="Next shift available", value=f"<t:{int((new_shift_time + datetime.timedelta(minutes=job.cooldown)).timestamp())}:R>", inline=True)
                                await inter.response.edit_message(embed=embed, view=None)
                                await DatabaseManager.update_cmd_used(inter.user.id)
                            item.callback = no_bonus_callback

                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title=f"🧑‍💼 Work Shift: {job.name}",
                            description=f"Answer this question from your required knowledge category (**{quiz_category.capitalize()}**) for a **bonus**!\n\n❓ {q_text}",
                            color=discord.Color.from_str("#607bff")
                        ).add_field(
                            name="Options",
                            value=f"A) {answer_choices[0]}\nB) {answer_choices[1]}\nC) {answer_choices[2]}\nD) {answer_choices[3]}",
                            inline=False
                        ), view=view)
                    return

        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await EconomyManager.add_money(interaction.user.id, job.salary)
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            await cursor.execute("UPDATE last_used SET job=? WHERE user_id=?", (now_str, interaction.user.id))
            await db.commit()

        embed = discord.Embed(
            title="Work Shift Complete!",
            description=f"You worked as a **{job.name}** and earned **{job.salary:,}$**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Next shift available", value=f"<t:{int((datetime.datetime.now() + datetime.timedelta(minutes=job.cooldown)).timestamp())}:R>", inline=True)

        await interaction.response.send_message(embed=embed)
        await DatabaseManager.update_cmd_used(interaction.user.id)