from discord.ext import commands
import discord

import json
import sqlalchemy

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
    sql_url = credentials['sql_url']

    # engine = sqlalchemy.create_engine(sql_url)

    for extension in extensions:
        bot.load_extension(extension)

    bot.run(token)
