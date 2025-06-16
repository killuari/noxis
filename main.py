import discord, os, aiosqlite
from discord.ext import commands
from dotenv import load_dotenv
from items import *
from database_manager import DatabaseManager
from commands import BasicCommands
from buttons import *
from inventory_manager import InventoryManager


intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)


load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")


@client.event
async def on_ready():
    async with aiosqlite.connect("database.db") as db:
        cursor = await db.cursor()
        await cursor.execute("DROP TABLE IF EXISTS inventory")
        await db.commit()

    await DatabaseManager.init_database()
    await client.add_cog(BasicCommands(client))    
    await client.tree.sync()

@client.event
async def on_guild_join(guild: discord.Guild):
    all_channels = await guild.fetch_channels()
    
    for channel in all_channels:
        if channel.name.lower() in ["general", "chat", "allgemein"]:
            await channel.send(embed=discord.Embed(title="Hi I'm **Noxis**!", description="Click on **Get Started** to create an account in order to be able to start playing!", color=discord.Color.green()), view=GetStarted())
            return
            
            
@client.event
async def on_member_join(member):
    await member.send(embed=discord.Embed(title="Welcome on this Server!", description="Click on **Get Started** to create an account in order to be able to start playing!", color=discord.Color.green()), view=GetStarted())



client.run(TOKEN)