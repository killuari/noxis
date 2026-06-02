import discord


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
