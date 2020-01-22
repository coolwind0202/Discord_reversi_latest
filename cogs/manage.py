import discord
from discord.ext import commands

def kifu(kifus):
    for i in kifus:
        yield i 

class ManageCog(commands.Cog):
    '''
    棋譜やエクステンションの再読み込みを行うコマンド類
    '''
    def __init__(self,bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def reload(self,ctx,name):
        self.bot.reload_extension("cogs."+name)
        await ctx.send("reloaded")

    @commands.is_owner()
    @commands.command()
    async def load_kifu(self,ctx):
        f = open("kifu.txt","r")
        tmp = f.readlines()
        f.close()

        self.bot.kifus = []

        for i in tmp:
            x = int(i.split(" ")[0])
            y = int(i.split(" ")[1])

            self.bot.kifus.append((x,y))

        self.bot.read_kifus = kifu(self.bot.kifus)
        await ctx.send("the kifu was loaded")

def setup(bot):
    bot.add_cog(ManageCog(bot))
