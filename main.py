import os
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from dotenv import load_dotenv

load_dotenv()
TOKEN: str = os.getenv("DISCORD_TOKEN") or ""

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

station_info = {
    "987": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/987FM_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1748749187/mediacorp/mel/image/2025-06/987_kv_final_2.jpg",
    },
    "yes933": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/YES933_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1740634264/mediacorp/mel/image/2025-02/933_kv_5120x2880.jpg",
    },
    "class95": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/CLASS95_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1745809388/mediacorp/mel/image/2025-04/c95widget1920x1080lowres.jpg",
    },
    "love972": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/LOVE972FM_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1740634184/mediacorp/mel/image/2025-02/972_kv_final_revised.jpg",
    },
    "capital958": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/CAPITAL958FM_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1752480782/mediacorp/mel/image/2025-07/capital958_kv_final_v2.jpg",
    },
    "cna938": {
        "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/938NOW_PREM.aac",
        "image": "https://onecms-res.cloudinary.com/image/upload/v1740639429/mediacorp/mel/image/2025-02/cna938_kv_ml_5120x2880.jpg",
    },
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

def get_user_voice_channel(ctx):
    return getattr(getattr(ctx.author, "voice", None), "channel", None)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def cmds(ctx):
    help_text = (
        "**Available commands:**\n"
        "`!play <station>` - Play a radio station in your voice channel.\n"
        "`!stop` - Disconnect the bot from the voice channel.\n\n"
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

        station_image = station_info[station]["image"]
        if station_image:
            embed.set_image(url=station_image)
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Error starting radio: `{type(e).__name__}: {e}`")

@bot.command(aliases=["leave", "dc"])
async def stop(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("Stopped radio and disconnected.")
    else:
        await ctx.send("I’m not in VC")

bot.run(TOKEN)
