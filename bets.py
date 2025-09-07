import discord, aiohttp, json, os
from discord import app_commands
from discord.ext import commands, tasks
from user_manager import UserManager
from commands import get_started
from statistics import mean
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict

class BetManager:
    API_BASE = 'https://api.the-odds-api.com/v4/'
    BL_KEY = 'soccer_germany_bundesliga'
    API_KEY = '35e92ee26bf991936c0b6278a8cbe2bc'
    TZ = ZoneInfo("Europe/Berlin")
    CACHE_FILE = 'matches_cache.json'
    
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
        for ev in events:
            ct = cls.parse_iso_to_utc(ev.get("commence_time"))

            if not ct:
                continue
            if not (now_utc <= ct <= end_utc):
                continue

            home = ev.get("home_team")
            away = ev.get("away_team")
            odds = cls.avg_price_for_outcomes(ev, home, away)
            filtered.append({
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
        embed = discord.Embed(title="Matches (next 7 days)", description="Matches and averaged Home / Draw / Away odds", color=0x1F8B4C)

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
        
        try:
            matches = await BetManager.get_matches()
            embed = BetManager.build_embed_for_matches(matches)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="Error", 
                description=f"Failed to fetch matches: {str(e)}", 
                color=0xFF0000
            )
            await interaction.followup.send(embed=error_embed)
        
    async def bet_place(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return