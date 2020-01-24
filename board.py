# 盤面コンテキストを定義するファイル。
# 盤面コンテキストには盤面情報、前回の盤面情報、、チャンネルID、サーバーID、
# 対局者1、対局者2、棋譜、パスしたか、手数、置ける位置、対局開始時刻が含まれる。

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
    
    def put(self,x,y,team):
        """
        盤面の特定インデックス [a][b] にチーム (team) の石を置く。
        """
        
        pass
    
    def can_put_grid_and_returns(self,team):
        """
        現在の盤面において、キーが「チーム (team) が石を置ける場所」、値が「仮にその場所に置いたらどうなるか」を示す辞書を返す。
        """
        
        pass

class ManageBoard(object):
    
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
        pass
    # 盤面コンテキストで行える操作を定義する。盤面に変換する処理などはクラスメソッドとして定義。
    
    def put(self,x,y,team):
        """
        盤面の特定インデックス [a][b] にチーム (team) の石を置く。
        """
        
        pass
    
    def can_put_grid_and_returns(self,team):
        """
        現在の盤面において、キーが「チーム (team) が石を置ける場所」、値が「仮にその場所に置いたらどうなるか」を示す辞書を返す。
        """
        
        pass
