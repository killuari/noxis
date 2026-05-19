import discord


class Inventory(discord.ui.View):
    def __init__(self, interaction, inventory, url, page, *, timeout=None):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.inventory = inventory
        self.url = url
        self.cur_page = page

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.secondary, disabled=False)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        self.cur_page = 1  
        total_pages = max(1, (len(self.inventory)+8)//9)
        embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

        start_idx = 0
        end_idx = 9
        for item in self.inventory[start_idx:end_idx]:
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            value = f"{item.value}$" if not item.unique else "Unique"
            embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                            value=f"""
                                Rarity: `{item.rarity}`
                                Value: `{value}`
                            """,
                            inline=True)
        await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, disabled=False)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        
        if self.cur_page > 1:
            self.cur_page -= 1
            total_pages = max(1, (len(self.inventory)+8)//9)
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")

            for item in self.inventory[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                value = f"{item.value}$" if not item.unique else "Unique"
                embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                                value=f"""
                                    Rarity: `{item.rarity}`
                                    Value: `{value}`
                                """,
                                inline=True)

            await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary, disabled=False)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        total_pages = max(1, (len(self.inventory)+8)//9)
        if self.cur_page < total_pages:
            self.cur_page += 1
            start_idx = (self.cur_page - 1) * 9
            end_idx = start_idx + 9
            embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
            embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")
            
            for item in self.inventory[start_idx:end_idx]:
                emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
                value = f"{item.value}$" if not item.unique else "Unique"
                embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                                value=f"""
                                    Rarity: `{item.rarity}`
                                    Value: `{value}`
                                """,
                                inline=True)
                
            await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))
        else:
            await interaction.response.defer()

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.secondary, disabled=False)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.interaction.user.id != interaction.user.id:
            await interaction.response.send_message(f"Only {self.interaction.user.name} can use these buttons", ephemeral=True)
            return
        total_pages = max(1, (len(self.inventory)+8)//9)
        self.cur_page = total_pages
        start_idx = (self.cur_page - 1) * 9
        end_idx = start_idx + 9
        embed = discord.Embed(title=f"{self.interaction.user.name}'s inventory", color=discord.Color.from_str("#607bff")).set_thumbnail(url=self.url)
        embed.set_footer(text=f"Page {self.cur_page}/{total_pages}")
        
        for item in self.inventory[start_idx:end_idx]:
            emoji_str = f"<:{item.item_id}:{item.custom_emoji_id}>"
            value = f"{item.value}$" if not item.unique else "Unique"
            embed.add_field(name=f"{emoji_str} {item.name} ({item.quantity}x)",
                            value=f"""
                                Rarity: `{item.rarity}`
                                Value: `{value}`
                            """,
                            inline=True)

        await interaction.response.edit_message(embed=embed, view=Inventory(self.interaction, self.inventory, self.url, self.cur_page))
