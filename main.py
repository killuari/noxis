import discord, os, aiosqlite
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from dataclasses import dataclass
from items import *
from database_manager import DatabaseManager

intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")

@client.event
async def on_ready():
    await DatabaseManager.init_database()

client.run(TOKEN)