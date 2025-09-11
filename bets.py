import discord, aiohttp, json, os, aiosqlite
from discord import app_commands
from discord.ext import commands, tasks
from user_manager import UserManager
from commands import get_started
from statistics import mean
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any, Tuple
from discord import ui, TextStyle
from economy_manager import EconomyManager
from database_manager import DatabaseManager

TZ = ZoneInfo("Europe/Berlin")

class BetManager:
    API_BASE = 'https://api.the-odds-api.com/v4/'
    BL_KEY = 'soccer_germany_bundesliga'
    API_KEY = '35e92ee26bf991936c0b6278a8cbe2bc'
    CACHE_FILE = 'bets/matches_cache.json'
    TZ = TZ

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

            id = ev.get("id", idx)
            home = ev.get("home_team")
            away = ev.get("away_team")
            odds = cls.avg_price_for_outcomes(ev, home, away)
            match_dict = {
                "id": id,
                "commence_time_utc": ct.isoformat(),  # Convert to string for JSON serialization
                "home": home,
                "away": away,
                "odds": odds
            }
            filtered.append(match_dict)

        filtered.sort(key=lambda x: x["commence_time_utc"])
        return filtered
    
    @classmethod
    async def fetch_results_from_api(cls, sport_key: str, event_ids: Optional[List[str]] = None) -> Dict[str, Optional[dict]]:
        """
        Fetch scores for given sport/event IDs.
        Returns a dict mapping event_id -> {
            "id": str,
            "commence_time_utc": Optional[str],
            "home_team": str,
            "away_team": str,
            "scores": {"home": int, "away": int},
            "result": "home" | "draw" | "away"
        }
        Returns event_id -> None if not completed
        """
        if not sport_key:
            return {}

        url = f"{cls.API_BASE}/sports/{sport_key}/scores"
        params = {
            "apiKey": cls.API_KEY,
            "daysFrom": 2,
            "dateFormat": "iso"
        }

        if event_ids:
            # ensure strings and comma-separated
            params["eventIds"] = ",".join(str(e) for e in event_ids)

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, params=params, timeout=20) as resp:
                if resp.status == 401:
                    raise RuntimeError("401 Unauthorized — check your ODDS_API_KEY.")
                if resp.status == 429:
                    raise RuntimeError("429 Rate limit / credits exceeded.")
                resp.raise_for_status()
                events = await resp.json()

        results: Dict[str, Optional[dict]] = {}

        for ev in events:
            ev_id = str(ev.get("id"))
            home = ev.get("home_team") or ""
            away = ev.get("away_team") or ""
            commence = ev.get("commence_time")

            commence_iso = None
            if commence:
                try:
                    ct = cls.parse_iso_to_utc(commence)
                    commence_iso = ct.isoformat() if ct else None
                except Exception:
                    commence_iso = commence

            completed = bool(ev.get("completed", False))

            if not completed:
                results[ev_id] = None
                continue

            # Scores mapping
            scores_raw = ev.get("scores") or []
            home_score, away_score = None, None
            try:
                name_to_score = {s.get("name", "").lower(): s.get("score") for s in scores_raw if s}
                if home.lower() in name_to_score:
                    home_score = int(name_to_score[home.lower()])
                if away.lower() in name_to_score:
                    away_score = int(name_to_score[away.lower()])
                # fallback: first two entries
                if home_score is None and len(scores_raw) >= 1:
                    home_score = int(scores_raw[0].get("score"))
                if away_score is None and len(scores_raw) >= 2:
                    away_score = int(scores_raw[1].get("score"))
            except Exception:
                pass

            # result: home / draw / away
            result_str = "draw"
            if home_score is not None and away_score is not None:
                if home_score > away_score:
                    result_str = "home"
                elif away_score > home_score:
                    result_str = "away"

            results[ev_id] = {
                "id": ev_id,
                "commence_time_utc": commence_iso,
                "home_team": home,
                "away_team": away,
                "scores": {
                    "home": home_score,
                    "away": away_score,
                },
                "result": result_str,
            }

        return results

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
    async def insert_bet_into_db(user_id: int, match_id: str, commence_time_utc: datetime, selection: str, stake: int, potential_return: int):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("INSERT INTO bets (user_id, match_id, commence_time_utc, selection, stake, return) VALUES (?, ?, ?, ?, ?, ?)", (user_id, match_id, commence_time_utc, selection, stake, potential_return))
            await db.commit()

    @staticmethod
    async def remove_bet_from_db(user_id: int, match_id: str):
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM bets WHERE (user_id, match_id) = (?, ?)", (user_id, match_id))
            await db.commit()

    @staticmethod
    async def is_bet_placed(user_id: int, match_id: str) -> bool:
        async with aiosqlite.connect("database.db") as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT user_id FROM bets WHERE (user_id, match_id) = (?, ?)", (user_id, match_id))
            result = await cursor.fetchall()

        if result:
            return True
        return False
    
    @staticmethod
    async def get_placed_bets(user_id: int) -> List[Dict[str, Any]]:
        """
        Return all bets for a given user.
        Returned list items: {"match_id": str, "selection": str, "return": int}
        """
        results: List[Dict[str, Any]] = []

        try:
            async with aiosqlite.connect("database.db") as db:
                # return rows as mapping for convenience
                db.row_factory = aiosqlite.Row

                query = """
                    SELECT match_id, commence_time_utc, selection, stake, return
                    FROM bets
                    WHERE user_id = ?
                """
                async with db.execute(query, (user_id,)) as cursor:
                    rows = await cursor.fetchall()

                for r in rows:
                    try:
                        results.append({
                            "match_id": str(r["match_id"]),
                            "commence_time_utc": r["commence_time_utc"],
                            "selection": r["selection"],
                            "stake": r["stake"],
                            "return": r["return"]
                        })
                    except Exception:
                        # if a row is malformed, skip it but continue processing others
                        print(f"[BetManager] Skipping malformed bet row: {dict(r)}")

        except Exception as e:
            print(f"[BetManager] get_placed_bets failed: {e}")
            return []

        results.sort(key=lambda x: x["commence_time_utc"])
        return results

    @staticmethod
    async def get_completed_bets() -> List[Dict[str, Any]]:
        """
        Return all bets where commence_time_utc is older than now - 2 hours.
        Returned list items: {"user_id": int, "match_id": str, "selection": str, "return": int}
        """

        # cutoff = now_utc - 2 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        # normalize: remove microseconds for consistent comparisons/storage
        cutoff_iso = cutoff.replace(microsecond=0)

        results: List[Dict[str, Any]] = []

        try:
            async with aiosqlite.connect("database.db") as db:
                # return rows as mapping for convenience
                db.row_factory = aiosqlite.Row

                query = """
                    SELECT user_id, match_id, selection, return, commence_time_utc
                    FROM bets
                    WHERE commence_time_utc IS NOT NULL
                      AND commence_time_utc <= ?
                """
                async with db.execute(query, (cutoff_iso,)) as cursor:
                    rows = await cursor.fetchall()

                for r in rows:
                    try:
                        results.append({
                            "user_id": int(r["user_id"]),
                            "match_id": str(r["match_id"]),
                            "selection": r["selection"],
                            "return": r["return"]
                        })
                    except Exception:
                        # if a row is malformed, skip it but continue processing others
                        print(f"[BetManager] Skipping malformed bet row: {dict(r)}")

        except Exception as e:
            print(f"[BetManager] get_completed_bets failed: {e}")
            return []

        return results
    
    @staticmethod
    def build_bet_result_embed(result: Dict, bet: Dict) -> Tuple[bool, discord.Embed]:
        user_choice = bet.get("selection", "").lower()
        match_result = result.get("result", "").lower()
        is_win = user_choice == match_result

        color = discord.Color.green() if is_win else discord.Color.orange()

        emoji_map = {"home": "🏠", "away": "✈️", "draw": "🤝"}
        user_emoji = emoji_map.get(user_choice, "")
        result_emoji = emoji_map.get(match_result, "")

        title = "Bet Result — Match Finished"
        description = f"**{result['home_team']}** vs **{result['away_team']}**\n" \
                      f"Final score: **{result['scores']['home']} — {result['scores']['away']}**"

        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name="Match outcome", value=f"{result_emoji} **{match_result.capitalize()}**", inline=True)
        embed.add_field(name="Your bet", value=f"{user_emoji} **{user_choice.capitalize()}**", inline=True)
        embed.add_field(name="Return", value=f"`{bet.get('return', 0)}`", inline=False)
        status_text = "🎉 Congratulations — your bet won!" if is_win else "😞 Sorry — your bet lost."
        embed.add_field(name="Status", value=status_text, inline=False)

        ts_text = result.get("commence_time_utc", "")
        try:
            iso = ts_text.rstrip("Z")
            ts = datetime.fromisoformat(iso)
            embed.timestamp = ts
        except Exception:
            pass

        embed.set_footer(text=f"Match ID: {result.get('id', '?')} • Commence (UTC): {ts_text}")
        return (is_win, embed)

