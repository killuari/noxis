import discord


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
