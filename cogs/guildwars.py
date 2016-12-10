from discord.ext import commands
import discord
from guildwars2api.v2 import GuildWars2API as GW2
from guildwars2api.v1 import GuildWars2API as GW1
import BotBase as Db

api = GW1()


def world_name(wid):
    for i in api.world_names.get():
        if i['id'] == str(wid):
            return i['name']
    return "Error"


class GuildWars:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def world(self, ctx):
        """
        Returns the world of the saved API key.
        """
        member = ctx.message.author
        tkn = Db.get_key(member.id)
        if tkn is None:
            await self.bot.say("Error! No api token saved for user {}.".format(member.mention))
        else:
            user = GW2(api_key=tkn)
            wid = user.account.get()["world"]
            wname = Db.get_world(wid)
            await self.bot.say('{member.mention} is on world: **{world}**.'.format(member=member, world=wname))

    @commands.command(pass_context=True)
    async def addKey(self, ctx, tkn):
        """
        Save your API token to the server.
        :param ctx: Message context to provide your Discord ID.
        :param tkn: Your API token in "quotes."
        :return: "Success!" or "Failed :("
        """
        uid = ctx.message.author.id
        msg = Db.add_key(int(uid), tkn)
        await self.bot.say(msg)

    @commands.command(pass_context=True)
    async def delKey(self, ctx):
        member = ctx.message.author
        uid = member.id
        result = Db.delete(uid)
        if result:
            await self.bot.say("Successfully removed API key for {}".format(member.mention))
        else:
            await self.bot.say("The api key for {} could not be deleted since it doesn't exist.")

    @commands.command(pass_context=True):
    async def addWorldRole(self, ctx, role):
        pass



def setup(bot):
    bot.add_cog(GuildWars(bot))
