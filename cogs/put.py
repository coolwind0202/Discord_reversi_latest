import discord
from discord.ext import commands
from cogs.rev_utils import draw_and_get_stones,can_put_to_dict
from cogs.rev_utils import return_msg_content,can_put_for_bot
import datetime
import os
from cogs.db import *
import copy

#botは自身からのメンションを受け取ったとき、それを自身の番が来たと解釈し、そのメッセージに
#含まれるメンションからリーダーユーザーを検索し、そのIDからmanage_boardを取得し、そのcan_p
#utがもし存在しなければ自身をパスさせ、その次もパスであれば自身にメンションを送信する。

#そして、そのメンションを受信し、またmanage_boardのcan_putが存在しなければ自身をパス、次も
#パスならメンションを送信・・・受信・・・を繰り返す。

#ーーーーーーーーーーーーーーーーーーーーー

#配置のロジックはbotと人間とで共通にする？
#配置関数は、呼び出したメンバー、盤面、座標を受け取り、もし裏返すことができるのなら裏返す
#パスする必要があるならパスし、また次の人がパスする必要があるなら終局する。
#（そして次の人が配置したいとき、次の人がこれを呼び出す。）
#botの場合、自身からのメンションを受け取った際にこれを行えばよい話である。
#これが新規に呼び出されるのはパスが完全に終わった後であるから、パス判定も不要。

def back_stone(board,team,a,b,back_stones):
    '''
    座標と、それで裏返すことのできる石のリストを受け取って、boardの該当マスをteamにします
    '''
    board[a][b] = team
        
    for grid in back_stones:
        board[grid[0]][grid[1]] = team

async def msg_0(reply,bot,ctx):
    manage_board = bot.board_dict[ctx.author.id]
    board = manage_board.board
    black,white,all = draw_and_get_stones(manage_board,manage_board.size)
    path = f"images/{manage_board.player_list[1].id}.jpg"

    reply += return_msg_content(black,white,all,manage_board)
    
    embed = discord.Embed(title=f"{manage_board.count}手目",description=reply,color=0x00bfff)
    file = discord.File(path)
    await ctx.send(file=file,embed=embed)
   
    for member in manage_board.player_list:
        if member.id in bot.board_dict.keys() and member != bot.user:
            del bot.board_dict[member.id]


async def msg_64(reply,bot,ctx):
    manage_board = bot.board_dict[ctx.author.id]
    board = manage_board.board
    black,white,all = draw_and_get_stones(manage_board,manage_board.size)
    path = f"images/{manage_board.player_list[1].id}.jpg"

    reply += "全てのマスに石が配置されました・・・\n"
    reply += return_msg_content(black,white,all,manage_board)
    
    embed = discord.Embed(title=f"{manage_board.count}手目",description=reply,color=0x00bfff)
    file = discord.File(path)
    await ctx.send(file=file,embed=embed)
   
    for member in manage_board.player_list:
        if member.id in bot.board_dict.keys() and member != bot.user:
            del bot.board_dict[member.id]

async def msg_other(reply,bot,ctx):
    manage_board = bot.board_dict[ctx.author.id]
    board = manage_board.board
    black,white,all = draw_and_get_stones(manage_board,manage_board.size)
    path = f"images/{manage_board.player_list[1].id}.jpg"

    reply += "両者ともに配置できなくなっため対局を終了します。\n"
    reply += return_msg_content(black,white,all,manage_board)
    
    embed = discord.Embed(title=f"{manage_board.count}手目",description=reply,color=0x00bfff)
    file = discord.File(path)

    await ctx.send(file=file,embed=embed)
   
    for member in manage_board.player_list:
        if member.id in bot.board_dict.keys() and member != bot.user:
            del bot.board_dict[member.id]

