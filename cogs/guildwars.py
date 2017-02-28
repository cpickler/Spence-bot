import base64
import codecs
import os
from urllib.parse import quote
import datetime
import iso8601
import random


import discord
import guildwars2api
from discord.ext import commands
from guildwars2api.v1 import GuildWars2API as GW1
from guildwars2api.v2 import GuildWars2API as GW2
import aiohttp
import asyncio
import async_timeout
import json

import BotBase as Db

api1 = GW1()
api2 = GW2()


def world_name(wid):
    for i in api1.world_names.get():
        if i['id'] == str(wid):
            return i['name']
    return "Error"


def chat_to_id(chat):
    b64 = base64.b64decode(chat)[2:][::-1]
    hex_string = '0x' + str(codecs.encode(b64, 'hex'))[-5:-1]
    return int(hex_string, 0)


async def auth_fetch(session, url, tkn):
    with async_timeout.timeout(10):
        head = {'Authorization': 'Bearer {0}'.format(tkn)}
        async with session.get(url, headers=head) as response:
            return await response.text()

async def acct_inv_main(loop, tkn):
    user = GW2(api_key=tkn)
    chars = user.characters.get()
    tasks = []
    item_dict = dict()
    async with aiohttp.ClientSession(loop=loop) as session:
        for c in chars:
            task = asyncio.ensure_future(auth_fetch(session, 'https://api.guildwars2.com/v2/characters/{0}/inventory/'.format(c), tkn))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        for char in responses:
            char_inv = json.loads(char)
            for bag in char_inv['bags']:
                if bag is not None:
                    for item in bag['inventory']:
                        if item is not None:
                            item_dict[item['id']] = item_dict.get(item['id'], 0) + item['count']
        for item in user.bank.get():
            if item is not None:
                item_dict[item['id']] = item_dict.get(item['id'], 0) + item['count']
        return item_dict


def acct_inv(tkn):
    loop = asyncio.get_event_loop()
    inv = loop.run_until_complete(acct_inv_main(loop, 'C53020FE-F672-514F-B5C9-D7C209927B91CC796525-2980-4FD6-8B85-3C9D96BFCD4E'))
    return inv


