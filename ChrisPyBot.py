from discord.ext import commands

import discord

import json
import BotBase as Db

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


@bot.command(pass_context=True)
async def addserver(ctx):
    server = ctx.message.server
    result = Db.add_server(server.id, server.name)
    if result:
        msg = 'Server successfully added.'
    elif result is False:
        msg = 'Server succesfully updated.'
    elif result is None:
        msg = 'No changes made, server may already exist.'
    await bot.say(msg)

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
