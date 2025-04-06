from dotenv import load_dotenv
import os
import discord
from discord.ext import commands

token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    print('DISCORD_BOT_TOKEN is not set')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = '!', intents = intents)

@bot.event
async def on_ready():
    print(f'> Logined as {bot.user}!')

@bot.command()
async def get_location(ctx: commands.Context):
    await ctx.send('just testing bot command')

bot.run(token)