class GuildWars:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def world(self, ctx):
        """
        Returns the world of the saved API key.
        """
        member = ctx.message.author
        server = ctx.message.server
        tkn = Db.get_key(member.id)
        if tkn is None:
            await self.bot.say("Error! No api token saved for user {}.".format(member.mention))
        else:
            user = GW2(api_key=tkn)
            wid = user.account.get()["world"]
            wname = Db.get_world(wid)
            # Check to see if the world has a role on the server
            rid = Db.get_world_role(server.id, wid)
            if rid is not None:
                role = discord.utils.get(server.roles, id=str(rid))
                await self.bot.add_roles(member, role)
            await self.bot.say('{member.mention} is on world: **{world}**.'.format(member=member, world=wname))

    @commands.command(pass_context=True, aliases=['addkey'])
    async def addKey(self, ctx, tkn):
        """
        Save your API token to the server.
        :param ctx: Message context to provide your Discord ID.
        :param tkn: Your API token in "quotes."
        :return: "Success!" or "Failed :("
        """
        # Check to see if the message is a PM, delete if not
        if ctx.message.server is not None:
            await self.bot.delete_message(ctx.message)
            await self.bot.send_message(ctx.message.author, 'API Keys can only be added in PMs.  '
                                                            'Reply with "!addKey <your api key>" to add your key.')
        else:
            try:
                user = GW2(api_key=tkn)
                user.token_info.get()
                uid = ctx.message.author.id
                msg = Db.add_key(int(uid), tkn)
            except guildwars2api.base.GuildWars2APIError:
                msg = "Invalid API key, please try again."
            await self.bot.say(msg)

    @commands.command(pass_context=True, aliases=['delkey'])
    async def delKey(self, ctx):
        member = ctx.message.author
        uid = member.id
        result = Db.delete_user(uid)
        if result:
            await self.bot.say("Successfully removed API key for {}".format(member.mention))
        else:
            await self.bot.say("The api key for {} could not be deleted since it doesn't exist.")

    @commands.command(pass_context=True, no_pm=True, aliases=['addworldrole'])
    @commands.has_permissions(administrator=True)
    async def addWorldRole(self, ctx, rname):

        sid = ctx.message.server.id
        wid = Db.get_world_id(rname)
        role = discord.utils.get(ctx.message.server.roles, name=rname)
        if role is None:
            await self.bot.say('No role named "{}", verify the role exists, or check your spelling.'.format(rname))
        else:
            Db.add_world_role(sid, role.id, wid)
            await self.bot.say("Role **{}** successfully linked to world.".format(rname))

    @commands.command(pass_context=True, no_pm=True, aliases=['addguildrole'])
    @commands.has_permissions(administrator=True)
    async def addGuildRole(self, ctx, rname=None, gnum=None, ):
        """
        Link a guild and a role together. You must have permissions to use this command.
        :param role: @mention or name of the role to add.
        :return: Series of prompts to add the role.
        """
        author = ctx.message.author
        user = GW2(api_key=Db.get_key(author.id))
        guilds = user.account.get()['guilds']

        if rname is None and gnum is None:
            prompt = 'Which guild to add? \n```'
            for i in range(len(guilds)):
                g = api1.guild_details.get(guild_id=guilds[i])
                prompt += '\n ({num}) {tag:<6} {name}'.format(num=i, tag='[' + g['tag'] + ']', name=g['guild_name'])

            prompt += '\n\n Reply with eg. !addGuildRole "Awesome Guild" 1```'
            await self.bot.say(prompt)

        elif rname is not None and gnum is not None:
            role = discord.utils.get(ctx.message.server.roles, name=rname)
            gid = guilds[int(gnum)]
            guild = api1.guild_details.get(guild_id=gid)
            Db.add_guild_role(gid, int(role.id), int(ctx.message.server.id))
            await self.bot.say("Role successfully added.")

    @commands.command(pass_context=True)
    async def guilds(self, ctx):
        """
        Returns a list of guild memberships for the user.
        """
        author = ctx.message.author
        user = GW2(api_key=Db.get_key(author.id))
        guilds = user.account.get()['guilds']
        result = '{} is in guilds:\n```'.format(author.mention)
        for i in range(len(guilds)):
            g = Db.get_add_guild(guilds[i])
            result += '\n ({num}) {tag:<6} {name}'.format(num=i, tag='[' + g['tag'] + ']', name=g['guild_name'])
            # Add guild role to the user
            rid = Db.get_guild_role(ctx.message.server.id, guilds[i])
            if rid is not None:
                role = discord.utils.get(ctx.message.server.roles, id=str(rid))
                await self.bot.add_roles(author, role)
        result += '\n```'
        await self.bot.say(result)

    @commands.command(pass_context=True)

    async def profile(self, ctx):
        """
        Return the account information for a given user.
        Automatically  parses the GW2 Efficiency link for character sharing. The link will be broken if there are no
         characters shared.
        This requires the progression API permissions to function properly.
        """
        author = ctx.message.author
        user = GW2(api_key=Db.get_key(author.id))
        acct_info = user.account.get()
        try:
            # embed setup
            acct_name = acct_info['name']
            url = "https://gw2efficiency.com/account/characters/" + quote(acct_name)
            embed = discord.Embed(title=acct_name, url=url)

            # add World for embed
            wid = acct_info["world"]
            wname = Db.get_world(wid)
            embed.add_field(name='World', value=wname, inline=True)

            # Add AR to embed
            # ar = get_agony(Db.get_key(author.id), char_name)
            # embed.add_field(value='AR: {}'.format(str(ar)), inline=True, name='Agony Resistance')

            # Add WvW rank
            wvw_rank = user.account.get()['wvw_rank']
            embed.add_field(name='WvW Rank', value=wvw_rank, inline=True)

            # Add account age
            created = iso8601.parse_date(acct_info['created'])
            date = created.strftime('%d %b %Y')
            embed.add_field(name='Created on', value=date, inline=True)

            # Send out the embed
            await self.bot.say(embed=embed)
        except guildwars2api.base.GuildWars2APIError:
            await self.bot.say('There was an error while processing your request.')

    @commands.command(pass_context=True, aliases=['defchar'])
    async def defaultCharacter(self, ctx, cname=None):
        user = GW2(api_key=Db.get_key(ctx.message.author.id))
        result = False
        if cname is None:
            await self.bot.say('Which character to use?\n' + char_output(Db.get_key(ctx.message.author.id)) +
                               '\nEg: `!defaultCharacter 1` to set character `(1)`')
        else:
            char_list = user.characters.get()
            try:
                cint = int(cname) - 1
                # get character name
                cname = char_list[cint]
            except IndexError:
                await self.bot.say('option must be between 1 and {max}.'.format(max=len(char_list)))
            except ValueError:
                # check character name is valid
                if cname not in char_list:
                    await self.bot.say('Character {name} does not exist. Spelling and capitalization '
                                       'does matter.'.format(name=cname))
                    cname = None
        if cname is not None:
            result = Db.set_default_character(ctx.message.author.id, cname)
        if result is True:
            await self.bot.say('Default character successfully set to: {}'.format(cname))

    @commands.command(pass_context=True, aliases=['chars'])
    async def characters(self, ctx):
        author = ctx.message.author
        tkn = Db.get_key(author.id)
        await self.bot.say(char_output(tkn))

    @commands.command()
    async def quaggan(self, name: str = None):
        if name is None:
            quaggans = api2.quaggans.get()
            name = random.choice(quaggans)
        try:
            url = api2.quaggans.get(id=name)['url']
        except guildwars2api.base.GuildWars2APIError:
            url = api2.quaggans.get(id='404')['url']

        # Create quaggan embed
        embed = discord.Embed(url=url)
        embed.set_image(url=url)

        # Set embed color
        quaggan_color = {'girl': discord.Colour.magenta()}
        embed.color = quaggan_color.get(name, discord.Colour.blue() )
        await self.bot.say(embed=embed)

    @commands.command(pass_context=True, aliases=['setnick', 'nick'], no_pm=True)
    async def setNickname(self, ctx, member=None):        if member is not None:
            mentioned = ctx.message.mentions
            if len(mentioned) == 0:
                await self.bot.say('The mentioned users are invalid, or may not be mentions.', delete_after=30)
                return
        elif member is None:
            mentioned = [ctx.message.author]

        for mention in mentioned:
            tkn = Db.get_key(mention.id)
            user = GW2(api_key=tkn)
            name = user.account.get()['name']
            try:
                await self.bot.change_nickname(ctx.message.author, name)
            except discord.errors.Forbidden:
                await self.bot.say('Member {mention} can not be added. The bot may not have permissions to change '
                                   'nicknames or, the bot may not be able to change the nickname of the '
                                   'specified member.'.format(mention=mention.mention), delete_after=30)


