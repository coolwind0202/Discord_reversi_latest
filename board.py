import datetime
import math
import copy
# 盤面コンテキストを定義するファイル。
# 盤面コンテキストには盤面情報、前回の盤面情報、、チャンネルID、サーバーID、
# 対局者1、対局者2、棋譜、パスしたか、手数、置ける位置、対局開始時刻が含まれる。

# TODO:
# 定数 CANT_PUT_STONE (-1) と DONE_PUT_STONE の追加
# LEADER ENEMY BOT_WIN BOT_LOSE NOT_ENDED ENDED定数の追加 （マジックナンバーを回避）

class _Board(object):
    """
    素の盤面情報。
    インスタンスに[x,y]の添字でアクセスすることで石情報を取得できる。
    石情報は、必ずNoneかPlayerクラスを示す。
    
    このインスタンスは良手を走査する際にコピーされる。
    このクラスのインスタンスをメインの処理で直接作成することはなく、基本的にManageBoardのインスタンスを作成することになる。
    """
    def __init__(self,**kwargs):
        self.size = kwargs.get("size",8)
        self.board_data = {(n,i):None for n in range(self.size) for i in range(self.size)}
        
    def __getitem__(self,x,y):
        # _board[x,y]で直接石情報にアクセスできるようにする。
        return self.board_data[(x,y)]
    
    @property
    def stones_num(self):
        """
        盤面上における （leaderの石数, enemyの石数） をタプルで返す。
        """
        leader_stones = 0
        enemy_stones = 0
        
        for i in range(self.size):
            for n in range(self.size):
                if self[i,n] == consts.LEADER:
                    leader_stones += 1
                elif self[i,n] == consts.ENEMY:
                    enemy_stones += 1
    
    @property
    def is_end(self):
        """
        対局が終了しているかを返す。
        どちらも石を置くことができない場合、その対局は終了している。
        """
        leader_can_put_grid = self.can_put_grid_and_returns(consts.LEADER)
        enemy_can_put_grid = self.can_put_grid_and_returns(consts.ENEMY)
        
        if leader_can_put_grid or enemy_can_put_grid:
            # まだ対局は終わっていない
            return consts.NOT_ENDED
        else:
            # どちらも置けないので、定数 ENDED を返す
            return consts.ENDED
        
    def bot_won(self,bot_team):
        """
        botが勝利したかを返す。
        """
        
        bot_stones = self.stones_num[bot_team]
        enemy_stones = self.stones_num[not bot_team]
            
        if bot_stones > enemy_stones:
            return consts.BOT_WIN
        else:
            return consts.BOT_LOSE
        
    
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
            for i in range(self.size):
                a, b = COURSE
                
                if 0 > a * i or a * i > self.size - 1:
                    break
                elif 0 > b * i or b * i > self.size - 1:
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
    
    def stones_will_not_return(self,bot_team):
        """
        botの思考に必要なメソッド。
        
        盤面における （botの確定石, 敵の確定石）のタプルを返す。
        ただし、正確な確定石数ではなく、端のみに着目したものである。
        4隅をタプルとして定義する。
        4隅について、その石が自分の石なら各方向に対し走査する。自分の石だったら石数に追加。そうでなければ走査打ち切り。
        """
        
        FOUR_CORNER_AND_COURSES = {(0,0): ((0,1),(1,0)), (self.size - 1, 0): ((-1,0),(0,-1)), 
                                   (0,self.size - 1): ((0,-1),(1,0)), (self.size - 1, self.size - 1): ((0,-1),(-1,0))}
        # 4隅の座標と、走査すべき方向を定義
        
        bot_stone_count = 0 # botの確定石カウント
        enemy_stone_count = 1 # botの確定石カウント
        
        for CORNER in FOUR_CORNER_AND_COURSES:
            if self[CORNER] == bot_team:
                # その隅がbotの確定石なので、更に走査する
                bot_stone_count += 1
                
                for COURSE in FOUR_CORNER_AND_COURSES[CORNER]:
                    # その隅から各方向に対して走査。
                    # COURSE[0] は現在走査している方向のx、CORNER[0] は現在走査している四隅の座標のx
                    
                    for i in range(self.size):
                        grid = ((COURSE[0] * i + CORNER[0]),(COURSE[1] * i + CORNER[1]))
                        
                        if self[grid] == bot_team:
                            bot_stone_count += 1
                        else:
                            break
            elif self[CORNER] == not bot_team:
                # その隅が敵の確定石なので、更に走査する
                enemy_stone_count += 1
                
                for COURSE in FOUR_CORNER_AND_COURSES[CORNER]:
                    # その隅から各方向に対して走査。
                    # COURSE[0] は現在走査している方向のx、CORNER[0] は現在走査している四隅の座標のx
                    
                    for i in range(self.size):
                        grid = ((COURSE[0] * i + CORNER[0]),(COURSE[1] * i + CORNER[1]))
                        
                        if self[grid] == not bot_team:
                            enemy_stone_count += 1
                        else:
                            break
    
    def eval_(self):
        """
        botの思考に必要なメソッド。
        
        盤面を評価し評価値を返す。
        評価値に必要なのは、盤面の評価値、候補数、そして確定石数。
        """
        
        # 盤面の評価に必要な評価値テーブルをハードコーディング
        point_table = {(0,0):100, (1,0):-40, (2,0):20, (3,0):5, (4,0):5, (5,0):20, (6,0):-40, (7,0):100,
                       (0,1):-40, (1,1):-80, (2,1):-1, (3,1):-1,}
    
    def final_decision(self,base_depth,bot_team,depth,team):
        """
        botの思考に必要なメソッド。
        
        最終局面を残り6手と定義したとき、対局が最終局面に達したときに呼び出されるのがこのメソッドである。
        通常の eval_ メソッドと比べ、このメソッドが全探索することにかわりはないが、
        残りの手数に応じて終局まで読むのがこのメソッドである。各葉は枝に対しbotが勝利したかを通知する。
        枝はそれを受け取ると、根の方へ勝利した局面数を返す。さらに根に近い枝は受け取った局面数を合計し返す。
        根は、局面数と次の手の座標を辞書に追加し、最初の呼びだし元に最も局面数が多かった座標を返す。
        """
        
        if depth == 0:
            # 葉まで到達したので、botが勝利したかを取得（パスの発生などにより完全な勝利ではない場合を考えない）。
            return self.bot_won(bot_team)
            
        tmp = self.can_put_grid_and_returns(team)
        if not tmp:
            # もし打てるところがなければすぐに勝利しているか返す。
            return self.bot_won(bot_team)
        
        if base_depth == depth:
            # 初回の呼び出しでの処理。
            
            win_dict = {}
            
            for grid in tmp:
                self_copy = copy.deepcopy(self)
                self_copy.back_stones(team,((grid[0], grid[1]),) + tmp[grid]) # 石を返した場合をシミュレート
                win_dict[grid] = self_copy.final_decision(depth - 1,not team)) # 次の手の座標と合計勝利局面数を追加
                
            sorted_tuple = sorted(win_dict.items(), lambda items: items[1] * -1) # 勝利数でソートして
            return sorted_tuple[0][0] # 最も合計勝利局面数が多かった座標を返す
            
        win_count = 0
        
        for grid in tmp:
            self_copy = copy.deepcopy(self)
            self_copy.back_stones(team,((grid[0], grid[1]),) + tmp[grid]) # 石を返した場合をシミュレート
            win_count += self_copy.final_decision(depth - 1,not team)) # シミュレートした盤面のfinal_decisionメソッドを呼び出して追加
            
        return win_count
    
    def decision(self,base_depth,bot_team):
        """
        botの思考を行う。このメソッドは初回の思考時に実行され、alpha_betaメソッドを呼び出し結果を返す。
        
        base_depth は探索の深さ。
        bot_team はbotのチーム。
        """
        
        grids = self.can_put_grid_and_returns(bot_team) #置ける位置と、返される石
        eval_dict = {}
        
        for grid in grids:
            self_copy = copy.copy(self) # 自身をコピー
            self_copy.back_stones(bot_team, ((grid[0], grid[1]),) + grids[grid]) # 走査中の手で返す
            
            inf = float("inf")
            eval_dict[grid] = self_copy.alpha_beta(base_depth - 1, bot_team, bot_team, -inf, inf) # alpha_betaに渡す
            
        max_eval = sorted(eval_dict.items(), reverse=True, key=lambda items:items[1])[0] # (座標,評価) のタプル
        return max_eval[0]
    
    def alpha_beta(self,depth,bot_team,team,alpha,beta):
        """
        2手目以降を探索する。
        alpha は下限値、beta は上限値で、返った評価値がこの範囲から外れた枝はそれ以上探索しない。
        
        参考: http://aidiary.hatenablog.com/entry/20050205/1274150331
        """
        
        if depth == 0:
            # 葉まで到達したので、評価値を取得
            return self.eval_()
        
        grids = self.can_put_grid_and_returns(team)
        eval_list = [] # 評価値のリスト。2手目以降は評価のみが重要なので、座標は不要
        
        for grid in grids:
            self_copy = copy.copy(self)
            self_copy.back_stones(team, ((grid[0], grid[1]),) + grids[grid]) # 走査中の手で返す
            
            copy_eval = alpha_beta(depth - 1, not team, alpha, beta) # 子ノードの評価値
            eval_list.append(copy_eval)
            
            if team == bot_team:
                # BOTの手番はMAXノード、評価が最大のものを選択
                max_eval = max(eval_list) # 現時点の最大の評価値
                alpha = max_eval
                
                if max_eval > beta:
                    return max_eval
            else:
                # 人間の手番はMINノード、評価が最小のものを選択
                min_eval = min(eval_list)
                beta = min_eval
                
                if min_eval < alpha:
                    return min_eval
        
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
    
    
