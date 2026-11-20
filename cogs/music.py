"""Music commands: play audio from YouTube, SoundCloud and other links in voice channels.

Requires FFmpeg installed on the machine running the bot (see README).
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "default_search": "ytsearch",  # plain text becomes a YouTube search
    "quiet": True,
    "no_warnings": True,
    "source_address": "0.0.0.0",
}
FFMPEG_OPTIONS = {
    # Reconnect if the stream drops instead of skipping the song.
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}
IDLE_TIMEOUT = 300  # seconds to stay in voice with nothing playing
MAX_QUEUE = 100

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


@dataclass
class Track:
    title: str
    page_url: str
    duration: int | None
    requester: discord.abc.User

    @property
    def length(self) -> str:
        if not self.duration:
            return "live"
        minutes, seconds = divmod(int(self.duration), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"

    def __str__(self) -> str:
        return f"[{self.title}]({self.page_url}) `{self.length}`"


async def extract(query: str) -> dict:
    """Run yt-dlp off the event loop so the bot doesn't freeze while it works."""
    loop = asyncio.get_running_loop()
    info = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
    if info and "entries" in info:  # search results come back as a list
        entries = [e for e in info["entries"] if e]
        if not entries:
            raise LookupError("No results found.")
        info = entries[0]
    if not info:
        raise LookupError("No results found.")
    return info


