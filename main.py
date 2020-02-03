import os
import re
import traceback

import discord
from discord.ext import commands

TOKEN = os.getenv('TOKEN','')
COGS = []

class ReversiBot(commands.Bot):
    def __init__(self,command_prefix,help_command,**options):
        self.in_progress_boards = []      
        super().__init__(command_prefix,help_command,**options)
    
        for cog in COGS:
            try:
                self.load_extension(cog)
            except Exception:
                traceback.print_exc()
                
    async def on_ready(self):
        ch = self.get_channel(637542489510641673)
        self.system_msg = await ch.fetch_message(637568531424083978)
    
        await self.change_presence(activity=discord.Game(name='オセロ'))
        
def get_prefix(tmp,msg):
    if not isinstance(msg.channel, discord.abc.GuildChannel):
        return ""

    nick = msg.guild.me.display_name
    prefix = re.search(r"\[(.+)help\]",nick)

    if prefix is None:
        return "."
    else:
        return prefix.groups()[0]

if __name__ == '__main__':
    bot = ReversiBot(command_prefix=get_prefix,help_command=None)
    bot.run(TOKEN)
