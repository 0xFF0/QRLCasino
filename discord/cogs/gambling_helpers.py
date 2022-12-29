import discord
from discord.ext import commands
from modules.economy import Economy
from modules.helpers import *


class GamblingHelpers(commands.Cog, name='General'):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.economy = Economy()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def set(
        self,
        ctx: commands.Context,
        user_id: int=None,
        money: int=0,
        credits: int=0
    ):
        if money:
            self.economy.set_money(user_id, money)
        if credits:
            self.economy.set_credits(user_id, credits)


    @commands.command(
        brief="Shows the user with the most money",
        usage="leaderboard",
        aliases=["top", "l"]
    )
    async def leaderboard(self, ctx):
        entries = self.economy.top_entries(5)
        embed = make_embed(title='Leaderboard:', color=discord.Color.gold())
        for i, entry in enumerate(entries):
            embed.add_field(
                name=f"{i+1}. {self.client.get_user(entry[0]).name}",
                value='{:,} QRL'.format(entry[1]),
                inline=False
            )
        await ctx.send(embed=embed)

def setup(client: commands.Bot):
    client.add_cog(GamblingHelpers(client))
