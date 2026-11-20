# Discord Bot

A starter Discord bot written in Python with [discord.py](https://discordpy.readthedocs.io/). It uses slash commands and keeps commands in "cogs" (modules) so new features are easy to add.

## Commands

| Command | What it does |
|---|---|
| `/ping` | Checks that the bot is alive and shows its latency |
| `/hello` | Greets you |
| `/roll [dice]` | Rolls dice, e.g. `/roll 2d6` |
| `/8ball <question>` | Asks the magic 8-ball |
| `/serverinfo` | Shows the server's name, member count, creation date and owner |

## Setup

### 1. Create the bot on Discord
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Open the **Bot** tab and click **Reset Token**, then copy the token. Keep it secret.
3. Open **OAuth2 → URL Generator**, tick the `bot` and `applications.commands` scopes and the **Send Messages** permission, then open the generated URL to invite the bot to your server.

### 2. Run it
Requires Python 3.9 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env and paste your token
python bot.py
```

**Tip:** while developing, put your server's ID in `DEV_GUILD_ID` in `.env` so command changes show up right away. Without it, commands are registered globally and can take up to an hour to appear. To get the ID, turn on Developer Mode in Discord's settings, then right-click the server and choose **Copy Server ID**.

## Adding commands

Put new commands in a cog inside `cogs/`. Copy `cogs/general.py` as a template; every `.py` file in that folder is loaded automatically when the bot starts.
