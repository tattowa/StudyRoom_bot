from discord.ext import commands
import datetime
import pandas as pd

class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/vc_logs.csv'

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel != before.channel:
            entry = {
                'user_id': member.id,
                'timestamp': datetime.datetime.now(),
                'action': 'join',
                'channel': after.channel.name
            }
            df = pd.DataFrame([entry])
            df.to_csv(self.data_file, mode='a', header=False, index=False)

    @commands.command()
    async def register_vc(self, ctx, *, channel_name):
        await ctx.send(f'VC {channel_name} を登録しました。')

async def setup(bot):
    await bot.add_cog(VCTracker(bot))