def hyouka(base_board,a,b,back_stones,team):
    """
    盤面をdeepcopyし、[a][b]に石を置くとどうなるのか計算し、
    その計算結果の盤面を評価値リストに照らし合わせ評価値を算出し返す関数。
    """
    copy_board = copy.deepcopy(base_board) #控え
    copy_board[a][b] = team #置いた場所を返す
    
    for stone in back_stones:
        copy_board[stone[0]][stone[1]] = team

    if len(base_board) == 8:
        l = [
            [ 45,-11,  4, -1, -1,  4,-11, 45],
            [-11,-16, -1, -3, -3,  2,-16,-11],
            [  4, -1,  2, -1, -1,  2, -1,  4],
            [ -1, -3, -1,  0,  0, -1, -3, -1],
            [ -1, -3, -1,  0,  0, -1, -3, -1],
            [  4, -1,  2, -1, -1,  2, -1,  4],
            [-11,-16, -1, -3, -3,  2,-16,-11],
            [ 45,-11,  4, -1, -1,  4,-11, 45]
            ]
    else:
        l = [
            [ 45,-11, -1, -1,-11, 45],
            [-11,-16, -3, -3,-16,-11],
            [  4, -1,  0,  0, -1,  4],
            [  4, -1,  0,  0, -1,  4],
            [-11,-16, -3, -3,-16,-11],
            [ 45,-11, -1, -1,-11, 45],
            ]

    tmp = 0
    for i in range(len(base_board)):
        for n in range(len(base_board)):
            if copy_board[i][n] == 0:
                tmp += l[i][n]

    return tmp,copy_board

def hyouka_final(base_board,a,b,back_stones,team):
    """
    盤面をdeepcopyし、[a][b]に石を置くとどうなるのか計算し、
    その計算結果の盤面に自分の石がいくつかあるかを返す関数。
    """
    copy_board = copy.deepcopy(base_board) #控え
    copy_board[a][b] = team #置いた場所を返す
    
    for stone in back_stones:
        copy_board[stone[0]][stone[1]] = team

    tmp = 0
    for i in range(len(base_board)):
        for n in range(len(base_board)):
            if copy_board[i][n] == 0:
                tmp += 1

    return tmp


def return_good_grid(board,can_put_grid,can_put,op,count,size=8):
    """
    置くのが可能な全ての位置に評価関数を適用し、一番良かったものの座標を返す。
    board 現在の盤面
    can_put_grid 置ける座標のタプルのリスト
    can_put 置ける座標とその返る石の辞書
    op 不明
    size 盤面のサイズ
    count 現在の手数（最終盤ではなるべく多くの石を取るようにするため）
    """
    print("-----------------------")

    true_list = []
    
    l = []
    d = {}
    d_2 = {}
    final_d = {}
    enemy_can_put = {} #相手が置ける場所が少ないほどいい。

    print("デバッグ：カウントが16より大きい")

    for grid in can_put_grid:
        if count > 20:
            tmp = hyouka_final(board,grid[0],grid[1],can_put[(grid[0],grid[1])],0)
            final_d[grid] = tmp
            print(f"{grid} の計算結果： {tmp}")

        tmp = hyouka(board,grid[0],grid[1],can_put[(grid[0],grid[1])],0)
        d[grid] = tmp[1]

    if count > 20:
        #print(f"ソート後：{final_d[sorted(final_d,key=lambda x:final_d[x],reverse=True)}")
        for i in final_d:
            if i in [(1,0),(0,1),(1,1),(6,0),(7,1),(6,1),
                    (0,6),(1,7),(1,6),(7,6),(6,7),(6,6)]:
                final_d[i] /= 1.5
            elif i in [(0,0),(0,7),(7,0),(7,7)]:
                final_d[i] *= 1.5

        tmp = sorted(final_d,key=lambda x:final_d[x],reverse=True)[0]
        return tmp if tmp else can_put_grid[0]

    for grid,new_board in d.items():
        """
        このループでは、1手目で生成した「置ける位置」「置いた結果」の辞書から、
        置いた結果の2手目に、相手がどう置くか？を走査する。
        """
        can_put_2 = can_put_for_bot(new_board,1,len(board))
        can_put_grid_2 = list(can_put_2.keys())

        c = len(can_put_grid_2)

        if grid in enemy_can_put.keys():
            enemy_can_put[grid] = max(c,enemy_can_put[grid])
        else:
            enemy_can_put[grid] = c

        if can_put_grid_2[0] == (-1,-1):
            #print("これ以上おけないのでやり直し")
            continue

        for grid_2 in can_put_grid_2:
            """
            このループでは、2手目で相手が置ける位置をシミュレートし、
            その置いた結果の評価値がどうなるかを計算し、リストに保持する。
            """

            
            tmp = hyouka(new_board,grid_2[0],grid[1],can_put_2[grid_2],1)
            
            if grid not in d_2:
                #辞書の、座標をキーとした値にリストとして保持
                d_2[grid] = [tmp[0]]
            else:
                d_2[grid].append(tmp[0])

    l = {i:sorted(n)[0] for i,n in d_2.items()} #各枝で、最も評価値が低くなるものを選択する。
    

    def check(x):
        if x[0] in [(1,0),(0,1),(1,1),(6,0),(7,1),(6,1),
                    (0,6),(1,7),(1,6),(7,6),(6,7),(6,6)]:
            #print("端なので-99999")
            return -99999
        elif x[0] in [(0,0),(0,7),(7,0),(7,7)]:
            return 99999
        else:
            return x[1]-enemy_can_put[x[0]]

    #print("enemy_can_put・・・\n",enemy_can_put)

    score_sorted = sorted(l.items(),reverse=True,key=check)
    #print("score_sorted・・・\n",score_sorted)

    return score_sorted[0][0] if score_sorted else can_put_grid[0]
   
