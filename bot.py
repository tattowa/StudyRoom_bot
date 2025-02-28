import discord
from discord.ext import commands
import traceback
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected')
    await bot.tree.sync()  # スラッシュコマンドを同期
    print(f'{bot.user}としてログインしました。')
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
        washitatto_user = await bot.fetch_user(556332871560986663)

        # メッセージが2000文字を超えている場合は分割して送信
        while len(error_message) > 1900:
            await washitatto_user.send(f"エラーが発生しました:\n```{error_message[:1900]}```")
            error_message = error_message[1900:]  # 残りのメッセージを次に送信

        # 残りのエラーメッセージを送信
        if error_message:
            await washitatto_user.send(f"エラーが発生しました:\n```{error_message}```")
            
    except discord.Forbidden:
        # DMを送れない場合のエラーハンドリング
        print("washitattoにDMを送信できませんでした。")

@bot.event
async def on_command_error(ctx, error):
    # コマンドエラーのメッセージを取得
    error_message = str(error)  # `error` オブジェクトからエラーメッセージを取得

    try:
        washitatto_user = await bot.fetch_user(556332871560986663)

        # メッセージが2000文字を超えている場合は分割して送信
        while len(error_message) > 1900:
            await washitatto_user.send(f"コマンドエラーが発生しました:\n```{error_message[:1900]}```")
            error_message = error_message[1900:]  # 残りのメッセージを次に送信

        # 残りのエラーメッセージを送信
        if error_message:
            await washitatto_user.send(f"コマンドエラーが発生しました:\n```{error_message}```")

    except discord.Forbidden:
        print("washitattoにDMを送信できませんでした。")

    # ユーザーにコマンドエラーを通知
    await ctx.send("コマンド実行中にエラーが発生しました。")

bot.run(TOKEN)
