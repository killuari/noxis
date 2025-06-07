import discord, aiosqlite, asyncio
from database_manager import *
from user_manager import UserManager


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