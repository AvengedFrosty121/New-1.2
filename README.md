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

### Music

| Command | What it does |
|---|---|
| `/play <link or search>` | Joins your voice channel and plays a song, or adds it to the queue |
| `/pause`, `/resume` | Pauses or resumes playback |
| `/skip` | Skips to the next song |
| `/stop` | Stops, clears the queue and leaves the channel |
| `/queue` | Shows what's playing and what's next |
| `/nowplaying` | Shows the current song |
| `/volume <0-100>` | Sets the volume |
| `/loop` | Repeats the current song (run again to turn off) |
| `/remove <number>` | Removes a song from the queue |

Links can come from YouTube, SoundCloud, Bandcamp and [many other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). Plain text searches YouTube. The bot leaves when everyone else leaves the channel, or after 5 minutes with nothing playing. Only people in the bot's voice channel can control playback.

## Setup

### 1. Create the bot on Discord
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Open the **Bot** tab and click **Reset Token**, then copy the token. Keep it secret.
3. Open **OAuth2 → URL Generator**, tick the `bot` and `applications.commands` scopes and the **Send Messages**, **Connect** and **Speak** permissions, then open the generated URL to invite the bot to your server.

### 2. Install FFmpeg
The music commands need [FFmpeg](https://ffmpeg.org/download.html):
- **Windows:** `winget install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

### 3. Run it
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

## Keeping the music working

YouTube changes things often, which breaks yt-dlp from time to time. If songs stop playing, update it first:

```bash
pip install -U yt-dlp
```

Note that streaming from YouTube goes against YouTube's Terms of Service. That's why big public music bots get shut down. It's fine for a bot on your own server with friends, but don't expect to grow a public bot this way.
