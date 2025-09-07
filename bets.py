import discord, aiohttp, json, os
from discord import app_commands
from discord.ext import commands, tasks
from user_manager import UserManager
from commands import get_started
from statistics import mean
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict
from discord import ui, TextStyle

class BetManager:
    API_BASE = 'https://api.the-odds-api.com/v4/'
    BL_KEY = 'soccer_germany_bundesliga'
    API_KEY = '35e92ee26bf991936c0b6278a8cbe2bc'
    TZ = ZoneInfo("Europe/Berlin")
    CACHE_FILE = 'bets/matches_cache.json'
    BETS_PLACED_FILE = 'bets/bets_placed.json'
    
    @staticmethod
    def parse_iso_to_utc(dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str).astimezone(timezone.utc)

    @staticmethod
    def avg_price_for_outcomes(event: dict, home: str, away: str) -> Dict[str, Optional[float]]:
        outcome_prices = {"home": [], "draw": [], "away": []}
        for bm in event.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") in ("h2h", "h2h_3_way", "h2h_3way"):
                    for out in market.get("outcomes", []):
                        name = (out.get("name") or "").strip().lower()
                        price = out.get("price")
                        if price is None:
                            continue
                        if "draw" in name:
                            outcome_prices["draw"].append(price)
                        elif home and home.lower() in name:
                            outcome_prices["home"].append(price)
                        elif away and away.lower() in name:
                            outcome_prices["away"].append(price)
                        else:
                            # fuzzy fallback
                            if home and home.lower() in name:
                                outcome_prices["home"].append(price)
                            elif away and away.lower() in name:
                                outcome_prices["away"].append(price)

        def avg(lst):
            return round(mean(lst), 3) if lst else None
        
        return {"home": avg(outcome_prices["home"]), "draw": avg(outcome_prices["draw"]), "away": avg(outcome_prices["away"])}

    @classmethod
    async def fetch_odds_from_api(cls, sport_key: str) -> List[dict]:
        """Fetch odds directly from API"""
        url = f"{cls.API_BASE}/sports/{sport_key}/odds"
        params = {
            "regions": 'eu',
            "markets": "h2h",
            "oddsFormat": "decimal",
            "apiKey": cls.API_KEY
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, params=params, timeout=20) as resp:
                if resp.status == 401:
                    raise RuntimeError("401 Unauthorized — check your ODDS_API_KEY.")
                if resp.status == 429:
                    raise RuntimeError("429 Rate limit / credits exceeded.")
                resp.raise_for_status()
                events = await resp.json()

        now_utc = datetime.now(timezone.utc)
        end_utc = now_utc + timedelta(days=7)
        filtered = []
        for idx, ev in enumerate(events):
            ct = cls.parse_iso_to_utc(ev.get("commence_time"))

            if not ct:
                continue
            if not (now_utc <= ct <= end_utc):
                continue

            home = ev.get("home_team")
            away = ev.get("away_team")
            odds = cls.avg_price_for_outcomes(ev, home, away)
            filtered.append({
                "id": idx,
                "commence_time_utc": ct.isoformat(),  # Convert to string for JSON serialization
                "home": home,
                "away": away,
                "odds": odds
            })

        filtered.sort(key=lambda x: x["commence_time_utc"])
        return filtered

    @classmethod
    def save_matches_to_cache(cls, matches: List[dict]) -> None:
        """Save matches to JSON cache file"""
        cache_data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "matches": matches
        }
        try:
            with open(cls.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"[BetManager] Saved {len(matches)} matches to cache")
        except Exception as e:
            print(f"[BetManager] Error saving cache: {e}")

    @classmethod
    def load_matches_from_cache(cls) -> tuple[List[dict], Optional[datetime]]:
        """Load matches from JSON cache file"""
        if not os.path.exists(cls.CACHE_FILE):
            print(f"[BetManager] Cache file not found")
            return [], None
        
        try:
            with open(cls.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            matches = cache_data.get("matches", [])
            last_updated_str = cache_data.get("last_updated")
            last_updated = datetime.fromisoformat(last_updated_str) if last_updated_str else None
            
            print(f"[BetManager] Loaded {len(matches)} matches from cache (last updated: {last_updated})")
            return matches, last_updated
            
        except Exception as e:
            print(f"[BetManager] Error loading cache: {e}")
            return [], None

    @classmethod
    def is_cache_valid(cls, last_updated: Optional[datetime]) -> bool:
        """Check if cache is still valid (updated today)"""
        if not last_updated:
            return False
        
        now_berlin = datetime.now(cls.TZ)
        last_updated_berlin = last_updated.astimezone(cls.TZ)
        
        # Cache is valid if it was updated today (same date)
        return now_berlin.date() == last_updated_berlin.date()

    @classmethod
    async def get_matches(cls) -> List[dict]:
        """Get matches - from cache if valid, otherwise fetch from API"""
        sport_key = cls.BL_KEY
        
        matches, last_updated = cls.load_matches_from_cache()
        
        if cls.is_cache_valid(last_updated):
            print("[BetManager] Using cached matches")

            # Convert datetime strings back to datetime objects for compatibility
            for match in matches:
                if isinstance(match.get("commence_time_utc"), str):
                    match["commence_time_utc"] = datetime.fromisoformat(match["commence_time_utc"])
            return matches
        
        else:
            print("[BetManager] Cache invalid/expired, fetching from API")
            try:
                matches = await cls.fetch_odds_from_api(sport_key)
                cls.save_matches_to_cache(matches)

                # Convert datetime strings back to datetime objects
                for match in matches:
                    if isinstance(match.get("commence_time_utc"), str):
                        match["commence_time_utc"] = datetime.fromisoformat(match["commence_time_utc"])
                return matches
            
            except Exception as e:
                print(f"[BetManager] API fetch failed: {e}")
                # Return cached data even if expired, better than nothing
                if matches:
                    print("[BetManager] Using expired cache as fallback")
                    for match in matches:
                        if isinstance(match.get("commence_time_utc"), str):
                            match["commence_time_utc"] = datetime.fromisoformat(match["commence_time_utc"])
                    return matches
                return []

    @staticmethod
    def build_embed_for_matches(matches: List[dict]) -> discord.Embed:
        embed = discord.Embed(title="Matches (next 7 days)", description="Matches and averaged Home / Draw / Away odds", color=discord.Color.from_str("#607bff"))

        if not matches:
            embed.add_field(name="No matches", value="No available matches with odds in the next 7 days.", inline=False)
            return embed

        # group matches by local date (Europe/Berlin)
        groups = {}
        for m in matches:
            # Handle both datetime objects and ISO strings
            if isinstance(m["commence_time_utc"], str):
                commence_time = datetime.fromisoformat(m["commence_time_utc"])
            else:
                commence_time = m["commence_time_utc"]
                
            local_dt = commence_time.astimezone(BetManager.TZ)
            date_key = local_dt.date()  # groups by YYYY-MM-DD
            line_time = local_dt.strftime("%H:%M")
            odds = m["odds"]
            
            line = f"{line_time} — {m['home']} vs {m['away']}\n"
            line += f"Home: `{odds['home'] or '-'}` Draw: `{odds['draw'] or '-'}` Away: `{odds['away'] or '-'}`\n"
            groups.setdefault(date_key, []).append(line)

        # Add one field per date
        for date_key in sorted(groups.keys()):
            pretty_date = date_key.strftime("%A, %d %b %Y")  # e.g. "Monday, 08 Sep 2025"
            value = "\n".join(groups[date_key])
            embed.add_field(name=pretty_date, value=value, inline=False)

        embed.set_footer(text="Odds provided by https://the-odds-api.com/")
        return embed

# Modal zum Platzieren einer Wette
class PlaceBetModal(ui.Modal):
    def __init__(self, match: dict, option: str = "Home"):
        super().__init__(title=f"{match['home']} vs {match['away']}")
        self.amount = ui.TextInput(
            label="Place Bet",
            style=TextStyle.short,
            placeholder="1000",
            required=True,
            max_length=12
        )
        self.add_item(self.amount)
        self._match = match
        self.outcome = option

    async def on_submit(self, interaction: discord.Interaction):
        # parse amount
        amount_text = self.amount.value
        try:
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except Exception:
            await interaction.response.send_message("Invalid stake amount.", ephemeral=True)
            return

        match = self._match

        # map outcome -> odds key (adjust if your structure differs)
        outcome_key = self.outcome.lower()
        try:
            raw_odd = match.get("odds", {}).get(outcome_key, 0) or 0
            odds = float(raw_odd)
        except Exception:
            odds = 0.0

        potential_return = int(amount * odds)  # stake * odds

        # format amounts in English style with 2 decimals
        stake_str = f"{amount:,}"
        potential_str = f"{potential_return:,}"
        odds_str = f"{odds:g}"  # compact representation

        # Build the confirmation message (receipt style)
        embed = discord.Embed(
            title="Bet confirmed", 
            description=f"""
                **Match:** {match.get('home')} vs {match.get('away')}
                **Selection:** {self.outcome}
                **Stake:** `{stake_str}$`
                **Odds:** `{odds_str}`
                **Potential return:** `{potential_str}$`
            """,
            color=discord.Color.green()
        )

        # TODO: persist the bet to your DB / file here before confirming

        # send ephemeral confirmation to the user
        await interaction.response.send_message(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("Fehler beim Platzieren der Wette.", ephemeral=True)

class PlaceBetDropdown(discord.ui.Select):
    def __init__(self, button: ui.Button, author_id: int):
        self.author_id = author_id
        self.button = button

        options = [
            discord.SelectOption(label=option_str,
                                 value=option_str, 
                                 default=option_str=="Home")
            for option_str in ("Home", "Draw", "Away")
        ]
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your bet.", ephemeral=True)
            return
        
        self.button.option = self.values[0]

        await interaction.response.defer(ephemeral=True)

# Button als eigene Klasse — aber eine neue Instanz pro Match erzeugen!
class PlaceBetButton(ui.Button):
    def __init__(self, match: dict, author_id: int, option: str = None):
        # label & style hier setzen
        super().__init__(label="Place Bet", style=discord.ButtonStyle.primary)
        self.match = match
        self.option = option
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your bet.", ephemeral=True)
            return
        
        if not self.option:
            await interaction.response.send_message(view=MatchLayoutView(self.match, author_id=self.author_id))
        else:
            await interaction.response.send_modal(PlaceBetModal(self.match, self.option))

class MatchLayoutView(ui.LayoutView):
    def __init__(self, match: Dict, author_id: int):
        super().__init__()

        self.author_id = author_id
            
        odds = match["odds"]
        line = f"**{match['home']}** vs **{match['away']}**\n"
        line += f"Home: `{odds['home'] or '-'}` Draw: `{odds['draw'] or '-'}` Away: `{odds['away'] or '-'}`\n"
        
        text = ui.TextDisplay(line)
        btn = PlaceBetButton(match, author_id=author_id, option="Home")
        section = ui.Section(text, accessory=btn)
        select_menu = PlaceBetDropdown(btn, author_id=author_id)
        select_menu_row = ui.ActionRow(select_menu)

        container = ui.Container(section, select_menu_row)
        self.add_item(container)


class MatchesLayoutView(ui.LayoutView):
    def __init__(self, matches: list, author_id: int):
        super().__init__()

        self.author_id = author_id

        if not matches:
            no_text = ui.TextDisplay("Keine verfügbaren Matches in den nächsten 7 Tagen.")
            container = ui.Container(no_text, accent_color=discord.Color.red())
            self.add_item(container)
            return

        # group matches by local date (Europe/Berlin)
        groups = {}
        for m in matches:
            # Handle both datetime objects and ISO strings
            if isinstance(m["commence_time_utc"], str):
                commence_time = datetime.fromisoformat(m["commence_time_utc"])
            else:
                commence_time = m["commence_time_utc"]
                
            local_dt = commence_time.astimezone(BetManager.TZ)
            date_key = local_dt.date()  # groups by YYYY-MM-DD
            line_time = local_dt.strftime("%H:%M")
            odds = m["odds"]
            
            line = f"{line_time} — {m['home']} vs {m['away']}\n"
            line += f"Home: `{odds['home'] or '-'}` Draw: `{odds['draw'] or '-'}` Away: `{odds['away'] or '-'}`\n"
            groups.setdefault(date_key, []).append((line, m))

        items = []
        # Add one field per date
        for date_key in sorted(groups.keys(), key=lambda d: (d is None, d)):
            pretty_date = date_key.strftime("%A, %d %b %Y")  # e.g. "Monday, 08 Sep 2025"
            pretty_date_display = ui.TextDisplay(f"**{pretty_date}**")
            items.append(pretty_date_display)

            for (match_str, match_obj) in groups[date_key]:
                text = ui.TextDisplay(match_str)
                btn = PlaceBetButton(match_obj, author_id=author_id)
                section = ui.Section(text, accessory=btn)
                separator = ui.Separator(spacing=discord.SeparatorSpacing.large)
                items.extend((section, separator))

        container = ui.Container(*items, accent_color=discord.Color.blurple())
        self.add_item(container)


class BetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bet_group = app_commands.Group(name="bet", description="Bet related commands")
        self.bet_group.command(name="overview", description="Shows all available matches to bet on in a league")(self.bet_overview)
        self.bet_group.command(name="place", description="Place a bet")(self.bet_place)
        self.bot.tree.add_command(self.bet_group)

    async def cog_load(self):
        """Start the daily update task when the cog is loaded"""
        self.daily_odds_update.start()
        print("[BetCommands] Daily odds update task started")

    async def cog_unload(self):
        """Stop the daily update task when the cog is unloaded"""
        self.daily_odds_update.cancel()
        print("[BetCommands] Daily odds update task stopped")

    @tasks.loop(time=time(hour=0, minute=0, second=0))  # Run daily at midnight Berlin time
    async def daily_odds_update(self):
        """Update odds cache daily at midnight"""
        try:
            print("[BetCommands] Starting daily odds update...")
            matches = await BetManager.fetch_odds_from_api(BetManager.BL_KEY)
            BetManager.save_matches_to_cache(matches)
            print(f"[BetCommands] Daily update completed: {len(matches)} matches cached")
        except Exception as e:
            print(f"[BetCommands] Daily update failed: {e}")

    @daily_odds_update.before_loop
    async def before_daily_update(self):
        """Wait until bot is ready before starting the loop"""
        await self.bot.wait_until_ready()
        print("[BetCommands] Daily update task ready, waiting for midnight...")

    async def bet_overview(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        # Defer the response since this might take a moment
        await interaction.response.defer()
        
        matches = await BetManager.get_matches()
        view = MatchesLayoutView(matches, author_id=interaction.user.id)
        await interaction.followup.send(view=view)
        
    async def bet_place(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return