import discord, os, aiosqlite
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from dataclasses import dataclass
from items import *
from database_manager import DatabaseManager
from inventory_manager import InventoryManager
from user_manager import UserManager
from economy_manager import EconomyManager


intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")

@client.event
async def on_ready():
    await DatabaseManager.init_database()

    await UserManager.add_user(5)

    print(await InventoryManager.user_has_item(5, 1))
    await InventoryManager.add_item(5, 1)
    print(await InventoryManager.user_has_item(5, 1))
    print(await InventoryManager.user_has_item(5, 1, 5))
    await InventoryManager.add_item(5, 1, 4)
    print(await InventoryManager.user_has_item(5, 1, 5))
    await InventoryManager.remove_item(5, 1, 2)
    print(await InventoryManager.user_has_item(5, 1, 5))
    print(await InventoryManager.user_has_item(5, 1, 3))
    await InventoryManager.add_item(5, 2, 10)
    await InventoryManager.remove_item(5, 1, 3)
    await EconomyManager.add_money(5, 10, bank=False)
    await EconomyManager.add_money(5, 10, bank=True)    
    await EconomyManager.remove_money(5, 23, bank=False)
    print(await EconomyManager.get_user_balance(5))


client.run(TOKEN)