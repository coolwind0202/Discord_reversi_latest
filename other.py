import discord
from discord.ext import commands
import datetime
from cogs.rev_utils import draw_and_get_stones,can_put_to_dict,create_about,return_msg_content
from cogs.db import *

def get_four_end(board,member_1,member_2,size):
        tmp = [(0,0),(size-1,0),(size-1,size-1),(size-1,size-1)]
        list_for_return = []
        for elem in tmp:
            num = board[elem[0]][elem[1]]
            if num == 0:
                list_for_return.append(member_1.name)
            elif num == 1:
                list_for_return.append(member_2.name)
            else:
                list_for_return.append("空地")
        return list_for_return

class OtherCog(commands.Cog):
    '''
    その他のコマンドをまとめたコグ
    '''

    def __init__(self,bot):
        self.bot = bot

    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command()
    async def ping(self,ctx):
        await ctx.send("pong!")

    @commands.is_owner()
    @commands.command()
    async def set_prefix(self,ctx,prefix="."):
        await self.bot.change_presence(activity=discord.Game(name="オセロ"))
        await ctx.guild.me.edit(nick=f"Discord Reversi [{prefix}help]")

    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command(aliases=['retire','stop'])
    async def end(self,ctx):
        ID = ctx.author.id

        if ID not in self.bot.board_dict.keys():
            await ctx.send("まだ対局が始まっていません。")
            return

        manage_board = self.bot.board_dict[ID]
        players = manage_board.player_list
        print("player_list:",manage_board.player_list)
        player = players[1] if players[0] == ctx.author else players[0]
        black,white,all = draw_and_get_stones(manage_board,manage_board.size)

        await ctx.send(f"{ctx.author.mention} vs {player.mention} の対局を終了します。\n"\
                       f"{return_msg_content(black,white,all,manage_board)}")

        del self.bot.board_dict[ID]
        if player != self.bot.user and player != ctx.author:
            del self.bot.board_dict[player.id]
    
        await self.bot.system_msg.edit(embed=create_about(self.bot))

    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command(aliases=['i'])
    async def info(self,ctx):
        if ctx.author.id not in self.bot.board_dict.keys():
            manage_board = None
        else:
            manage_board = self.bot.board_dict[ctx.author.id]
            size = manage_board.size
            board = manage_board.board
            black,white,all = draw_and_get_stones(manage_board,size)
            path = f"{manage_board.player_list[1].id}.jpg"

        embed = discord.Embed(title=f"{ctx.author.display_name} さんの情報")

        got_data = get_user_info(ctx.author.id)
        if got_data is None:
            embed.add_field(name="過去の勝利数、対局数（勝率）",value="データがありません。")
            got_data = {}
        else:
            win = got_data.get("win_num",0)
            result = got_data.get("battle_num",0)

            rate = (win*100)//result if win > 0 else 0
            embed.add_field(name="過去の勝利数、対局数（勝率）",
                            value=f"**{win}** / **{result}** (**{rate}**%)")

            kifus = got_data.get("kifu","無し")
            if not kifus:
                kifus = "無し"
            embed.add_field(name="現在の棋譜",value=kifus)
        
        if manage_board:
            got_data = get_board_state(manage_board.player_list[1].id)
            embed.add_field(name="基本情報",
                            value=f"サーバー / **{self.bot.get_guild(int(got_data.get('guild_id'))).name}**\n"\
                              f"チャンネル / **{self.bot.get_channel(int(got_data.get('channel_id'))).name}**\n"\
                              f"対局相手 / **{self.bot.get_user(int(got_data.get(('enemy_id')))).name}**")
            embed.add_field(name="盤面の石の状況",value=f"黒:**{black}**個 / 白:**{white}**個 / 全体:**{all}**個",inline=False)

            tmp = get_four_end(board,manage_board.player_list[0],manage_board.player_list[1],size)

            embed.add_field(name="四隅の状況",value=f"左上:**{tmp[0]}**\n左下:**{tmp[1]}**\n右上:**{tmp[2]}**\n右下:**{tmp[3]}**",
                           inline=False)
            file = discord.File(f"images/{path}")
            embed.set_image(url=f"attachment://{path}")
            await ctx.send(file=file,embed=embed)
        else:
            embed.description = "まだ対局が開始していません。"
            await ctx.send(embed=embed)
    
    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command()
    async def about(self,ctx):
        await ctx.send(embed=create_about(self.bot))

    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command()
    async def now_bot_status(self,ctx):
        for manage_board in self.bot.board_dict.values():
            tmp = [self.bot.get_user(i).name for i in manage_board.player_list]
            print(tmp,manage_board.guild.name,">",manage_board.channel.name)
        print("---以下参加サーバーの情報---")
        for guild in self.bot.guilds:
            print(guild.name,"(",guild.id,")")
    
    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command()
    async def help(self,ctx):
        p = ctx.prefix
        description_ = "Discord ReversiはDiscord上でオセロをするためのbotです。\n"
        description_ += f"このサーバーのコマンドプレフィックスは「**{p}**」です。\n\n"
        description_ += "`TIPS:オセロBOTのニックネームの[.help]部分を書き換えると変更できます`"
    
        start = "メンションした相手と対局を開始します。\n相手は他のプレイヤーと対局中**でない**必要があります。\n"
        start += "botにメンションを送信すると対botの対局が開始されます。\n"
        start += f"例: `{p}start @user`\n"
        start += f"例: `{p}start @Discord Reversi [.help]#3269`\n\n"
    
        put = "既に対局が開始／再開している場合において、盤面の座標`(x,y)`に自分の石を配置します。\n"
        put += f"例: `{p}put 5 3`\n\n"
    
        retire = "既に対局が開始／再開している場合において、現在行っている対局を終了します。\n"
        retire += f"例: `{p}end`\n\n"
    
        about = "botの各情報を参照します。\n"
        about += f"例: `{p}about`\n\n"

        info = "自身の対局情報やユーザー情報を参照します。\n"
        info += f"例: `{p}info`\n\n"
    
        restart = "対局データが消失した場合に、メッセージ履歴から直前の盤面の復元を試みます。\n"
        restart += f"例: `{p}restart @user`\n\n"
    
        help_value = "もしこのhelpコマンドで解決しなければ、[公式サーバー](https://discord.gg/RvsHPvX)までお問合せください。\n"
        help_value += "実際に対局を試すこともできます。"
    
        embed = discord.Embed(title="Discord Reversi",description=description_,color=0xcc9966)
        embed.add_field(name=f"{p}start @メンション",value=start)
        embed.add_field(name=f"{p}put x y",value=put)
        embed.add_field(name=f"{p}end",value=retire)
        embed.add_field(name=f"{p}info",value=info)
        embed.add_field(name=f"{p}about",value=about)
        embed.add_field(name=f"{p}restart @メンション",value=restart)
        embed.add_field(name="質問・要望・不具合報告",value=help_value)
    
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(OtherCog(bot))
