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
    async def world(self, ctx, tkn):
        """
        Returns the world of the provided API key.
        :param tkn: Your API key in quotes.
        """
        # TODO Change to use the API key saved
        member = ctx.message.author
        user = GW2(api_key=tkn)
        wid = user.account.get()["world"]
        wname = Db.get_world(wid)
        await self.bot.say('{member.mention} is on world: **{world}**.'.format(member=member, world=wname))

    @commands.command(pass_context=True)
    async def addkey(self, ctx, tkn):
        """
        Save your API token to the server.
        :param ctx: Message context to provide your Discord ID.
        :param tkn: Your API token in "quotes."
        :return: "Success!" or "Failed :("
        """
        uid = ctx.message.author.id
        msg = Db.add_key(int(uid), tkn)
        await self.bot.say(msg)


def setup(bot):
    bot.add_cog(GuildWars(bot))
