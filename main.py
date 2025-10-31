import os
import asyncio
import requests
import xml.etree.ElementTree as ET
import urllib.parse

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv
load_dotenv()

TOKEN: str = os.getenv("DISCORD_TOKEN") or ""

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
guild_playback_state: dict[int, dict] = {}

station_info = {
    "987": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/987FM_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1748749187/mediacorp/mel/image/2025-06/987_kv_final_2.jpg",
        "mount": "987FMAAC",
    },
    "yes933": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/YES933_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1740634264/mediacorp/mel/image/2025-02/933_kv_5120x2880.jpg",
        "mount": "YES933AAC",
    },
    "class95": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/CLASS95_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1745809388/mediacorp/mel/image/2025-04/c95widget1920x1080lowres.jpg",
        "mount": "CLASS95AAC",
    },
    "love972": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/LOVE972FM_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1740634184/mediacorp/mel/image/2025-02/972_kv_final_revised.jpg",
        "mount": "LOVE972FMAAC",
    },
    "capital958": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/CAPITAL958FM_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1752480782/mediacorp/mel/image/2025-07/capital958_kv_final_v2.jpg",
        "mount": "CAPITAL958FMAAC",
    },
    "cna938": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/938NOW_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1740639429/mediacorp/mel/image/2025-02/cna938_kv_ml_5120x2880.jpg",
        "mount": "938NOWAAC",
    },
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

def get_user_voice_channel(ctx: commands.Context):
    return getattr(getattr(ctx.author, "voice", None), "channel", None)

def build_nowplaying_url(mount_name: str) -> str:
    return (
        "https://np.tritondigital.com/public/nowplaying"
        f"?mountName={mount_name}&numberToFetch=1&eventType=track"
    )

def fetch_now_playing_for_mount(mount_name: str):
    if not mount_name:
        return (None, None)

    url = build_nowplaying_url(mount_name)

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception:
        return (None, None)

    try:
        root = ET.fromstring(r.text)
    except ET.ParseError:
        return (None, None)

    latest = root.find("nowplaying-info")
    if latest is None:
        return (None, None)

    title = None
    artist = None
    for prop in latest.findall("property"):
        n = prop.get("name")
        v = (prop.text or "").strip()
        if n == "cue_title":
            title = v
        elif n == "track_artist_name":
            artist = v

    return (title, artist)

def fetch_track_metadata(title: str | None, artist: str | None):
    if not title or not artist:
        return None

    base_url = "https://livetrack.melisten.sg/api/search"
    query = (
        "title=" + urllib.parse.quote(title) +
        "&artist=" + urllib.parse.quote(artist)
    )
    url = f"{base_url}?{query}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception:
        return None

    try:
        data = r.json()
    except Exception:
        return None

    info = data.get("data") or {}
    return {
        "title": info.get("title"),
        "artist": info.get("artist"),
        "albumart": info.get("albumart"),
        "spotify_url": info.get("spotify_url"),
    }

async def clear_presence():
    """Reset bot presence to nothing."""
    try:
        await bot.change_presence(activity=None, status=None)
    except Exception as e:
        print(f"[warn] failed to clear presence: {e}")

async def update_presence_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():
        active_guild_ids = list(guild_playback_state.keys())

        presence_string = None

        for guild_id in active_guild_ids:
            state = guild_playback_state.get(guild_id)
            if not state:
                continue

            station_key = state.get("station")
            last_track_string = state.get("last_track_string")

            if not station_key:
                continue

            station_meta = station_info.get(str(station_key), {})
            mount = station_meta.get("mount")
            if not mount:
                continue

            title, artist = fetch_now_playing_for_mount(mount)
            if not title and not artist:
                continue

            station_label = station_key.upper()
            if artist:
                track_string = f"{station_label}: {title} — {artist}"
            else:
                track_string = f"{station_label}: {title}"

            if track_string != last_track_string:
                state["last_track_string"] = track_string

            if not presence_string:
                presence_string = track_string

        if presence_string:
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=presence_string
            )
            try:
                await bot.change_presence(activity=activity)
            except Exception as e:
                print(f"[warn] failed to set presence: {e}")
        else:
            await clear_presence()

        await asyncio.sleep(20)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(update_presence_loop())

