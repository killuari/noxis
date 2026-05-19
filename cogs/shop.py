import discord
from discord import app_commands
from discord.ext import commands

from cogs.shared import get_started
from managers.database import DatabaseManager
from items import ItemManager
from managers.user import UserManager
from views import ShopView


class ShopCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Buy items that you need")
    async def shop(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        items = await ItemManager.get_buyable_items()

        embed = discord.Embed(title=f"Noxis Shop", color=discord.Color.from_str("#607bff"))
        embed.set_footer(text=f"Page 1/{max(1, (len(items)+8)//9)} | Use /item <item> to get more detailed info on an item!")

        for idx, item in enumerate(items):
            if idx < 9:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                embed.add_field(
                    name=f"{emoji_str} {item.name}",
                    value=f"""
                        Rarity: {item.rarity}
                        Cost: {item.value}$
                    """,
                    inline=True
                )

        shop_view = ShopView(interaction=interaction, items=items, page=1)
        await shop_view.add_buttons()

        await interaction.response.send_message(embed=embed, view=shop_view)
        await DatabaseManager.update_cmd_used(interaction.user.id)
