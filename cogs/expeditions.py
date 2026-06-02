import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from managers.expedition import ExpeditionManager
from managers.user import UserManager


class ExpeditionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="expedition", description="Go on an expedition for some special rewards!")
    async def expedition(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return

        await ExpeditionManager.send_expedition_embed(interaction=interaction, expedition_id = 0)
        await DatabaseManager.update_cmd_used(interaction.user.id)
