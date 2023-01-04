import discord
from discord.ext import commands
from modules.economy import Economy
from modules.helpers import *

from modules.qrld import qrlnode

class GamblingHelpers(commands.Cog, name='QRL'):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.economy = Economy()

    @commands.command(
        brief=f"Gives you {DEFAULT_BET*B_MULT} QRL once every {B_COOLDOWN}hrs",
        usage="faucet", 
        aliases=['add', 'drip']
    )
    @commands.cooldown(1, B_COOLDOWN*3600, type=commands.BucketType.user)
    async def faucet(self, ctx: commands.Context, user: discord.Member=None):
        user = user.id if user else ctx.author.id
        user = self.client.get_user(user)
        amount = DEFAULT_BET*B_MULT
        self.economy.add_money(ctx.author.id, amount)
        embed = make_embed(
            title=user.name,
            description=(
                'Added **{:,}** QRL. Come back in {}hrs.'.format(amount,B_COOLDOWN)
            ),
            footer=discord.Embed.Empty
        )
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)        
        #await ctx.send(f"Added ${amount} QRL. Come back in {B_COOLDOWN}hrs")

    @commands.command(
        brief="How much QRL you or someone else has",
        usage="qrl *[@member]",
        aliases=['credits', 'money', 'q']
    )
    async def qrl(self, ctx: commands.Context, user: discord.Member=None):
        user = user.id if user else ctx.author.id
        user = self.client.get_user(user)
        profile = self.economy.get_entry(user.id)
        embed = make_embed(
            title=user.name,
            description=(
                'You have **{:,}** QRL in your account.'.format(profile[1])
            ),
            footer=discord.Embed.Empty
        )
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)
        
    @commands.command(
        brief=f"Deposit to your QRL account. Transfer QRL to this address to get more funds. Please run the sync command after a deposit.",
        usage="deposit",
        aliases=["buy", "d", "addr"]
    )
    async def deposit(self, ctx: commands.Context):
        user_id = ctx.author.id
        profile = self.economy.get_entry(user_id)
        qrl_addr = profile[2]
        last_sync = datetime.utcfromtimestamp(int(profile[3])).strftime("%Y-%m-%d %H:%M:%S +00:00")
        
        async def qr_code(**kwargs) -> discord.Message:
            qrl_node = qrlnode()
            qrl_node.create_qr(ctx.author.id, qrl_addr)
                           
            embed = make_embed(**kwargs)
            file = discord.File(f"{ctx.author.id}.png", filename=f"{ctx.author.id}.png")
            embed.set_image(url=f"attachment://{ctx.author.id}.png")
            msg: discord.Message = await ctx.send(file=file, embed=embed)
            return msg
        
        msg = await qr_code(
            title="Deposit method",
            description=(
                f"Transfer QRL to this address: {qrl_addr}.\nPlease run the *+sync* command after a deposit."
            )
        )
        os.remove(f'./{ctx.author.id}.png')
        
        #await ctx.send(f"Deposit method: transfer QRL to this address: {qrl_addr}. Last sync was on {last_sync}.")


        
            
    @commands.command(
        brief=f'Withdraw QRL from your QRLCasino account to a QRL wallet.',
        usage="withdraw [addr] *[amount]",
        aliases=["w"]
    )
    async def withdraw(self, ctx: commands.Context, dest_addr: str, amount_to_withdraw: int=-1, user: discord.Member=None):
        user_id = ctx.author.id      
        profile = self.economy.get_entry(user_id)

        user = user.id if user else ctx.author.id
        user = self.client.get_user(user)        
        if profile[1] > 0:
            if amount_to_withdraw <= 0:
                amount_to_withdraw = profile[1]
                
            if profile[1] >= amount_to_withdraw:
                msg = self.economy.withdraw(user_id, dest_addr, amount_to_withdraw)
                embed = make_embed(
                    title=user.name,
                    description=(msg),
                    footer=discord.Embed.Empty
                )
                embed.set_thumbnail(url=user.avatar_url)
                await ctx.send(embed=embed)  
        else:
            await ctx.send(f"No QRL to withdraw.")  

    @commands.command(
        brief=f'Sync your QRLCasino account with your QRL wallet.',
        usage="sync",
        aliases=["s"]
    )
    async def sync(self, ctx: commands.Context, user: discord.Member=None):
        user_id = ctx.author.id
        user = user.id if user else ctx.author.id
        user = self.client.get_user(user)
        await ctx.send(f"Sync started, trying to transfer QRL to the casino account. Please wait, this could take a couple of minutes") 
        msg = self.economy.sync(user_id)
        embed = make_embed(
            title=user.name,
            description=(msg),
            footer=discord.Embed.Empty
        )
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)      

def setup(client: commands.Bot):
    client.add_cog(GamblingHelpers(client))
