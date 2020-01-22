import discord
from discord.ext import commands
import os
import datetime
import re
import traceback
import random

from cogs.db import get_all_battle_info,get_board_data
from cogs.start import Manage_board
from cogs.rev_utils import can_put_to_dict

TOKEN = os.environ['DISCORD_BOT_TOKEN']
#TOKEN = "NTkwMTM4NTE5NjUwMDQxODc2.XbE5CA.oD6_NPRGc4rpsjMpDtsNO6djb9s"
COGS = ["cogs.put","cogs.start","cogs.other","cogs.manage"]

def kifu(kifus):
    for i in kifus:
        yield i 

class ReversiBot(commands.Bot):
    def __init__(self,command_prefix,help_command,**options):
        super().__init__(command_prefix,help_command,**options)
    
        for cog in COGS:
            try:
                self.load_extension(cog)
            except Exception:
                traceback.print_exc()
                
    async def on_ready(self):
        os.mkdir("images")
        battle_info = get_all_battle_info()
        self.board_dict = {}

        for elem in battle_info:
            tmp = battle_info[elem]
            leader_id = tmp[0]
            enemy_id = tmp[1]
            now = tmp[2]
            leader_num = int(tmp[3])
            enemy_num = int(tmp[4])

            board = get_board_data(leader_num,enemy_num)
            size = tmp[5]
            channel = self.get_channel(int(tmp[6]))
            guild = self.get_guild(int(tmp[7]))
            leader = guild.get_member(int(leader_id))
            enemy = guild.get_member(int(enemy_id))

            manage_board = Manage_board(leader,enemy,guild=guild,team=now,
                                        channel=channel,size=size,board=board)

            can_put_to_dict(manage_board,board,now)
            self.board_dict[int(leader_id)] = manage_board
            self.board_dict[int(enemy_id)] = manage_board

        print(self.board_dict)

        self.kifus = []
        self.read_kifus = kifu(self.kifus)

        ch = self.get_channel(637542489510641673)
        self.system_msg = await ch.fetch_message(637568531424083978)
    
        await self.change_presence(activity=discord.Game(name='オセロ'))
        print("start...")
        
    
    async def on_command_error(self,ctx,error):
        if isinstance(error,commands.CommandNotFound):
            if ctx.message.content[1].isalpha():
                await ctx.send("その名前のコマンドは存在しません。")
                print("[存在しないコマンド]",ctx.message.content,ctx.message.guild.name,">",ctx.message.channel.name)
        elif isinstance(error,commands.CommandOnCooldown):
            await ctx.send("短時間にコマンドを複数送信しています。負荷軽減のため、"\
                           f"**{round(error.retry_after,1)} **秒にもう一度お試しください。")
        elif isinstance(error,commands.UserInputError):
            await ctx.send("コマンド実行時に不適切なデータが渡されました。\n"\
                           "`.help` と送信することで各コマンドの使用方法を確認できます。")
        else:
            orig_error = getattr(error, "original", error)
            error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
            await ctx.send("処理中にエラーが発生しました。改善しないようであれば`.help`コマンドを"\
                           "ご確認の上、公式サーバーまでお問い合わせ下さい。")

            owner = self.get_user(519434882460549169)
            await owner.send(error_msg[:1999])

    async def on_guild_join(self,guild):
        await bot.system_msg.edit(embed=create_about(bot))

    async def on_guild_remove(self,guild):
        await bot.system_msg.edit(embed=create_about(bot))

def get_prefix(tmp,msg):
    if not isinstance(msg.channel,discord.abc.GuildChannel):
        return ""

    nick = msg.guild.me.display_name
    prefix = re.search(r"\[(.+)help\]",nick)

    if prefix is None:
        return "."
    else:
        return prefix.groups()[0]

if __name__ == '__main__':
    bot = ReversiBot(command_prefix=get_prefix,help_command=None,heartbeat_timeout=30.0,
                     status=discord.Status.dnd)
    bot.run(TOKEN,reconnect=True) # Botのトークン
