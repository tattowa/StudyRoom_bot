import discord
from discord.ext import commands
import traceback


intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected')
    await bot.change_presence(activity=discord.Game(name="勉強時間をトラッキング中！"))

    # 拡張機能の読み込み
    await bot.load_extension('cogs.vc_tracker')
    await bot.load_extension('cogs.role_manager')
    await bot.load_extension('cogs.stats')

# コマンド実行中にエラーが発生した場合のイベント
@bot.event
async def on_error(event, *args, **kwargs):
    # エラーメッセージを取得
    error_message = traceback.format_exc()

    # 「washitatto」のUserオブジェクトを取得
    try:
        washitatto_user = await bot.fetch_user(4110)
        await washitatto_user.send(f"エラーが発生しました:\n```{error_message}```")
    except discord.Forbidden:
        # DMを送れない場合のエラーハンドリング
        print("washitattoにDMを送信できませんでした。")

bot.run(TOKEN)