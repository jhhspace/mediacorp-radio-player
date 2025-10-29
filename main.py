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

stations = {
    "987": "https://playerservices.streamtheworld.com/api/livestream-redirect/987FM_PREM.aac",
    "yes933": "https://playerservices.streamtheworld.com/api/livestream-redirect/YES933_PREM.aac",
    "class95": "https://playerservices.streamtheworld.com/api/livestream-redirect/CLASS95_PREM.aac",
    "love972": "https://playerservices.streamtheworld.com/api/livestream-redirect/LOVE972FM_PREM.aac",
    "capital958": "https://playerservices.streamtheworld.com/api/livestream-redirect/CAPITAL958FM_PREM.aac",
    "cna938": "https://playerservices.streamtheworld.com/api/livestream-redirect/938NOW_PREM.aac",
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
        "\n".join(stations.keys())
    )
    await ctx.send(help_text)

@bot.command()
async def play(ctx, station: str):
    station = station.lower()
    if station not in stations:
        await ctx.send(f"Station not found. Try one of the stations here:\n {'\n'.join(stations.keys())}")
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

    stream_url = stations[station]
    try:
        audio_source = FFmpegPCMAudio(
            stream_url,
            before_options=FFMPEG_OPTS["before_options"],
            options=FFMPEG_OPTS["options"],
        )
        vc.play(audio_source, after=lambda e: print("Stream ended:", e))
        await ctx.send(f"Now streaming **{station}** in **{voice_channel.name}**.")
    except Exception as e:
        await ctx.send(f"Error starting radio: `{type(e).__name__}: {e}`")

@bot.command(aliases=["leave", "dc"])
async def stop(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("Left VC")
    else:
        await ctx.send("I’m not in VC")


bot.run(TOKEN)
