import discord
from discord.ext import commands
import datetime
from io import BytesIO
from PIL import Image,ImageDraw
import re

from cogs.rev_utils import draw_and_get_stones,can_put_to_dict,create_about
from cogs.db import *

async def board_check(bot,message,member1,member2):
    '''
    messageのあったchannelから履歴を取得し、もし盤面に該当する画像があればそれから
    盤面の復元を試みます。
    '''

    async for msg in message.channel.history(limit=100):
        if msg.author == bot.user and msg.embeds and msg.embeds[0].description:
            tmp = msg.embeds[0].description

            if not all(m.mention in tmp for m in [member1,member2]):
                continue

            mem1_mention = tmp.find(member1.mention)
            mem2_mention = tmp.find(member2.mention)

            img_content = await msg.attachments[0].read()
            img_tmp = BytesIO(img_content)
            img = Image.open(img_tmp).convert("RGB")

            if img.width == 400:
                size = 6
            else:
                size = 8
            
            board = [[None for i in range(size)] for n in range(size)]
            for i in range(size):
                for n in range(size):
                    #一つ45×45ピクセル。空白は14×59ピクセル。
                    x = 60 + n*58
                    y = 60 + i*58

                    pixel = img.getpixel((x,y))
                    if pixel == (0,0,0):
                        board[i][n] = 1
                    elif pixel == (255,255,255):
                        board[i][n] = 0
                    else:
                        board[i][n] = None
            img.close()
            members = [member1 if mem1_mention > mem2_mention else member2]
            if members[0] == member2:
                members.append(member1)
            else:
                members.append(member2)
            
            n = re.search(r"（(.)）",tmp)
            if n.group(1) == "黒":
                return_team = 1
                return_member = members[0]
            else:
                return_team = 0
                return_member = members[1]

            return size,return_team,return_member,board
    else:
        await message.channel.send("盤面の復元を試みましたが、過去100件以内に該当するメッセージが見つかりませんでした。")
        return

class Manage_board:
    def __init__(self,author,member,**kwargs):
        self.player_list = [member,author]
        
        self.guild = kwargs.get("guild",None)
        self.channel = kwargs.get("channel",None)
        self.team = kwargs.get("team",1)
        self.now_player = self.player_list[self.team]
        self.passer = None
        self.created_at = datetime.datetime.now()
        self.can_put = {}
        self.size = kwargs.get("size",8)
        self.count = 0


        self.board = kwargs.get("board",[[None for i in range(self.size)] for n in range(self.size)])

        if "board" not in kwargs.keys():
            if self.size == 8:
                self.board[3][4] = self.board[4][3] = 1
                self.board[3][3] = self.board[4][4] = 0
            else:
                self.board[2][3] = self.board[3][2] = 1
                self.board[3][3] = self.board[2][2] = 0

class StartCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.guild_only()
    @commands.cooldown(1,5.0,type=commands.BucketType.user)
    @commands.command(aliases=['s'])
    async def start(self,ctx,member:discord.Member,size=8):
        await self.bot.wait_until_ready()

        ID = ctx.author.id

        if ID in self.bot.board_dict.keys():
            manage_board = self.bot.board_dict[ID]
            player_1 = manage_board.player_list[0].name
            player_2 = manage_board.player_list[1].name

            await ctx.send(f"{player_1} 対 {player_2} による対局が行われているため、開始できません。")
            return

        if member.id in self.bot.board_dict.keys() and member != self.bot.user:
            manage_board = self.bot.board_dict[member.id]
            player_1 = manage_board.player_list[0].name
            player_2 = manage_board.player_list[1].name

            await ctx.send(f"対戦相手は{player_1} 対 {player_2}で対局しているため、開始できません。")
            return

        if size != 6:
            size = 8

        manage_board = Manage_board(ctx.author,member,size=size,channel=ctx.message.channel,
                                    guild=ctx.message.guild)

        self.bot.board_dict[ctx.author.id] = manage_board
        if member != self.bot.user:
            self.bot.board_dict[member.id] = manage_board

        
        start_board_state(ctx.author.id, member.id, size, ctx.message.channel.id,
                        ctx.message.guild.id)


        board = manage_board.board
        draw_and_get_stones(manage_board,size)
        can_put_to_dict(manage_board,board,1,size)
    
        reply = f"__初手：{ctx.author.mention} （黒）__\n"
        reply += f"`{ctx.prefix}put x y`で自分の石を置くことができます。"
    
        embed = discord.Embed(title="新規対局",description=reply,color=0x00ff00)
        await ctx.send(file=discord.File(f"images/{ctx.author.id}.jpg"),embed=embed)
        await self.bot.system_msg.edit(embed=create_about(self.bot))

    @commands.guild_only()
    @commands.cooldown(1,5.0,type=commands.BucketType.user)
    @commands.command()
    async def restart(self,ctx,member:discord.Member):
        if ctx.author.id in self.bot.board_dict.keys() or member in self.bot.board_dict.keys():
            await ctx.send("既に対局が開始しています。\n"\
                           "このコマンドは対局が異常終了した際に使用してください。")
            return

        size,team,leader,board = await board_check(self.bot,ctx.message,ctx.author,member)
        
        sub = ctx.author if leader != ctx.author else member
        manage_board = Manage_board(leader,sub,team=team,board=board,size=size,
                                    channel=ctx.message.channel,guild=ctx.message.guild)
    
        self.bot.board_dict[ctx.author.id] = manage_board
        if member != self.bot.user:
            self.bot.board_dict[member.id] = manage_board

        start_board_state(ctx.author.id, member.id, size, ctx.message.channel.id,ctx.message.guild.id)
       

        write_user_info(ctx.author.id,board_num=268959744,enemy=member.id,
                        channel=ctx.message.channel.id,guild=ctx.message.guild.id)
        write_user_info(member.id,board_num=135266304,enemy=ctx.author.id,
                        channel=ctx.message.channel.id,guild=ctx.message.guild.id)

        board = manage_board.board
        draw_and_get_stones(manage_board,size)
        can_put_to_dict(manage_board,board,team)

        if member == self.bot.user:
            reply = f"__再開：{ctx.author.mention} （{['白','黒'][team]}）__\n"
        else:
            reply = f"__再開：{leader.mention} （{['白','黒'][team]}）__\n"

        reply += "\nrestartコマンドによる再起動を行いました。\n仕様上、開始時刻、手数は維持されていません。"

        embed = discord.Embed(title="対局再開",description=reply,color=0x00ff00)
        await ctx.send(file=discord.File(f"images/{leader.id}.jpg"),embed=embed)


def setup(bot):
    bot.add_cog(StartCog(bot))
