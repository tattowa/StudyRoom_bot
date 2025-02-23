from discord.ext import commands
import pandas as pd

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/vc_logs.csv'

    @commands.command()
    async def weekly_stats(self, ctx):
        df = pd.read_csv(self.data_file)
        # 週別統計処理を追加
        await ctx.send("週別統計を表示します。")

async def setup(bot):
    await bot.add_cog(Stats(bot))