async def _put(message,bot,manage_board):

    '''
    これはbotがputする際の処理である。
    '''

    board = manage_board.board
    path = f"images/{manage_board.player_list[1].id}.jpg"
    passer = None
    size = manage_board.size

    reply = "\n"
    kifus = ""

    # これが実行されるとき、それはパスがすべて解消され、人間がコマンドを実行し、
    # 人間が配置を完了したときである。つまり、実行時点ではbotがパスをするか否かは決定されず、
    # 以下の無限ループ内においてbotは「人間パス」→「bot配置」を行う。
    # なぜなら、先に人間がパスをするという状況はこの関数を使う限りありえないからである。

    # もしbotにパスが必要なときは、必ず処理を人間に戻すこと。
    # それ以外は無限に置き続けること。

    while True:
        #i=0のとき、自身のパス判定、i=1のとき、人間のパス判定
        #もし自身がパスするしかないのなら、その次に人間のパス判定を行う
        #もし人間もパスしなければならないのなら、それは終局であり
        #人間がパスする必要がなければ関数の処理はやめて人間に番を移す

        can_put_to_dict(manage_board,manage_board.board,0,size) #botは打てるか
        can_put_grid = list(manage_board.can_put.keys())

        if can_put_grid[0] == (-1,-1):     
            # botはパスするので、もし既に人間がパスしていたら終局だし、
            # そうでなければ人間のパス判定に移行しループを継続
            if passer == 1:
                # 終局
                black,white,all = draw_and_get_stones(manage_board,size)

                if not (black and white):
                    return 0,reply,kifus # どちらかの石が0になった場合の処理。
                elif all == 64:
                    return 64,reply,kifus # 最後まで打ち終わった場合の処理。
                else:
                    return -1,reply,kifus # どちらも打てなくなった場合の処理
            elif passer is None:
                # 人間のパス判定を行うのでループを継続
                passer = 0

        else:
            # botはパスする必要が無いので、そのまま配置する。
            passer = None

            # ここから配置処理
            
            can_put_tmp = list(manage_board.can_put.keys())
            print("デバッグ：",can_put_tmp)
            if len(can_put_tmp) == 1:
                grid_tmp = can_put_tmp[0]
            else:
                grid_tmp = return_good_grid(manage_board.board,can_put_grid,
                                            manage_board.can_put,-1,manage_board.count,size)
            if grid_tmp:
                bot_x,bot_y = grid_tmp
            else:
                raise Exception("botは置ける判定なのに置けない")
                return

            back_stone(board,manage_board.team,bot_x,bot_y,
                                    manage_board.can_put[(bot_x,bot_y)])     
            
            black,white,all = draw_and_get_stones(manage_board,size)
            reply += f"[CPU] ({bot_y+1},{bot_x+1})に配置しました。\n"

            x_for_kifu = chr(bot_y+97)
            y_for_kifu = str(bot_x+1)

            kifus += f"{x_for_kifu}{y_for_kifu}"
            # ここまで配置処理

        can_put_to_dict(manage_board,manage_board.board,1,size) #人間は打てるか
        can_put_grid = list(manage_board.can_put.keys())
        
        if can_put_grid[0] == (-1,-1):
            # 人間はパスするので、もし事前にbotがパスしていたら終局だし、
            # そうでなければbotのパス判定に移行しループを継続
            if passer == 0:
                # 終局
                black,white,all = draw_and_get_stones(manage_board,size)

                if not (black and white):
                    return 0,reply,kifus # どちらかの石が0になった場合の処理。
                elif all == size ** 2:
                    return 64,reply,kifus # 最後まで打ち終わった場合の処理。
                else:
                    return -1,reply,kifus # どちらも打てなくなった場合の処理

            elif passer is None:
                # botのパス判定を行うのでループを継続
                passer == 1

        else:
            return None,reply,kifus

    # この関数がreturnするreplyが、botの配置ログそのものである。


class PutCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command(aliases=["p"])
    async def put(self,ctx,x:int,y:int):
        x_for_kifu = chr(x+96)
        y_for_kifu = str(y)

        x -= 1
        y -= 1

        ID = ctx.author.id
        bot = self.bot

        if ID not in bot.board_dict.keys():
            await ctx.send("対局が開始していません。")
            return

        reply = ""

        manage_board = bot.board_dict[ID]
        board = manage_board.board
        path = f"images/{manage_board.player_list[1].id}.jpg"
        size = manage_board.size

        can_put_grid = list(manage_board.can_put.keys())
        players = manage_board.player_list
    
        if manage_board.now_player != ctx.author:
            await ctx.send("あなたの番ではありません。")
            return
    
        if (y,x) in can_put_grid:
            back_stone(board,manage_board.team,y,x,manage_board.can_put[(y,x)])
            manage_board.passer = None
            black,white,all = draw_and_get_stones(manage_board,size)
            reply += f"({x+1},{y+1})に配置しました。\n"
            manage_board.team = not manage_board.team
            manage_board.count += 1

            got_data = get_board_state(players[1].id)
            board_num = list(get_board_num(board))
            print(got_data.get("kifu",""),x_for_kifu,y_for_kifu)
            write_board_state(players[1].id, manage_board.team, board_num[0], board_num[1],
                              got_data.get("kifu","") + x_for_kifu + y_for_kifu)
    
        else:
            black,white,all = draw_and_get_stones(manage_board,size)
            grid_guide = tuple((grid[1]+1,grid[0]+1) for grid in can_put_grid)
            await ctx.send(f"({x+1},{y+1})には配置できません。\n置ける場所：{grid_guide}")
            return
            
        manage_board.now_player = manage_board.player_list[manage_board.team]
        
        if all == manage_board.size ** 2:
            await msg_64(reply,bot,ctx)
            return

        if black == 0 or white == 0:
            t = "黒" if black == 0 else "白"
            reply += f"{t}の石が0個になりました。対局を終了します。\n"
            
            await msg_0(reply,bot,ctx)
            return
        
        for i in range(2):
            can_put_to_dict(manage_board,manage_board.board,manage_board.team,size)
            can_put_grid = list(manage_board.can_put.keys())
            player = players[1] if players[0] == ctx.author else players[0]
    
            if can_put_grid[0] == (-1,-1):
                if manage_board.passer != manage_board.team and manage_board.passer is not None:
                    await msg_other(reply,bot,ctx)
                    return
    
                manage_board.passer = manage_board.team
                reply += "どこにも置けないため、パスします。\n"
                manage_board.team = not manage_board.team
                manage_board.now_player = manage_board.player_list[manage_board.team]
                can_put_to_dict(manage_board,manage_board.board,manage_board.team)


        if manage_board.now_player == bot.user:
            # 現在の番がbot自身なら、石を置いて番を相手に返す

            await ctx.send("botが思考中・・・")
                    
            result,bot_reply,bot_kifus = await _put(ctx.message,bot,manage_board)
            manage_board.passer = None

            manage_board.team = not manage_board.team
            manage_board.now_player = manage_board.player_list[manage_board.team]

            reply += f"```{bot_reply}```"

            
            got_data = get_board_state(players[1].id)
            board_num = list(get_board_num(board))
            write_board_state(players[1].id, manage_board.team, board_num[0], board_num[1],
                              got_data.get("kifu","") + bot_kifus)

            if result == 0:
                await msg_0(reply,bot,ctx)
                return
            elif result == -1:
                await msg_other(reply,bot,ctx)
                return
            elif result == 64:
                await msg_64(reply,bot,ctx)
                return
        
        can_put_grid = list(manage_board.can_put.keys())
    
        black,white,all = draw_and_get_stones(manage_board,size)
        reply += f"\n{manage_board.player_list[not manage_board.team].mention}の番が終了・・・\n"
        reply += f"現在の石数 [黒: **{black}** / 白: **{white}**]\n"
        reply += f"\n__つぎ:{manage_board.now_player.mention}（{['白','黒'][manage_board.team]}）__"
        
        embed = discord.Embed(title=f"{manage_board.count}手目",description=reply,color=0x00bfff)
        file = discord.File(path)
        await ctx.send(file=file,embed=embed)
        os.remove(path)

    @commands.is_owner()
    @commands.command()
    async def print_can_put(self,ctx):
        print(self.bot.board_dict[ctx.author.id].can_put)
        
def setup(bot):
    bot.add_cog(PutCog(bot))