class GuildPlayer:
    """Queue and playback state for one server."""

    def __init__(self, bot: commands.Bot, guild: discord.Guild) -> None:
        self.bot = bot
        self.guild = guild
        self.queue: deque[Track] = deque()
        self.current: Track | None = None
        self.volume = 0.5
        self.loop_track = False
        self._idle_task: asyncio.Task | None = None

    @property
    def voice(self) -> discord.VoiceClient | None:
        return self.guild.voice_client  # type: ignore[return-value]

    async def play_next(self) -> None:
        vc = self.voice
        if vc is None or not vc.is_connected():
            return
        if not (self.loop_track and self.current):
            self.current = self.queue.popleft() if self.queue else None
        if self.current is None:
            self._start_idle_timer()
            return
        self._cancel_idle_timer()

        track = self.current
        try:
            # Resolve the stream URL right before playing: these links expire.
            info = await extract(track.page_url)
        except Exception:
            log.exception("Could not load %s", track.page_url)
            self.current = None
            self.loop_track = False
            await self.play_next()
            return

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS), volume=self.volume
        )

        def after(error: Exception | None) -> None:
            if error:
                log.error("Player error: %s", error)
            asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)

        vc.play(source, after=after)

    def _start_idle_timer(self) -> None:
        self._cancel_idle_timer()
        self._idle_task = self.bot.loop.create_task(self._idle_disconnect())

    def _cancel_idle_timer(self) -> None:
        if self._idle_task and not self._idle_task.done():
            self._idle_task.cancel()
        self._idle_task = None

    async def _idle_disconnect(self) -> None:
        await asyncio.sleep(IDLE_TIMEOUT)
        if self.voice and not self.voice.is_playing():
            await self.voice.disconnect()

    async def stop(self) -> None:
        self.queue.clear()
        self.current = None
        self.loop_track = False
        self._cancel_idle_timer()
        if self.voice:
            await self.voice.disconnect()


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.players: dict[int, GuildPlayer] = {}

    def player(self, guild: discord.Guild) -> GuildPlayer:
        if guild.id not in self.players:
            self.players[guild.id] = GuildPlayer(self.bot, guild)
        return self.players[guild.id]

    async def cog_unload(self) -> None:
        for p in self.players.values():
            await p.stop()

    # ----- checks -----------------------------------------------------------

    @staticmethod
    async def _require_same_channel(interaction: discord.Interaction) -> bool:
        """Only let people in the bot's voice channel control playback."""
        user_voice = interaction.user.voice  # type: ignore[union-attr]
        vc = interaction.guild.voice_client
        if vc is None:
            await interaction.response.send_message("I'm not playing anything.", ephemeral=True)
            return False
        if user_voice is None or user_voice.channel != vc.channel:
            await interaction.response.send_message(
                "Join my voice channel to control the music.", ephemeral=True
            )
            return False
        return True

    # ----- commands ---------------------------------------------------------

    @app_commands.command(description="Play a song from a link or search YouTube.")
    @app_commands.describe(query="A link (YouTube, SoundCloud, ...) or search terms")
    @app_commands.guild_only()
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        user_voice = interaction.user.voice  # type: ignore[union-attr]
        if user_voice is None or user_voice.channel is None:
            await interaction.response.send_message("Join a voice channel first.", ephemeral=True)
            return

        vc = interaction.guild.voice_client
        if vc is not None and vc.channel != user_voice.channel:
            await interaction.response.send_message(
                f"I'm already playing in {vc.channel.mention}.", ephemeral=True
            )
            return

        p = self.player(interaction.guild)
        if len(p.queue) >= MAX_QUEUE:
            await interaction.response.send_message("The queue is full.", ephemeral=True)
            return

        await interaction.response.defer()  # searching can take a few seconds
        try:
            info = await extract(query)
        except Exception as e:
            await interaction.followup.send(f"Couldn't find that: {e}")
            return

        track = Track(
            title=info.get("title", "Unknown"),
            page_url=info.get("webpage_url") or info.get("original_url") or query,
            duration=info.get("duration"),
            requester=interaction.user,
        )

        if vc is None:
            await user_voice.channel.connect(self_deaf=True)

        p.queue.append(track)
        if p.current is None and not p.voice.is_playing():
            await interaction.followup.send(f"▶️ Now playing {track}")
            await p.play_next()
        else:
            await interaction.followup.send(f"➕ Queued at #{len(p.queue)}: {track}")

    @app_commands.command(description="Pause the music.")
    @app_commands.guild_only()
    async def pause(self, interaction: discord.Interaction) -> None:
        if not await self._require_same_channel(interaction):
            return
        vc = interaction.guild.voice_client
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Paused.")
        else:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)

    @app_commands.command(description="Resume the music.")
    @app_commands.guild_only()
    async def resume(self, interaction: discord.Interaction) -> None:
        if not await self._require_same_channel(interaction):
            return
        vc = interaction.guild.voice_client
        if vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Resumed.")
        else:
            await interaction.response.send_message("I'm not paused.", ephemeral=True)

    @app_commands.command(description="Skip the current song.")
    @app_commands.guild_only()
    async def skip(self, interaction: discord.Interaction) -> None:
        if not await self._require_same_channel(interaction):
            return
        p = self.player(interaction.guild)
        vc = interaction.guild.voice_client
        if not (vc.is_playing() or vc.is_paused()):
            await interaction.response.send_message("Nothing to skip.", ephemeral=True)
            return
        skipped = p.current
        p.loop_track = False
        vc.stop()  # triggers the after-callback, which plays the next song
        await interaction.response.send_message(f"⏭️ Skipped {skipped.title if skipped else 'song'}.")

    @app_commands.command(description="Stop the music, clear the queue and leave.")
    @app_commands.guild_only()
    async def stop(self, interaction: discord.Interaction) -> None:
        if not await self._require_same_channel(interaction):
            return
        await self.player(interaction.guild).stop()
        await interaction.response.send_message("⏹️ Stopped and left the channel.")

    @app_commands.command(description="Show the song queue.")
    @app_commands.guild_only()
    async def queue(self, interaction: discord.Interaction) -> None:
        p = self.player(interaction.guild)
        if p.current is None and not p.queue:
            await interaction.response.send_message("The queue is empty.", ephemeral=True)
            return
        embed = discord.Embed(title="Queue", color=discord.Color.blurple())
        if p.current:
            loop_note = " 🔂" if p.loop_track else ""
            embed.add_field(name="Now playing", value=f"{p.current}{loop_note}", inline=False)
        if p.queue:
            lines = [f"`{i}.` {t}" for i, t in enumerate(list(p.queue)[:10], start=1)]
            if len(p.queue) > 10:
                lines.append(f"...and {len(p.queue) - 10} more")
            embed.add_field(name="Up next", value="\n".join(lines), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Show the song that's playing now.")
    @app_commands.guild_only()
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        p = self.player(interaction.guild)
        if p.current is None:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return
        await interaction.response.send_message(
            f"🎶 {p.current} — requested by {p.current.requester.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @app_commands.command(description="Set the volume (0–100).")
    @app_commands.describe(level="Volume percent")
    @app_commands.guild_only()
    async def volume(
        self, interaction: discord.Interaction, level: app_commands.Range[int, 0, 100]
    ) -> None:
        if not await self._require_same_channel(interaction):
            return
        p = self.player(interaction.guild)
        p.volume = level / 100
        vc = interaction.guild.voice_client
        if isinstance(vc.source, discord.PCMVolumeTransformer):
            vc.source.volume = p.volume
        await interaction.response.send_message(f"🔊 Volume set to {level}%.")

    @app_commands.command(description="Repeat the current song on/off.")
    @app_commands.guild_only()
    async def loop(self, interaction: discord.Interaction) -> None:
        if not await self._require_same_channel(interaction):
            return
        p = self.player(interaction.guild)
        p.loop_track = not p.loop_track
        await interaction.response.send_message(
            "🔂 Looping the current song." if p.loop_track else "➡️ Loop off."
        )

    @app_commands.command(description="Remove a song from the queue by its number.")
    @app_commands.describe(position="Number shown in /queue")
    @app_commands.guild_only()
    async def remove(
        self, interaction: discord.Interaction, position: app_commands.Range[int, 1]
    ) -> None:
        if not await self._require_same_channel(interaction):
            return
        p = self.player(interaction.guild)
        if position > len(p.queue):
            await interaction.response.send_message("There's no song at that number.", ephemeral=True)
            return
        track = p.queue[position - 1]
        del p.queue[position - 1]
        await interaction.response.send_message(f"🗑️ Removed {track.title}.")

    # ----- events -----------------------------------------------------------

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        vc = member.guild.voice_client
        if vc is None:
            return
        # Bot was disconnected (kicked or moved out): reset its state.
        if member.id == self.bot.user.id and after.channel is None:
            p = self.players.pop(member.guild.id, None)
            if p:
                p.queue.clear()
                p.current = None
                p._cancel_idle_timer()
            return
        # Everyone else left the channel: leave too.
        if before.channel == vc.channel and all(m.bot for m in vc.channel.members):
            await self.player(member.guild).stop()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
