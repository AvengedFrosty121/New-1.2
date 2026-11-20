"""Entry point: loads config, loads every cog in ./cogs, and starts the bot."""

import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID", "").strip()

log = logging.getLogger("bot")


class Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        # Load every .py file in ./cogs as an extension.
        for path in sorted(Path(__file__).parent.joinpath("cogs").glob("*.py")):
            if path.name.startswith("_"):
                continue
            await self.load_extension(f"cogs.{path.stem}")
            log.info("Loaded cog: %s", path.stem)

        # Register slash commands with Discord.
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to dev guild %s", len(synced), DEV_GUILD_ID)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global commands", len(synced))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)


def main() -> None:
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and add your token.")
    Bot().run(TOKEN, root_logger=True)


if __name__ == "__main__":
    main()
