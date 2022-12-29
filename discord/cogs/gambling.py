import random

from discord.ext import commands
from discord.ext.commands.errors import BadArgument
from modules.economy import Economy
from modules.helpers import *
import shutil
import discord


class Gambling(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.economy = Economy()

    def check_bet(
        self,
        ctx: commands.Context,
        bet: int=DEFAULT_BET,
    ):
        bet = int(bet)
        if bet <= 0:
            raise commands.errors.BadArgument()
        current = self.economy.get_entry(ctx.author.id)[1]
        if bet > current:
            raise InsufficientFundsException(current, bet)

    @commands.command(
        brief="Flip a coin\nBet must be greater than $0",
        usage=f"flip [heads|tails] *[bet- default=${DEFAULT_BET}]",
    )
    async def flip(
        self,
        ctx: commands.Context,
        choice: str,
        bet: int=DEFAULT_BET
    ):
        self.check_bet(ctx, bet)
        choices = {'heads': True, 'tails': False}
        choice = choice.lower()
        if choice in choices.keys():
            casinoChoice = random.choice(list(choices.keys()))
            if casinoChoice == choice:
                msg_title = "You won!"
                msg_desc = 'You won ' + str(bet) + ' QRL!'
                self.economy.add_money(ctx.author.id, bet)
            else:
                msg_title = "You lost."
                msg_desc = 'You lost ' + str(bet) + ' QRL.'
                self.economy.add_money(ctx.author.id, bet * -1)
                
            async def flip_img(**kwargs) -> discord.Message:
                shutil.copyfile(f"modules/flip/{casinoChoice}.png",f"{ctx.author.id}.png")
                               
                embed = make_embed(**kwargs)
                file = discord.File(f"{ctx.author.id}.png", filename=f"{ctx.author.id}.png")
                embed.set_image(url=f"attachment://{ctx.author.id}.png")
                msg: discord.Message = await ctx.send(file=file, embed=embed)
                return msg
                
            msg = await flip_img(
                title=msg_title,
                description=msg_desc
            )
            os.remove(f'./{ctx.author.id}.png')
        else:
            raise BadArgument()

    @commands.command(
        brief="Roll 1 die\nBet must be greater than $0",
        usage=f"roll [guess:1-6] *[bet- default=${DEFAULT_BET}]"
    )
    async def roll(
        self,
        ctx: commands.Context,
        choice: int,
        bet: int=DEFAULT_BET
    ):
        self.check_bet(ctx, bet)
        choices = range(1,7)
        if choice in choices:
            casinoChoice = random.choice(choices)
            if casinoChoice == choice:
                msg_title = "You won!"
                msg_desc = 'You won ' + str(bet*6) + ' QRL!'
                self.economy.add_money(ctx.author.id, bet*6)
            else:
                msg_title = "You lost."
                msg_desc = 'You lost ' + str(bet) + ' QRL.'
                self.economy.add_money(ctx.author.id, bet * -1)
                
            async def dice_img(**kwargs) -> discord.Message:
                shutil.copyfile(f"modules/dices/{casinoChoice}.png",f"{ctx.author.id}.png")
                               
                embed = make_embed(**kwargs)
                file = discord.File(f"{ctx.author.id}.png", filename=f"{ctx.author.id}.png")
                embed.set_image(url=f"attachment://{ctx.author.id}.png")
                msg: discord.Message = await ctx.send(file=file, embed=embed)
                return msg
                
            msg = await dice_img(
                title=msg_title,
                description=msg_desc
            )
            os.remove(f'./{ctx.author.id}.png')
            
        else:
            raise BadArgument()

def setup(client: commands.Bot):
    client.add_cog(Gambling(client))
