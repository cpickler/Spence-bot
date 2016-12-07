from discord.ext import commands
import discord

import json
import sys

description="""ChrisPy-Bot"""


def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)

if __name__ == '__main__':
    bot = commands.Bot(command_prefix='!', description=description)