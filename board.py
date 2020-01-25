import datetime
# 盤面コンテキストを定義するファイル。
# 盤面コンテキストには盤面情報、前回の盤面情報、、チャンネルID、サーバーID、
# 対局者1、対局者2、棋譜、パスしたか、手数、置ける位置、対局開始時刻が含まれる。

# TODO:
# 定数 CANT_PUT_STONE (-1) と DONE_PUT_STONE の追加

class _Board(object):
    """
    素の盤面情報。
    インスタンスに[x,y]の添字でアクセスすることで石情報を取得できる。
    
    このインスタンスは良手を走査する際にコピーされる。
    """
    def __init__(self,**kwargs):
        self.board_data = {(n,i):None for n in range(8) for i in range(8)}
        
    def __getitem__(self,x,y):
        # _board[x,y]で直接石情報にアクセスできるようにする。
        return self.board_data[(x,y)]
    
    def can_back_stones(self,x,y,team):
        """
        (x,y) に石を置いた場合石を返せるか判定する。
        オセロにおいて石を返せる場合に石を置くことができる。逆にいえば石を返せないなら置けないとわかる。
        どの石が返るかの座標を示すタプルをさらにまとめたタプルを返す。もし戻り値がFalseなら置けない。
        """
        board = self.board_data
        
        COURSES = ((0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)) # 走査する方向を定義
        confirmed_stones = [] # 返せることが確定した石の座標リスト。
        
        for COURSE in COURSES:
            may_back_stones_grid = [] # もしかすると返せるかもしれない、自石が発見された時点で返せることが確定する石のリスト。
            for i in range(8):
                a, b = COURSE
                
                if 0 > a * i or a * i > 7:
                    break
                elif 0 > b * i or b * i > 7:
                    break
                    
                if self[x + i, y + i] is None:
                    # 参照した座標がNoneなら石を返すことはできない。
                    break
                elif self[x + i, y + i] == team:
                    # 参照した座標が自分の石なら、返せるかもしれない石のリストを確定済石のリストに追加。
                    # 隣がすぐに自分の石だった場合は空のリストを追加するだけなので問題ない。
                    confirmed_stones += may_back_stones_grid
                    break
                elif self[x + i, y + i] == not team:
                    # 参照した座標が敵の石なら、返せるかもしれない石のリストに追加。
                    may_back_stones_grid.append((x + i, y + i))
                    
        return confirmed_stones
    
    def put(self,x,y,team):
        """
        盤面の特定インデックス [a][b] にチーム (team) の石を置く。
        先に返せる石があるかを問合せ、もしなければ定数「CANT_PUT_STONE」を、あれば石を置く処理のあと定数「DONE_PUT_STONE」を返す。
        """
        back_stones = can_back_stones(x,y,team)
        
        if not back_stones:
            return consts.CANT_PUT_STONE
        else:
            self[x,y] = team
            for stone in back_stones:
                self[stone] = team
            return consts.DONE_PUT_STONE
    
    def can_put_grid_and_returns(self,team):
        """
        現在の盤面において、キーが「チーム (team) が石を置ける場所」、値が「仮にその場所に置いたらどうなるか」を示す辞書を返す。
        """
        
        pass

class ManageBoard(_Board):
    
    """
    TODO
    良手の走査
    
    再帰的に関数を呼び出すことで走査できるようにする。
    最初に呼び出す際に深さと盤面、現在の手を指定する。
    そのあと、盤面をコピーする。
    
    コピーした盤面の置ける位置を取得し、各座標に置いた結果を示す盤面に走査関数を適用。
    そのまま再帰的に呼び出し、もしn回目の呼び出しで最初に指定した深さになったらその盤面に評価関数を適用して返す。
    
    評価値が返ってきたら、その中で最も評価が良いものを返す。
    一番最初に呼び出した関数に処理が戻ったら、最も評価が良かった2手目を返す。
    
    パスが存在した場合の処理については要検討、エラー回避をするならその時点で走査を打ち切るのが無難か？
    """
    
    def __init__(self,**kwargs):
        super().__init__()
        
        self.board = _Board()
        self.channel_id = kwargs.get("channel_id",0)
        self.guild_id = kwargs.get("guild_id",0)
        self.leader_id = kwargs.get("leader_id",0)
        self.enemy_id = kwargs.get("enemy_id",0)
        
        self.players_id = [leader_id, enemy_id]
        self.kifus = ""
        self.pass_flag = False 
        self.turn_num = 0
        self.start_time = datetime.datetime.now()
        
    # 盤面コンテキストで行える操作を定義する。あるオブジェクトを盤面に変換する処理などはクラスメソッドとして定義。
    
    def put(self,x,y,team):
        """
        盤面の特定インデックス [a][b] にチーム (team) の石を置く。
        """
        
        self.board.put(x,y,team)
    
    def can_put_grid_and_returns(self,team):
        """
        現在の盤面において、キーが「チーム (team) が石を置ける場所」、値が「仮にその場所に置いたらどうなるか」を示す辞書を返す。
        """
        
        pass
