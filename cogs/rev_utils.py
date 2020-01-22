from PIL import Image,ImageDraw
import discord
import datetime

from cogs.db import *

def can_put_stone(board,team,a,b,size=8):
    '''
    board[a][b]に石を置けるか。また石を置いたときどれが裏返るかを判定します。
    '''

    can_back_stones = []
    
    for i in range(-1,2):
        for n in range(-1,2):
            #以下、各方向ごとの処理
            enemy_stone_flag = False
            possible_stones = []
            for distance in range(1,8):
                a_ = a + i * distance
                b_ = b + n * distance
                if a_<0 or b_<0:
                    break
                elif a_>size-1 or b_>size-1:
                    break
                    
                try:
                    grid = board[a_][b_]
                except:
                    print("走査エラー：",a_,b_)
                    break
    
                if grid is None:
                    break
    
                if grid != team:
                    enemy_stone_flag = True
                    possible_stones.append((a_,b_))
                elif grid == team and enemy_stone_flag:
                    can_back_stones.extend(possible_stones)
                    break
                elif grid == team and not possible_stones:
                    break
        
    return can_back_stones
    

def can_put_to_dict(manage_board,board,team,size=8):
    '''
    座標を受け取り、その座標に相当する石をひっくり返します
    '''
    can_put_flag = False
    back_list = []
    
    stones_dict_for_me = {}
    manage_board.can_put = {}
    
    for i in range(size):
        for n in range(size):
            try:
                grid = board[i][n]
            except:
                print("辞書変換エラー：",i,n)
            if grid is None:
                stones_for_back = can_put_stone(board,team,i,n,size)
                if stones_for_back:
                    can_put_flag = True
                    manage_board.can_put[(i,n)] = stones_for_back
    
    if not manage_board.can_put:
        manage_board.can_put = {(-1,-1):0}
    
    return 1

def can_put_for_bot(board,team,size=8):
    '''
    botが現在思考中の局面でどこに配置できるかを返すだけの関数です。
    配置はしません。
    '''
    can_put_flag = False
    back_list = []
    
    stones_dict_for_me = {}
    
    for i in range(size):
        for n in range(size):
            try:
                grid = board[i][n]
            except:
                print("辞書変換エラー：",i,n)
            if grid is None:
                stones_for_back = can_put_stone(board,team,i,n,size)
                if stones_for_back:
                    can_put_flag = True
                    stones_dict_for_me[(i,n)] = stones_for_back
    
    if not stones_dict_for_me:
        stones_dict_for_me = {(-1,-1):0}
    
    return stones_dict_for_me


def draw_and_get_stones(manage_board,size=8):
    '''
    盤面の状況を画像化します。
    '''
    board = manage_board.board
    id = manage_board.player_list[1].id

    black_stone = 0
    white_stone = 0
    all_stone = 0

    if size == 8:
        base = Image.open('reversi.jpg')
    else:
        base = Image.open('reversi_6.jpg')
    draw = ImageDraw.Draw(base)

    for i in range(size):
        for n in range(size):
            #一つ45×45ピクセル。空白は14×59ピクセル。
            start_x = 40 + n*45 + n*13
            start_y = 39 + i*45 + i*13
            
            if board[i][n] == 1:
                team = 0
                black_stone += 1
            elif board[i][n] == 0:
                team = 1
                white_stone += 1
            else:
                continue
            
            all_stone += 1
            fill_color = (255*team,255*team,255*team)
            
            if board[i][n] == 2:
                fill_color = (255,0,0)
            line_color = tuple(bool(elem-255) for elem in fill_color)

            draw.ellipse((start_x,start_y,start_x+45,start_y+45),fill=fill_color,outline=line_color)

    base.save(f"images/{id}.jpg",quality=90)
    return black_stone,white_stone,all_stone

def create_about(bot):
    embed = discord.Embed(title="Discord Reversiの各情報",color=0xdebacc)
    embed.add_field(name="参加しているサーバー数",value=str(len(bot.guilds)))
    embed.add_field(name="現在行われている対局数",value=str(len(list(bot.board_dict.keys()))))
    embed.add_field(name="BOTの追加リンク",
                    value="[Discord Reversiを招待する](https://discordapp.com/api/oauth2/authorize?client_id=590138519650041876&permissions=0&scope=bot)",
                    inline=False)
    embed.add_field(name="公式サーバーの招待",value="[公式サーバーに参加する](https://discord.gg/RvsHPvX)")
    return embed

def return_msg_content(black,white,all,manage_board):

    size = manage_board.size
    player_list = manage_board.player_list
    created_at = manage_board.created_at
    
    msg = ""

    if black > white:
        msg += f"黒の{player_list[1].name}さんの勝利！\n"
        end_board_state(player_list[1].id,1)
    elif black < white:
        msg += f"白の{player_list[0].name}さんの勝利！\n"
        end_board_state(player_list[1].id,0)
    else:
        msg += f"黒白同数につき引き分け！\n"
        end_board_state(player_list[1].id,-1)
    
    if all == 64:
        msg += f"結果: (黒: **{black}** / 白: **{white}** / 総数: **64** ) "
    else:
        if black == 0:
            msg += f"結果: (黒: **0** / 白: **{size*size}** ) "
        elif white == 0:
            msg += f"結果: (黒: **{size*size}** / 白: **0** ) "
        else:
            msg += f"結果: (黒: **{black}** / 白: **{white}** / 総数: **{all}** ) "
    
    tmp = int((datetime.datetime.now() - created_at).total_seconds())
    msg += f"対局時間：{tmp} 秒\nお疲れ様でした。\n"

    return msg

