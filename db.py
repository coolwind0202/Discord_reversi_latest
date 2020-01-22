from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
import numpy as np
import atexit

"""データベースへの書き込み、読み込みを代行するプログラム。"""

client = Cloudant.iam("9002cd5e-e707-497c-8206-267e9dfbe4b2-bluemix", 
                      "O4y6twOjjD5Lh6hG3nE7fiyC4zMBoPokzckcFcSmrfob")
client.connect()

db = client["dr_db"]
tmp_db = client["tmp_db"] #現在の対局情報を一時的に保存

def write_user_info(ID,**kwargs):
    ID = str(ID)

    tmp_dict = {}
    for key,value in kwargs.items():
        tmp_dict[str(key)] = str(value)
    
    if ID in db:
        #更新
        for key,value in tmp_dict.items():
            db[ID][key] = value
        db[ID].save()
    else:
        #作成
        tmp_dict.update({"_id":ID})
        db.create_document(tmp_dict)

def write_board_state(leader_id,now,leader_num,enemy_num,kifu):
    """
    引数は全て整数型である
    start_board_stateに対して、これは手が打たれるたびに呼び出される。
    何度打たれてもsizeやenemy_idは変化しないのでこの関数がそれらを受け取る必要性はない。
    """

    tmp_db = client["tmp_db"]
    ID = str(leader_id)
    tmp_db[ID]["now"] = now
    tmp_db[ID]["leader_num"] = str(leader_num)
    tmp_db[ID]["enemy_num"] = str(enemy_num)
    tmp_db[ID]["kifu"] = kifu
    tmp_db[ID].save()

def start_board_state(leader_id,enemy_id,size,channel_id,guild_id):
    """
    write_board_stateに対して、これは対局開始時にのみ呼び出される。
    開始時のみに呼び出されるのは、enemy_idやsizeを保持するため。
    """
    tmp_dict = {"_id":str(leader_id),"enemy_id":str(enemy_id),"size":size,
                "channel_id":str(channel_id),"guild_id":str(guild_id),
                "now": None, "leader_num": None, "enemy_num": None,"kifu": ""}
    tmp_db.create_document(tmp_dict)

def end_board_state(leader_id,winner):
    """
    start_board_stateに対して、これは対局終了時にのみ呼び出される。
    tmp_dbは一時的なものであるため、対局が終了する際に破棄する必要がある。
    また、一時的データベースに保存している棋譜情報をメンバーの恒常データベースに移動して、
    メンバーの勝利数についても増加を行う。
    """
    ID = str(leader_id)
    enemy_id = str(tmp_db[ID]["enemy_id"])
    kifu = tmp_db[ID]["kifu"]

    if ID in db:
        db[ID]["kifu"] = kifu
    else:
        db.create_document({"_id":ID,"kifu":kifu})

    if enemy_id in db:
        db[enemy_id]["kifu"] = kifu
    else:
        db.create_document({"_id":enemy_id,"kifu":kifu})

    if winner == 1:
        db[ID]["win_num"] = db[ID].get("win_num",0) + 1
    elif winner == 0:
        db[enemy_id]["win_num"] = db[enemy_id].get("win_num",0) + 1

    db[ID]["battle_num"] = db[ID].get("battle_num",0) + 1
    db[enemy_id]["battle_num"] = db[enemy_id].get("battle_num",0) + 1

    db[ID].save()
    db[enemy_id].save()

    tmp_db[str(leader_id)].delete()

def get_board_state(leader_id):

    ID = str(leader_id)
    if ID in tmp_db:
        return tmp_db[ID]
    else:
        return None

def get_user_info(ID):
    """IDからユーザー情報を読み込みます。IDは文字列型です。"""    
    ID = str(ID)
    if ID in db:
        return db[ID]
    else:
        return None

def get_all_battle_info():
    """
    現在行われている全ての盤面データを読み込みます。
    これはbotが起動時に、盤面データを復元するために呼び出されます。
    リーダー、参加者、現在の手番、盤面状況、盤面サイズ、チャンネル、サーバーの
    順にデータを返します（それらをまとめたリストの、さらにまとめたリスト）。
    """
    tmp = {}
    for elem in tmp_db:
        elem_ = elem
        l = [elem_.get("_id"), elem_.get("enemy_id"), elem_.get("now"), elem_.get("leader_num"), 
             elem_.get("enemy_num"), elem_.get("size"), elem_.get("channel_id"), elem_.get("guild_id")]
        if None in l:
            continue          
                
        tmp[elem_["_id"]] = l

    return tmp


def end_user_info(ID,**kwargs):
    """IDからそのユーザーの対局情報だけを削除します。"""
    ID = str(ID)

    if ID in db:
        db[ID]["board_num"] = None
        db[ID]["channel"] = None
        db[ID]["guild"] = None
        db[ID]["enemy"] = None
        if "win_num" in db[ID].keys():
            db[ID]["win_num"] += kwargs.get("win",0)
        else:
            db[ID]["win_num"] = kwargs.get("win",0)
        
        if "battle_num" in db[ID].keys():
            db[ID]["battle_num"] += 1
        else:
            db[ID]["battle_num"] = 1
        db[ID].save()

def get_board_num(board):
    l = list(np.ravel(board))

    l1 = ["1" if i==1 else "0" for i in l]
    l2 = ["1" if i==0 else "0" for i in l]

    n1 = int("".join(l1),2)
    n2 = int("".join(l2),2)

    return n1,n2

def get_board_data(board_num_1,board_num_2):
    n1 = str(bin(board_num_1))[2:].zfill(64)
    n2 = str(bin(board_num_2))[2:].zfill(64)

    l = [[] for i in range(8)]
    c = 0

    for i in range(8):
        for n in range(8):
            if n1[c] == "0" and n2[c] == "0":
                l[i].append(None)
            elif n1[c] == "1":
                l[i].append(1)
            else:
                l[i].append(0)
            c += 1

    return l

@atexit.register
def stop():
    client.disconnect()
