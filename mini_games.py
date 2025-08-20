import discord, random
from typing import List
from items import Item
from buttons import *


async def lockpick(interaction: discord.Interaction, target: discord.User, user_guess: str, items: List[str]) -> discord.Interaction:
    new_game = True
    lockpin_plus_active = False
    insider_tip_active = False
    
    if new_game:
        secret_num1 = random.randint(0, 9)
        secret_num2 = random.randint(0, 9)
        secret_num3 = random.randint(0, 9)
        secret_num4 = random.randint(0, 9)
        secret_pin = f"{secret_num1}{secret_num2}{secret_num3}{secret_num4}"
        new_game = False
        
    
    for item_name in items:
        if item_name == "Lockpick plus":
            lockpin_plus_active = True
        elif item_name == "Insider tip":
            insider_tip_active = True
            
    tip = random.randint(0, 3) if insider_tip_active else None
    lifes = 7 if lockpin_plus_active else 6
  
    game_over = False
  
    if lifes <= 0 or game_over:
        await interaction.response.send_message(embed=discord.Embed(title="Bankrobbery complete. Status: ", description=""))
        return
        
    for idx, num in enumerate(user_guess):
        if num in secret_pin:
            for index, secret_num in secret_pin:
                if num == secret_num:
                    message += f"{num} is a correct PIN number and on the right position" if index == idx else f"{num} is a correct PIN number but on the wrong position"
    

    game_over = secret_num == user_guess
    lifes -= 1
    bankrob = BankrobModal(interaction, target, secret_pin)            
    bankrob.message.label = message
    await interaction.response.edit_message(embed=discord.Embed(description="Your guess was:" + bankrob.message.value))
    await interaction.response.send_modal(bankrob)