@bot.command()
async def cmds(ctx):
    help_text = (
        "**Available commands:**\n"
        "`!play <station>` - Play a radio station in your voice channel.\n"
        "`!stop` - Disconnect the bot from the voice channel.\n"
        "`!nowplaying` / `!np` - Show the current track.\n\n"
        "**Available stations:**\n" +
        "\n".join(station_info.keys())
    )
    await ctx.send(help_text)

@bot.command()
async def play(ctx, station: str):
    station = station.lower()
    if station not in station_info:
        await ctx.send(
            "Station not found. Try one of the stations here:\n " +
            "\n".join(station_info.keys())
        )
        return

    voice_channel = get_user_voice_channel(ctx)
    if not voice_channel:
        await ctx.send("You need to be in a VC.")
        return

    if ctx.voice_client and ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)
        vc = ctx.voice_client
    elif not ctx.voice_client:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    if vc.is_playing():
        vc.stop()

    stream_url = station_info[station]["url"]

    try:
        audio_source = FFmpegPCMAudio(
            stream_url,
            before_options=FFMPEG_OPTS["before_options"],
            options=FFMPEG_OPTS["options"],
        )
        vc.play(audio_source, after=lambda e: print("Stream ended:", e))

        embed = discord.Embed(
            title=f"Now Streaming: {station}",
            description=f"Playing in **{voice_channel.name}**",
            color=discord.Color.green(),
        )

        station_image = station_info[station].get("image")
        if station_image:
            embed.set_image(url=station_image)
        await ctx.send(embed=embed)

        guild_playback_state[ctx.guild.id] = {
            "station": station,
            "voice_channel_id": voice_channel.id,
            "last_track_string": None,
        }

    except Exception as e:
        await ctx.send(f"Error starting radio: `{type(e).__name__}: {e}`")

@bot.command(aliases=["leave", "dc"])
async def stop(ctx):
    vc = ctx.voice_client
    if vc:
        guild_playback_state.pop(ctx.guild.id, None)
        await vc.disconnect()
        await ctx.send("Stopped radio and disconnected.")

        if not guild_playback_state:
            await clear_presence()
    else:
        await ctx.send("I’m not in VC")

class SpotifyView(discord.ui.View):
    def __init__(self, spotify_url: str | None):
        super().__init__()
        if spotify_url:
            self.add_item(
                discord.ui.Button(
                    label="Open in Spotify",
                    url=spotify_url,
                    style=discord.ButtonStyle.link,
                )
            )
        else:
            self.add_item(
                discord.ui.Button(
                    label="Open in Spotify",
                    style=discord.ButtonStyle.gray,
                    disabled=True
                )
            )

@bot.command(aliases=["np"])
async def nowplaying(ctx):
    state = guild_playback_state.get(ctx.guild.id)
    if not state:
        await ctx.send("Nothing is currently playing in this server.")
        return

    station_key = state.get("station")
    if not station_key:
        await ctx.send("No station is registered for this server.")
        return

    st_meta = station_info.get(station_key, {})
    mount = st_meta.get("mount")
    if not mount:
        await ctx.send("This station doesn't support now playing info yet.")
        return

    title, artist = fetch_now_playing_for_mount(mount)
    if not title and not artist:
        await ctx.send("Couldn't fetch now playing info right now 😭")
        return

    extra = fetch_track_metadata(title, artist)
    spotify_url = None
    albumart = None
    if extra:
        spotify_url = extra.get("spotify_url")
        albumart = extra.get("albumart")

    station_label = station_key.upper()
    if title and artist:
        header_line = f"{station_label}: {title} — {artist}"
    elif title:
        header_line = f"{station_label}: {title}"
    else:
        header_line = f"{station_label}"

    desc_lines = []
    if title:
        desc_lines.append(f"**Title:** {title}")
    if artist:
        desc_lines.append(f"**Artist:** {artist}")
    desc = "\n".join(desc_lines) if desc_lines else "Currently playing"

    embed = discord.Embed(
        title=header_line,
        description=desc,
        color=discord.Color.blurple(),
    )

    if albumart:
        embed.set_thumbnail(url=albumart)

    view = SpotifyView(spotify_url)
    await ctx.send(embed=embed, view=view)

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not set in environment")
bot.run(TOKEN)
