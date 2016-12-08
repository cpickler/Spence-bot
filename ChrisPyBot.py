from discord.ext import commands
import discord

import json
import sys
import asyncio
import gw2api.v2

description="""ChrisPy-Bot"""


extensions = [
    'cogs.guildwars'
]

bot = commands.Bot(command_prefix='!', description=description)


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')


def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)

if __name__ == '__main__':
    credentials = load_credentials()
    token = credentials['token']

    for extension in extensions:
        bot.load_extension(extension)

    bot.run(token)
