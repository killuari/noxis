import discord, random

from managers.economy import EconomyManager
from managers.inventory import InventoryManager
from models.item import Item
from managers.level import LevelManager


class ShopModal(discord.ui.Modal):
    def __init__(self, interaction: discord.Interaction, item: Item):
        title = f"Buy {item.name}"
        super().__init__(title=title, timeout=None)

        self.interaction = interaction
        self.item = item

        self.text_input = discord.ui.TextInput(label=f"How much {self.item.name} do you wanna buy?", placeholder="1", required=True)
        self.add_item(self.text_input)
         
    async def on_submit(self, interaction: discord.Interaction):
        user_balance = (await EconomyManager.get_balance(self.interaction.user.id))[0]

        if not self.text_input.value.isdigit():
            await interaction.response.send_message(embed=discord.Embed(title="You need to input a number!", color=discord.Color.red()), ephemeral=True)
            return
        
        quantity = int(self.text_input.value)

        if not quantity > 0:
            await interaction.response.send_message(embed=discord.Embed(title="You need to input a number greater than zero!", color=discord.Color.red()), ephemeral=True)
            return

        if user_balance < quantity*self.item.value:
            await interaction.response.send_message(embed=discord.Embed(title="You dont have enough money on your wallet!", color=discord.Color.red()), ephemeral=True)
            return
        
        await InventoryManager.add_item(user_id=self.interaction.user.id, item_id=self.item.item_id, quantity=quantity)
        await EconomyManager.remove_money(user_id=self.interaction.user.id, amount=quantity*self.item.value)
        await LevelManager.add_experience(user_id=self.interaction.user.id, amount=min(1000, quantity*random.randrange(10, 25)), interaction=self.interaction)

        emoji_str = f"<:{self.item.item_id}:{self.item.custom_emoji_id}>"
        await interaction.response.send_message(embed=discord.Embed(title="Success", description=f"You successfully bought {quantity}x {emoji_str} {self.item.name}", color=discord.Color.green()), ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self, interaction, items, page, timeout=None):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.items = items
        self.cur_page = page

    async def add_buttons(self): # buttons wieder per factory method wegen async
        start_idx = (self.cur_page - 1) * 9
        end_idx = start_idx + 9

        user_balance = (await EconomyManager.get_balance(self.interaction.user.id))[0]
        
        for idx, item in enumerate(self.items[start_idx:end_idx]):
            disabled = not user_balance >= item.value

            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            button = discord.ui.Button(
                label=f"Buy {item.name}",
                emoji=emoji_str,
                style=discord.ButtonStyle.green if not disabled else discord.ButtonStyle.gray,
                row=int(idx/3),
                disabled=disabled
            )
            button.callback = await self.buy_item_wrapper(item=item)
            self.add_item(button)

    async def buy_item_wrapper(self, item: Item):
        async def buy_item(interaction: discord.Interaction):
            if self.interaction.user.id != interaction.user.id:
                await interaction.response.send_message(f"Only {self.interaction.user.mention} can use these buttons", ephemeral=True)
                return
            
            await interaction.response.send_modal(ShopModal(interaction=interaction, item=item))
        
        return buy_item

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, row=4, disabled=False)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.mention} can use these buttons", ephemeral=True)
            return
        
        if self.cur_page > 1:
            self.cur_page -= 1
            total_pages = max(1, (len(self.items)+8)//9)
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"Noxis Shop", color=discord.Color.from_str("#607bff"))
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

            for item in self.items[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                embed.add_field(
                    name=f"{emoji_str} {item.name}",
                    value=f"""
                        Rarity: {item.rarity}
                        Cost: {item.value}$
                    """,
                    inline=True
                )

            shop_view = ShopView(interaction=interaction, items=self.items, page=self.cur_page)
            await shop_view.add_buttons()

            await interaction.response.edit_message(embed=embed, view=shop_view)
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, row=4, disabled=False)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.mention} can use these buttons", ephemeral=True)
            return
        
        total_pages = max(1, (len(self.items)+8)//9)
        if self.cur_page < total_pages:
            self.cur_page += 1
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"Noxis Shop", color=discord.Color.from_str("#607bff"))
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")
            
            for item in self.items[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                embed.add_field(
                    name=f"{emoji_str} {item.name}",
                    value=f"""
                        Rarity: {item.rarity}
                        Cost: {item.value}$
                    """,
                    inline=True
                )
                
            await interaction.response.edit_message(embed=embed, view=ShopView(self.interaction, self.items, self.cur_page))
        else:
            await interaction.response.defer()
