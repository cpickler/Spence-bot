import base64
import codecs

import discord
import guildwars2api
from discord.ext import commands
from guildwars2api.v1 import GuildWars2API as GW1
from guildwars2api.v2 import GuildWars2API as GW2

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
            print(user.token_info)
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

    @commands.command(pass_context=True, no_pm=True,aliases=['addguildrole'])
    @commands.has_permissions(administrator=True)
    async def addGuildRole(self, ctx, rname=None, gnum=None,):
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
                prompt += '\n ({num}) {tag:<6} {name}'.format(num=i, tag='['+g['tag']+']', name=g['guild_name'])

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
            result += '\n ({num}) {tag:<6} {name}'.format(num=i, tag='['+g['tag']+']', name=g['guild_name'])
            # Add guild role to the user
            rid = Db.get_guild_role(ctx.message.server.id, guilds[i])
            if rid is not None:
                role = discord.utils.get(ctx.message.server.roles, id=str(rid))
                await self.bot.add_roles(author, role)
        result += '\n```'
        await self.bot.say(result)

def setup(bot):
    bot.add_cog(GuildWars(bot))
