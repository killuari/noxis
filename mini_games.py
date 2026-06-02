import discord, random
from typing import List, Dict, Tuple
from managers.economy import EconomyManager

class LockpickGame:
    def __init__(self, user: discord.User, target: discord.User = None, callbacks: Dict = {"success_callback": None, "fail_callback": None}, expedition = False, lives: int = 3, num_length: int = 4, max_num: int = 9):
        self.user = user
        self.target = target
        self.num_length = num_length
        self.max_num = max_num
        self.lives = lives
        self.callbacks = callbacks

        if expedition:
            self.lives = 5
            self.num_length = 4
            self.max_num = 9

        secret_nums = [str(num) for num in random.sample(range(self.max_num + 1), self.num_length)]
        self.secret_pin = "".join(secret_nums)
        self.allowed_digits = set(str(i) for i in range(0, self.max_num+1))

        self.desc = ""
        if target is not None:
            self.desc += f"{self.user.mention} is attempting to crack {self.target.mention}'s vault code!\n\n"

    async def start_game(self, interaction: discord.Interaction, items_used: Dict = {"lockpick_plus": False, "insider_tip": False}):
        remaining_digits = tuple(self.allowed_digits-set(self.secret_pin))

        self.tip = random.choice(remaining_digits) if items_used["insider_tip"] else None
        self.lives += 1 if items_used["lockpick_plus"] else 0
        self.max_attempts = self.lives

        self.history = []
        
        await self.next_guess(interaction=interaction)

    async def next_guess(self, interaction: discord.Interaction, current_guess: str = None) -> Tuple[discord.Interaction, bool]:
        success = False
        wrong_input = False

        if current_guess is not None:
            if not current_guess.isdigit() or not all(char in self.allowed_digits for char in current_guess):
                wrong_input = True
            
            if not wrong_input:
                self.lives -= 1
                success, feedback = self.get_visual_feedback(current_guess)
                self.history.append({"guess": current_guess, "feedback": feedback})

        game_over = success or self.lives == 0
        
        if not game_over:
            title="🔐 Cracking the Vault..."
            desc=self.desc + (
                f"You have **{self.lives}/{self.max_attempts} attempts** remaining.\n"
                f"Each guess is a 4-digit code (digits 0-{self.max_num}).\n\n"
                "Feedback per guess:\n"
                "🟩 = Correct digit in correct place\n"
                "🟨 = Correct digit in wrong place\n"
                "🟥 = Not a correct digit"
            )
            color=discord.Color.orange()
        else:
            if self.target is not None:
                stolen_percentage = random.randint(2, 5) * 0.01
                stolen_amount = min(int(stolen_percentage * (await EconomyManager.get_balance(self.target.id))[1]), 25_000)
                if success:
                    await EconomyManager.add_money(self.user.id, stolen_amount)
                    await EconomyManager.remove_money(self.target.id, stolen_amount, bank=True)

                    title = "🎉 Vault Cracked!"
                    desc = (
                        f"{self.user.mention} successfully robbed {self.target.mention}'s bank!\n\n"
                        f"💰 You stole **{stolen_amount:,} coins** from their bank balance."
                    )
                    color = discord.Color.green()
                else:
                    fine = int(0.3 * stolen_amount)
                    money_left = await EconomyManager.remove_money(self.user.id, fine)

                     # if user doesnt have enough money in wallet, try to take it from bank
                    if money_left > 0:
                        money_left = await EconomyManager.remove_money(self.user.id, money_left, bank=True)
                    # TODO: add functionality if user also doesnt have enough money in bank

                    title = "🚨 Police Caught You!"
                    desc = (
                        f"{self.user.mention} failed to crack the vault in time...\n\n"
                        f"🚓 The police fined you **{fine:,} coins**."
                    )
                    color = discord.Color.red()
            else:
                callback = self.callbacks["success_callback"] if success else self.callbacks["fail_callback"]
                await callback(interaction=interaction)
                return

        if wrong_input:
            desc += f"\n\n**Wrong input! Only digits 0-{self.max_num} are allowed!**"

        embed = discord.Embed(title=title, description=desc, color=color)

        if self.tip is not None and not game_over:
            embed.add_field(name="Insider Tip", value=f"Not in the code: {self.tip}", inline=False)

        if len(self.history) > 0:
            history_text = ""
            for entry in self.history:
                guess = entry["guess"]
                feedback = entry["feedback"]
                history_text += f"`{guess}` → {feedback}\n"
            embed.add_field(name="📜 Guess History", value=history_text, inline=False)

        await interaction.response.edit_message(embed=embed, view=LockpickView(lockpick_game=self) if not game_over else None)
    
    def get_visual_feedback(self, guess: str) -> Tuple[bool, str]:
        """
        Returns a visual feedback string for a given guess against the secret.
        - ✅ = correct digit in correct position (bull)
        - ⚠️ = correct digit in wrong position (cow)
        - ❌ = wrong digit
        """
        result = []
        
        # Zähle verfügbare Zeichen im secret (ohne Bulls)
        secret_available = {}
        for i, s in enumerate(self.secret_pin):
            if guess[i] != s:  # Nur nicht-Bulls zählen
                secret_available[s] = secret_available.get(s, 0) + 1
        
        # Markiere Bulls
        for i, (g, s) in enumerate(zip(guess, self.secret_pin)):
            if g == s:
                result.append('🟩')
            else:
                result.append(None)  # Placeholder für zweiten Pass
        
        # Markiere Cows und falsche Digits
        for i, g in enumerate(guess):
            if result[i] is None:  # Nur nicht-Bulls bearbeiten
                if secret_available.get(g, 0) > 0:
                    result[i] = '🟨'
                    secret_available[g] -= 1
                else:
                    result[i] = '🟥'
        
        return (all(char == '🟩' for char in result), ' '.join(result))

class LockpickView(discord.ui.View):
    def __init__(self, lockpick_game: LockpickGame):
        super().__init__(timeout=None)

        self.lockpick_game = lockpick_game

    @discord.ui.button(label="Guess", style=discord.ButtonStyle.primary, disabled=False)
    async def guess(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LockpickModal(interaction=interaction, lockpick_game=self.lockpick_game))

class LockpickModal(discord.ui.Modal):
    def __init__(self, interaction, lockpick_game: LockpickGame, valid=True, title="🔐 Cracking the Vault..."):
        super().__init__(title=title, timeout=None)

        self.interaction = interaction
        self.lockpick_game = lockpick_game

        self.text_input = discord.ui.TextInput(label="Your guess", placeholder="0"*lockpick_game.num_length, min_length=lockpick_game.num_length, max_length=lockpick_game.num_length, required=True)
        self.add_item(self.text_input)
         
    async def on_submit(self, interaction: discord.Interaction):
        await self.lockpick_game.next_guess(interaction=interaction, current_guess=self.text_input.value)