def get_agony(tkn, char_name):
    """
    Get the AR for a character, returning the max possible AR between the two weapon sets.
    Disregards aquatic weapons and breathers.
    :param tkn: GW2 API Token
    :param char_name: Full character name
    :return: int : Total AR
    """
    user = GW2(api_key=tkn)
    equipment = user.characters.get(id=char_name)['equipment']
    infusions = []
    aslots = []
    bslots = []
    agony = 0
    a_agony = 0
    b_agony = 0
    # Get the agony for each load-out
    for item in equipment:
        if 'Aquatic' not in item['slot']:
            if item['slot'] in ('WeaponA1', 'WeaponA2'):
                i = item.get('infusions', None)
                if i is not None:
                    aslots += i
            elif item['slot'] in ('WeaponB1', 'WeaponB2'):
                i = item.get('infusions', None)
                if i is not None:
                    bslots += i
            else:
                i = item.get('infusions', None)
                if i is not None:
                    infusions += i
    for infusion in infusions:
        agony += Db.get_agony_resistance(infusion)
    for infusion in aslots:
        a_agony += Db.get_agony_resistance(infusion)
    for infusion in bslots:
        b_agony += Db.get_agony_resistance(infusion)
    # Use the highest load-out AR to calculate total AR
    if a_agony >= b_agony:
        agony += a_agony
    else:
        agony += b_agony
    return agony

    async def li(selfself, ctx):
        author = ctx.message.author
        user = GW2(api_key=Db.get_key(author.id))



def setup(bot):
    bot.add_cog(GuildWars(bot))


def char_output(tkn):
    user = GW2(api_key=tkn)
    chars = user.characters.get_all()
    output = '```\n'
    i = 1
    for char in chars:
        line = '({num}) {name} : Level {level} {race} {prof}.\n'.format(num=i, name=char['name'],
                                                                        level=char['level'], race=char['race'],
                                                                        prof=char['profession'])
        output += line
        i += 1
    output += '```'
    return output


if __name__ == '__main__':
    print(get_agony(os.environ['gw2_token'], 'Neth Yaulë'))
