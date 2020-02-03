# ゲーム全般を管理するファイル
import random

import discord
from discord.ext import commands

import board

class GameCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.guild_only()
    @commands.cooldown(1,3.0,type=commands.BucketType.user)
    @commands.command()
    async def start(self,ctx,enemy:discord.Member,size=8):
        """
        オセロの対局をメンションした相手とスタートします。
        
        Discord Reversi にリアクションの追加権限がある場合、どちらが先手になるか聞かれます。
        指示に従ってリアクションを追加してください。
        """
        if ctx.author == enemy:
            await ctx.send("自分自身と対局することはできません。")
            return
        
        players = [ctx.author, enemy]
        
        if ctx.channel.permissions_for(ctx.guild.me).add_reactions:
            # もし、botにリアクション権限があるなら先手の判定を行う
            one = ""
            two = ""
            rnd = "" # 「ランダム」を示す絵文字（R）
            emojis = [one,two,rnd] # 使用する絵文字のリスト
            
            reply = f"""対局を始める前に、どちらを先手とするかを決定します。リアクションで先手のプレイヤーを選択してください。
            {one} {ctx.author}
            {two} {enemy}
            {rnd} ランダム （{ctx.author.name} か、 {enemy.name} のどちらかをランダムで決定）
            """
            sent_message = await ctx.send(reply)
            
            for emoji in emojis:
                await send_message.add_reaction(emoji) # 必要なリアクションを追加
            
            def first_move_check(reaction,user):
                #行われたリアクションが、先手選択のリアクションであるかを判定する
                
                return user in [ctx.author, enemy] and reaction in emojis and \
                    reaction.message.id == send_message.id    
            try:
                reaction, user = await self.bot.wait_for("reaction_add",check=first_move_check,timeout=180.0)
            except asyncio.TimeoutError:
                await ctx.send("リアクションを待機しましたが、3分以内に応答がなかったため、対局をキャンセルします。")
                return
            
            if str(reaction.emoji) == two:
                # もし対局相手として指定されたメンバーのリアクションが押されたら、逆にする
                players[0], players[1] = players[1], players[0]
            elif str(reaction.emoji) == rnd:
                # もしランダムを指定されたら、シャッフル
                random.shuffle(players)
                
        manage_board = board.ManageBoard(channel_id=ctx.channel.id,guild_id=ctx.guild.id,)
        
        
    
