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
    石情報は、必ずNoneかPlayerクラスを示す。
    
    このインスタンスは良手を走査する際にコピーされる。
    このクラスのインスタンスをメインの処理で直接作成することはなく、基本的にManageBoardのインスタンスを作成することになる。
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
        既に何らかの石が置かれている場合は当然置くことができない。
        どの石が返るかの座標を示すタプルをさらにまとめたタプルを返す。もし戻り値がFalseなら置けない。
        """
        board = self.board_data
        
        if self[x, y] is not None:
            return ()
        
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
                    
        return tuple(confirmed_stones)
    
    def back_stones(self,team,stones):
        """
        与えられた石の座標のリストもしくはタプルから、該当する石を返す。
        """
        for stone in stones:
            self[stone] = team
    
    def put(self,x,y,team):
        """
        盤面の特定インデックス [a][b] にチーム (team) の石を置く。
        先に返せる石があるかを問合せ、もしなければ定数「CANT_PUT_STONE」を、あれば石を置く処理のあと定数「DONE_PUT_STONE」を返す。
        """
        stones = can_back_stones(x,y,team) # 返せる石のタプル。
        
        if not stones:
            return consts.CANT_PUT_STONE
        else:
            back_stones(team,((x, y),) + stones)
            return consts.DONE_PUT_STONE
    
    def can_put_grid_and_returns(self,team):
        """
        現在の盤面において、キーが「チーム (team) が石を置ける場所」、値が「仮にその場所に置いたら何が返るか」を示す辞書を返す。
        """
        grid_and_stones_dict = {}
        
        for key in self.board_data:
            back_stones = can_back_stones(self.board_data[key])
            
            if back_stones:
                grid_and_stones_dict[key] = back_stones
                
        return grid_and_stones_dict
    
    def stones_will_not_returned(self):
        """
        盤面の確定石数を返す。
        """
    
    def eval_(self):
        """
        盤面を評価し評価値を返す。
        """
        pass
        
    
    @property
    def decision(self,depth,team):
        """
        この関数が呼び出されるのはbotの思考時。
        呼び出す際には、その時点の盤面(_Board インスタンス)を与える。
        
        与えられた _Board インスタンス の can_put_grid_and_returns() メソッドを実行。
        これの戻り値（置ける場所がキー、置いた結果が）に対して以下の処理を行う。
        
        1. board 引数をコピー。
        2. コピーした board_2 に、戻り値を利用してputメソッドを実行。
        3. その結果をdescisionメソッドに渡す。このときteam引数は反転し、depth引数は1引くこと。
        4. depth引数が0になった、あるいは can_put_grid_and_returns() の戻り値が空になったら、
           処理をやめてその盤面を評価関数に渡す。評価関数の戻り値を返す。
        5. 戻り値が返ってきたら、それをリストに追加する。
        6. リストの中でもっとも評価が良かったものを返す。
           （min-max法に基づき、teamが敵の場合もっとも悪いものを返す。）
        7. 最後まで処理が戻ってきたら、座標と評価結果を辞書に格納。
        8. その中でもっとも評価が良かった座標を思考結果として返す。
       
        """
        
        if depth == 0:
            return self.eval_()
            
            
        
        

class ManageBoard(object):
    """
    盤面コンテキスト。
    ここで定義するのは盤面と実際のゲーム、Discordとの関連付けである
    一般的な処理は基本的に _Board クラスで定義しておく。
    """
    
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
    
    
