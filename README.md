# Noxis Discord Economy Bot

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/)
[![Discord.py](https://img.shields.io/badge/Discord-discord.py-5865F2.svg)](https://discordpy.readthedocs.io/)
[![Database](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Cogs%20%7C%20Managers%20%7C%20Views-orange.svg)](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html)

Noxis is a feature-rich Discord bot built around a persistent economy, RPG-style progression, interactive mini-games, item systems, expeditions, and sports betting workflows.

The project is structured to demonstrate maintainable bot architecture: slash commands are grouped into dedicated Cogs, UI components are isolated in reusable Views, business logic lives in Manager classes, and domain objects are represented through lightweight models.

---

## Key Features

* **Persistent Economy:** Wallet and bank balances, deposits, withdrawals, rewards, robbery mechanics, and inventory value tracking backed by SQLite.
* **Item & Inventory System:** JSON-defined items with rarity, custom emoji support, buy/sell/use behavior, unique items, metadata-driven rewards, and paginated inventory views.
* **Progression & Knowledge:** Experience, levels, quiz-based study sessions, knowledge categories, cooldowns, random tips, and leaderboard statistics.
* **Interactive Discord UI:** Slash commands, buttons, selects, modals, paginated embeds, item selection flows, and onboarding views built with `discord.ui`.
* **Mini-Games & Expeditions:** Higher-or-lower rewards, lockpicking gameplay, configurable expedition events, item-based choices, penalties, and final reward summaries.
* **Sports Betting Module:** Bundesliga, Premier League, and Champions League match handling using cached odds/results data and asynchronous API calls.

---

## Project Architecture & Engineering

### 1. Command Layer (`cogs/`)

Each command area is implemented as its own `commands.Cog`.

* **Economy:** `/balance`, `/deposit`, `/withdraw`
* **Inventory:** `/inventory`, `/item`, `/sell`, `/use`
* **Rewards:** `/daily`, `/weekly`, `/scavenge`
* **Games:** `/higherlower`
* **Crime:** `/rob`, `/bankrob`
* **Progression:** `/study`, `/profile`, `/leaderboard`, `/tip`
* **Jobs & Expeditions:** grouped job listing and expedition launch flows
* **Shop:** paginated item purchasing

This keeps command registration and feature ownership separated instead of centralizing everything in a single monolithic command file.

### 2. Business Logic Layer (`managers/`)

Manager classes encapsulate the core application behavior:

* `DatabaseManager` initializes and updates SQLite tables.
* `EconomyManager`, `InventoryManager`, `LevelManager`, and `KnowledgeManager` own player progression and account state.
* `ItemManager`, `JobManager`, and `ExpeditionManager` load and transform static game data.

This separation makes it easier to change command behavior without rewriting persistence or domain logic.

### 3. Interaction Layer (`views/`)

Reusable Discord UI components live in `views/`, including:

* paginated inventory and job lists
* shop buttons and purchase modals
* quiz answer buttons
* leaderboard dropdowns
* item selection views
* onboarding buttons

The UI layer is intentionally separated from the command layer so interactions can be reused across commands and game flows.

### 4. Data & Models (`data/`, `models/`)

Static content is stored in JSON files under `data/`, while dataclasses and enums live in `models/`.

* `data/items.json` defines item behavior and metadata.
* `data/study_questions.json` contains quiz content.
* `data/expeditions/` contains configurable expedition definitions.
* `models/item.py` and `models/job.py` define the core domain objects.

---

## Tech Stack

* **Language:** Python 3.14+
* **Discord Framework:** `discord.py`
* **Async I/O:** `aiohttp`, `aiofiles`, `aiosqlite`
* **Database:** SQLite
* **Configuration:** `.env` file loaded via `python-dotenv`
* **Dependency Setup:** `uv` or `pip` with `requirements.txt`
* **Data Format:** JSON for items, tips, study questions, and expedition definitions

---

## Installation

### Prerequisites

* Python 3.14 or compatible Python 3.13+ interpreter
* A Discord bot token
* `uv` is recommended for fast virtual environment creation and dependency installation

### 1. Clone the repository

```bash
git clone https://github.com/killuari/noxis.git
cd noxis
```

### 2. Create a virtual environment

Using `uv`:

```bash
uv venv --python 3.14 .venv
source .venv/bin/activate
```

If `uv` is installed but not available in your shell path, call it through its full path, for example:

```bash
/home/killuari/.local/bin/uv venv --python /usr/bin/python3.14 .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

Alternatively, with pip:

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_discord_bot_token
```

---

## Usage

Start the bot from the repository root:

```bash
python main.py
```

On startup, Noxis initializes the SQLite database, loads expedition and item definitions from `data/`, registers all Cogs, adds the betting module, and syncs Discord slash commands.

The bot also sends an onboarding message with a `Get Started` button when it joins a server or when a new member joins.

---

## Project Structure

```text
main.py                         # Bot entry point and startup lifecycle
bets.py                         # Sports betting module and match cache handling
mini_games.py                   # Lockpicking mini-game implementation
cogs/                           # Slash command groups by feature area
  economy.py
  inventory.py
  rewards.py
  crime.py
  study.py
  games.py
  profile.py
  work.py
  expeditions.py
  shop.py
managers/                       # Persistence and domain logic
  database.py
  economy.py
  inventory.py
  items.py
  jobs.py
  expedition.py
  knowledge.py
  level.py
  user.py
models/                         # Dataclasses and enums
  item.py
  job.py
views/                          # Discord UI views, buttons, selects, and modals
  higher_lower.py
  inventory.py
  item_selection.py
  jobs.py
  leaderboard.py
  onboarding.py
  quiz.py
  shop.py
data/                           # Static game data and cache directories
  items.json
  random_tips.json
  study_questions.json
  expeditions/
  bets/
requirements.txt                # Frozen dependency snapshot
.python-version                 # Preferred local Python version
```

---

## License

This repository does not currently include a license file. Add a `LICENSE` file before publishing or distributing the project under a specific license.

---

**Developed by Luis Kahles and Athanasios Giotas**

*Focus: Discord Bot Development, Async Python, Modular Software Architecture & Persistent Game Systems.*