# Modal zum Platzieren einer Wette
class PlaceBetModal(ui.Modal):
    def __init__(self, match: dict, option: str = "home"):
        super().__init__(title=f"{match['home']} vs {match['away']}")
        self.amount = ui.TextInput(
            label="Place Bet",
            style=TextStyle.short,
            placeholder="10000",
            required=True,
            max_length=8
        )
        self.add_item(self.amount)
        self.match = match
        self.outcome = option

    async def on_submit(self, interaction: discord.Interaction):
        # parse amount
        amount_text = self.amount.value
        try:
            amount = int(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except Exception:
            await interaction.response.send_message(embed=discord.Embed(title="Invalid stake amount.", color=discord.Color.red()), ephemeral=True)
            return
        
        if amount < 10_000:
            await interaction.response.send_message(embed=discord.Embed(title="A minimum stake of 10k is required.", color=discord.Color.red()), ephemeral=True)
            return

        wallet_balance = (await EconomyManager.get_balance(interaction.user.id))[0]
        if amount > wallet_balance:
            await interaction.response.send_message(embed=discord.Embed(title="You don't have enough money on your wallet!", color=discord.Color.red()), ephemeral=True)
            return
        
        await EconomyManager.remove_money(interaction.user.id, amount)

        # map outcome -> odds key
        outcome_key = self.outcome.lower()
        try:
            raw_odd = self.match.get("odds", {}).get(outcome_key, 0) or 0
            odds = float(raw_odd)
        except Exception:
            odds = 0.0

        potential_return = int(amount * odds)  # stake * odds
        match_id = self.match.get("id")
        commence_time_utc = self.match.get("commence_time_utc")

        await BetManager.insert_bet_into_db(interaction.user.id, match_id, commence_time_utc, outcome_key, amount, potential_return)
            
        # format amounts
        stake_str = f"{amount:,}"
        potential_str = f"{potential_return:,}"
        odds_str = f"{odds:g}"  # compact representation

        # send ephemeral confirmation to the user
        await interaction.response.edit_message(view=BetPlacedLayoutView(self.match, self.outcome, stake_str, odds_str, potential_str))

class PlaceBetDropdown(discord.ui.Select):
    def __init__(self, button: ui.Button, author_id: int):
        self.author_id = author_id
        self.button = button
        match = self.button.match

        options = [
            discord.SelectOption(label=option_str.capitalize() if option_str not in match.keys() else match[option_str],
                                 value=option_str, 
                                 default=option_str=="home")
            for option_str in ("home", "draw", "away")
        ]
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your bet.", ephemeral=True)
            return
        
        self.button.option = self.values[0]

        await interaction.response.defer(ephemeral=True)

class PlaceBetButton(ui.Button):
    def __init__(self, match: dict, author_id: int, option: str = None):
        self.match = match
        self.option = option
        self.author_id = author_id

        style = discord.ButtonStyle.gray if not option else discord.ButtonStyle.primary

        super().__init__(label="Place Bet", style=style)

    async def set_disabled(self):
        user_id = self.author_id
        match_id = self.match.get("id")

        bet_placed = await BetManager.is_bet_placed(user_id, match_id)
        if bet_placed:
            self.disabled = True

        total_balance = await EconomyManager.get_total_balance(user_id)
        if total_balance < 10_000:
            self.disabled = True

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This is not your bet.", ephemeral=True)
            return
        
        if await BetManager.is_bet_placed(self.author_id, self.match.get("id")):
            await interaction.response.send_message(embed=discord.Embed(title="Bet already placed!", color=discord.Color.red()), ephemeral=True)
            return

        if not self.option:
            await interaction.response.send_message(view=PlaceBetLayoutView(self.match, author_id=self.author_id))
        else:
            await interaction.response.send_modal(PlaceBetModal(self.match, self.option))

class BetPlacedLayoutView(ui.LayoutView):
    def __init__(self, match: Dict, outcome: str, stake_str: str, odds_str: str, potential_str: str):
        super().__init__()

        selection = outcome
        if outcome.lower() in match.keys():
            selection = f"{match[outcome.lower()]}"

        title = "**Bet Confirmed**"
        description = f"**Match:** {match.get('home')} vs {match.get('away')}\n**Selection:** {selection}\n**Stake:** `{stake_str}$`\n**Odds:** `{odds_str}`\n**Potential return:** `{potential_str}$`"
        
        disp1, disp2 = ui.TextDisplay(title), ui.TextDisplay(description)
        container = ui.Container(disp1, disp2, accent_color=discord.Color.green())
        self.add_item(container)

class PlaceBetLayoutView(ui.LayoutView):
    def __init__(self, match: Dict, author_id: int):
        super().__init__()

        self.author_id = author_id
            
        odds = match["odds"]
        title = f"**{match['home']}** vs **{match['away']}**"
        description = f"**Odds:**\n"
        description += f"{match['home']}: `{odds['home'] or '-'}`\nDraw: `{odds['draw'] or '-'}`\n{match['away']}: `{odds['away'] or '-'}`"
        
        disp1, disp2 = ui.TextDisplay(title), ui.TextDisplay(description)
        btn = PlaceBetButton(match, author_id=author_id, option="Home")
        section = ui.Section(disp1, disp2, accessory=btn)
        select_menu = PlaceBetDropdown(btn, author_id=author_id)
        select_menu_row = ui.ActionRow(select_menu)

        container = ui.Container(section, select_menu_row)
        self.add_item(container)

class BetsPlacedLayoutView(ui.LayoutView):
    def __init__(self, matches: list, bets: list, author_id: int, page: int = 1):
        super().__init__()

        self.author_id = author_id
        self.matches = matches
        self.matches_dict = {match["id"]: match for match in matches}
        self.bets = bets
        self.cur_page = page
        self.total_pages = max(1, (len(self.bets)+4)//5)

        self.add_content()

    def add_content(self):
        if not self.bets:
            no_text = ui.TextDisplay("No bets currently placed")
            container = ui.Container(no_text, accent_color=discord.Color.red())
            self.add_item(container)
            return
        
        start_idx = (self.cur_page - 1) * 5
        end_idx = start_idx + 5

        # group matches by utc date
        match_data = []
        for bet in self.bets[start_idx:end_idx]:
            match = self.matches_dict.get(bet["match_id"])

            # Handle both datetime objects and ISO strings
            if isinstance(bet["commence_time_utc"], str):
                commence_time = datetime.fromisoformat(bet["commence_time_utc"])
            else:
                commence_time = bet["commence_time_utc"]
                
            unix_timestamp = int(commence_time.timestamp())

            selection = bet["selection"].capitalize()
            if bet["selection"] in match.keys():
                selection = f"{match[bet["selection"]]}"
            
            line = f"<t:{unix_timestamp}:t> — {match['home']} vs {match['away']}\n"
            line += f"**Selection:** {selection}\n"
            line += f"**Stake:** `{bet["stake"]:,}$`\n"
            line += f"**Potential Return:** `{bet["return"]:,}$`\n"
            
            match_data.append((unix_timestamp, line))

        match_data.sort(key=lambda x: x[0])

        items = []
        current_date_timestamp = None

        for unix_timestamp, line in match_data:
            day_timestamp = (unix_timestamp // 86400) * 86400

            if day_timestamp != current_date_timestamp:
                current_date_timestamp = day_timestamp
                pretty_date_display = ui.TextDisplay(f"**<t:{day_timestamp}:D>**")
                items.append(pretty_date_display)

            text_display = ui.TextDisplay(line)
            separator = ui.Separator(spacing=discord.SeparatorSpacing.large)
            items.extend((text_display, separator))

        next_page_btn = ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.cur_page == self.total_pages)
        previous_page_btn = ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.cur_page == 1)
        next_page_btn.callback = self.next_page
        previous_page_btn.callback = self.previous_page

        action_row = ui.ActionRow(previous_page_btn, next_page_btn)

        footer = ui.TextDisplay(f"Page {self.cur_page}/{self.total_pages}")

        container = ui.Container(*items, footer, action_row)
        self.add_item(container)


    async def previous_page(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(embed=discord.Embed(title="This is not your bet!", color=discord.Color.red()), ephemeral=True)
            return
        
        if self.cur_page > 1:
            await interaction.response.edit_message(view=BetsPlacedLayoutView(self.matches, self.bets, self.author_id, page=self.cur_page-1))
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(embed=discord.Embed(title="This is not your bet!", color=discord.Color.red()), ephemeral=True)
            return
        
        if self.cur_page < self.total_pages:
            await interaction.response.edit_message(view=BetsPlacedLayoutView(self.matches, self.bets, self.author_id, page=self.cur_page+1))
        else:
            await interaction.response.defer()

class MatchesLayoutView(ui.LayoutView):
    def __init__(self, matches: list, author_id: int, page: int = 1):
        super().__init__()

        self.author_id = author_id
        self.matches = matches
        self.cur_page = page
        self.total_pages = max(1, (len(self.matches)+4)//5)

    async def add_buttons(self):
        if not self.matches:
            no_text = ui.TextDisplay("No available matches in the next 7 days.")
            container = ui.Container(no_text, accent_color=discord.Color.red())
            self.add_item(container)
            return
        
        start_idx = (self.cur_page - 1) * 5
        end_idx = start_idx + 5

        # group matches by utc date
        match_data = []
        for match in self.matches[start_idx:end_idx]:
            # Handle both datetime objects and ISO strings
            if isinstance(match["commence_time_utc"], str):
                commence_time = datetime.fromisoformat(match["commence_time_utc"])
            else:
                commence_time = match["commence_time_utc"]
                
            unix_timestamp = int(commence_time.timestamp())

            odds = match["odds"]
            
            line = f"<t:{unix_timestamp}:t> — {match['home']} vs {match['away']}\n"
            line += "**Odds:**\n"
            line += f"Home: `{odds['home'] or '-'}` Draw: `{odds['draw'] or '-'}` Away: `{odds['away'] or '-'}`\n"
            
            match_data.append((unix_timestamp, line, match))

        match_data.sort(key=lambda x: x[0])

        items = []
        current_date_timestamp = None

        for unix_timestamp, line, match_obj in match_data:
            day_timestamp = (unix_timestamp // 86400) * 86400

            if day_timestamp != current_date_timestamp:
                current_date_timestamp = day_timestamp
                pretty_date_display = ui.TextDisplay(f"**<t:{day_timestamp}:D>**")
                items.append(pretty_date_display)

            btn = PlaceBetButton(match_obj, author_id=self.author_id)
            await btn.set_disabled()

            section = ui.Section(line, accessory=btn)
            separator = ui.Separator(spacing=discord.SeparatorSpacing.large)
            items.extend((section, separator))

        next_page_btn = ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.cur_page == self.total_pages)
        previous_page_btn = ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.cur_page == 1)
        next_page_btn.callback = self.next_page
        previous_page_btn.callback = self.previous_page

        action_row = ui.ActionRow(previous_page_btn, next_page_btn)

        footer = ui.TextDisplay(f"Page {self.cur_page}/{self.total_pages} - You need at least 10k to place a bet!")

        container = ui.Container(*items, footer, action_row)
        self.add_item(container)


    async def previous_page(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(embed=discord.Embed(title="This is not your bet!", color=discord.Color.red()), ephemeral=True)
            return
        
        if self.cur_page > 1:
            new_view = MatchesLayoutView(self.matches, self.author_id, page=self.cur_page-1)
            await new_view.add_buttons()
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(embed=discord.Embed(title="This is not your bet!", color=discord.Color.red()), ephemeral=True)
            return
        
        if self.cur_page < self.total_pages:
            new_view = MatchesLayoutView(self.matches, self.author_id, page=self.cur_page+1)
            await new_view.add_buttons()
            await interaction.response.edit_message(view=new_view)
        else:
            await interaction.response.defer()

class BetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bet_group = app_commands.Group(name="bets", description="Bet related commands")
        self.bet_group.command(name="overview", description="Shows all available matches to bet on in a league")(self.bets_overview)
        self.bet_group.command(name="placed", description="See your placed bets")(self.bets_placed)
        self.bot.tree.add_command(self.bet_group)

    async def cog_load(self):
        """Start the daily update task when the cog is loaded"""
        if not self.daily_bets_update.is_running():
            self.daily_bets_update.start()
            print("[BetManager] Daily bets update task started")

    async def cog_unload(self):
        """Stop the daily update task when the cog is unloaded"""
        self.daily_bets_update.cancel()
        print("[BetManager] Daily bets update task stopped")

    @tasks.loop(time=time(hour=3, minute=0, second=0, tzinfo=TZ))  # Run daily at 2 AM Berlin Time
    async def daily_bets_update(self):
        """Update odds cache daily at midnight"""
        try:
            print("[BetManager] Starting daily bets update...")

            matches, last_updated = BetManager.load_matches_from_cache()
            
            if BetManager.is_cache_valid(last_updated):
                print("[BetManager] Cached matches already up to date")
            
            else:
                print("[BetManager] Cache expired, fetching from API")
                matches = await BetManager.fetch_odds_from_api(BetManager.BL_KEY)
                BetManager.save_matches_to_cache(matches)

            print(f"[BetManager] Daily odds update completed: {len(matches)} matches cached")

            completed_bets = await BetManager.get_completed_bets()
            completed_bet_ids = []
            for bet in completed_bets:
                if bet["match_id"] not in completed_bet_ids:
                    completed_bet_ids.append(bet["match_id"])

            if not completed_bet_ids:
                print("[BetManager] Daily bets update completed: No completed bets found")
                return
            
            results = await BetManager.fetch_results_from_api(sport_key=BetManager.BL_KEY, event_ids=completed_bet_ids)
            for bet in completed_bets:
                match_id = bet.get("match_id")
                user_id = bet.get("user_id")
                result = results.get(match_id)
                if not result:
                    continue

                is_win, embed = BetManager.build_bet_result_embed(result, bet)
                if is_win:
                    await EconomyManager.add_money(bet["user_id"], bet["return"])

                await BetManager.remove_bet_from_db(user_id, match_id)

                user = self.bot.get_user(user_id)
                await user.send(embed=embed)

                print(f"[BetManager] Daily bets update completed: {len(completed_bets)} completed bets evaluated")

        except Exception as e:
            print(f"[BetManager] Daily update failed: {e}")

    @daily_bets_update.before_loop
    async def before_daily_update(self):
        """Wait until bot is ready before starting the loop"""
        await self.bot.wait_until_ready()
        print("[BetManager] Daily update task ready, waiting for midnight...")

    async def bets_overview(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        # Defer the response since this might take a moment
        await interaction.response.defer()
        
        matches = await BetManager.get_matches()
        view = MatchesLayoutView(matches, author_id=interaction.user.id)
        await view.add_buttons()

        await interaction.followup.send(view=view)
        await DatabaseManager.update_cmd_used(interaction.user.id)

    async def bets_placed(self, interaction: discord.Interaction):
        if not await UserManager.user_exists(interaction.user.id):
            await get_started(interaction, interaction.user.id)
            return
        
        await interaction.response.defer()

        bets = await BetManager.get_placed_bets(interaction.user.id)
        matches = await BetManager.get_matches()

        await interaction.followup.send(view=BetsPlacedLayoutView(matches, bets, interaction.user.id))