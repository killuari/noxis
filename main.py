import discord, os, sqlite3
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv



intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")


client.run(TOKEN)