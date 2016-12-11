from discord.ext import commands
import discord
# noinspection PyPep8Naming
from guildwars2api.v2 import GuildWars2API as GW2
# noinspection PyPep8Naming
from guildwars2api.v1 import GuildWars2API as GW1
import guildwars2api
import BotBase as Db
import base64
import codecs

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


# def is_valid_key(key):


# noinspection PyPep8Naming,PyPep8Naming,PyPep8Naming
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

    @commands.command(pass_context=True)
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

    @commands.command(pass_context=True)
    async def delKey(self, ctx):
        member = ctx.message.author
        uid = member.id
        result = Db.delete_user(uid)
        if result:
            await self.bot.say("Successfully removed API key for {}".format(member.mention))
        else:
            await self.bot.say("The api key for {} could not be deleted since it doesn't exist.")

    @commands.command(pass_context=True, no_pm=True)
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


def setup(bot):
    bot.add_cog(GuildWars(bot))
