from discord.ext import commands
import datetime
import pandas as pd
import discord

class VCLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/vc_logs.csv'
        self.log_channel_id = 1343442260431470612  # 通知を送信するテキストチャンネルのID

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        entry = None
        message = None

        # VC参加
        if after.channel and after.channel != before.channel:
            entry = {
                'user_id': member.id,
                'timestamp': datetime.datetime.now(),
                'action': 'join',
                'channel': after.channel.name
            }
            message = f"🔊 **{member.display_name}** が **{after.channel.name}** に参加しました。"

        # VC退出
        elif before.channel and not after.channel:
            entry = {
                'user_id': member.id,
                'timestamp': datetime.datetime.now(),
                'action': 'leave',
                'channel': before.channel.name
            }
            message = f"📴 **{member.display_name}** が **{before.channel.name}** から退出しました。"

        # ログをCSVに保存
        if entry:
            df = pd.DataFrame([entry])
            df.to_csv(self.data_file, mode='a', header=not pd.io.common.file_exists(self.data_file), index=False)

        # ログ用テキストチャンネルにメッセージを送信
        if message:
            log_channel = self.bot.get_channel(self.log_channel_id)
            if log_channel:
                try:
                    await log_channel.send(message)
                except discord.HTTPException as e:
                    print(f"メッセージ送信エラー: {e}")

    @commands.command()
    async def register_vc(self, ctx, *, channel_name):
        """VCを登録するためのコマンド。将来の機能拡張用。"""
        await ctx.send(f'✅ VC「{channel_name}」を登録しました。')

async def setup(bot):
    await bot.add_cog(VCLogger(bot))
