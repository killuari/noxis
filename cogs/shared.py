import discord

from views import GetStarted


# This function creates an account through button interaction
async def get_started(interaction: discord.Interaction, user_id: int):
    await interaction.response.send_message(embed=discord.Embed(title="Wait something's wrong...", description="Seems like you have never used a Noxis-Command before.\nIf you want to start playing click on **Get Started**.", color=discord.Color.red()), view=GetStarted(), ephemeral=True)
