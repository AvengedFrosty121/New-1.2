"""General-purpose slash commands. Copy this file as a template for new cogs."""

import random

import discord
from discord import app_commands
from discord.ext import commands

EIGHT_BALL_ANSWERS = [
    "It is certain.", "Without a doubt.", "Yes, definitely.", "Most likely.",
    "Ask again later.", "Cannot predict now.", "Don't count on it.",
    "My sources say no.", "Very doubtful.",
]


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(description="Check that the bot is alive.")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! 🏓 ({latency_ms} ms)")

    @app_commands.command(description="Say hello.")
    async def hello(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f"Hey {interaction.user.mention}! 👋")

    @app_commands.command(description="Roll dice, e.g. 2d6.")
    @app_commands.describe(dice="Dice to roll in NdM format (default 1d6)")
    async def roll(self, interaction: discord.Interaction, dice: str = "1d6") -> None:
        try:
            count_str, sides_str = dice.lower().split("d")
            count = int(count_str or 1)
            sides = int(sides_str)
            if not (1 <= count <= 100 and 2 <= sides <= 1000):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Use NdM format, e.g. `2d6` (up to 100 dice, 2–1000 sides).", ephemeral=True
            )
            return
        rolls = [random.randint(1, sides) for _ in range(count)]
        detail = ", ".join(map(str, rolls)) if count > 1 else ""
        msg = f"🎲 **{dice}** → **{sum(rolls)}**" + (f" ({detail})" if detail else "")
        await interaction.response.send_message(msg)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="Your yes/no question")
    async def eight_ball(self, interaction: discord.Interaction, question: str) -> None:
        await interaction.response.send_message(
            f"🎱 *{question}*\n**{random.choice(EIGHT_BALL_ANSWERS)}**"
        )

    @app_commands.command(description="Show info about this server.")
    @app_commands.guild_only()
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "D"))
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
