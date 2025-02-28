import discord
from discord.ext import commands
from discord import app_commands
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib
from datetime import datetime, timedelta

sns.set(style="whitegrid")
japanize_matplotlib.japanize()

class StudyTimeTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def plot_study_time(self, df, user_id=None, period="D"):
        if user_id:
            df = df[df["user_id"] == user_id]

        if df.empty:
            return None

        df_grouped = df.groupby(pd.Grouper(key="start_time", freq=period)).sum(numeric_only=True)
        plt.figure(figsize=(10, 5))
        df_grouped["duration"].plot(kind="line", color="skyblue")
        plt.title("学習時間の推移")
        plt.ylabel("学習時間 (時間)")
        plt.xlabel("日付" if period == "D" else "週")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("study_time.png")
        plt.close()
        return "study_time.png"

    def generate_ranking(self, df):
        ranking = df.groupby("user_id")["duration"].sum().sort_values(ascending=False)
        ranking_text = "\n".join([
            f"{idx + 1}位: <@{user}> - {duration:.2f} 時間"
            for idx, (user, duration) in enumerate(ranking.head(3).items())
        ])
        return ranking_text

    def assign_title(self, df, user_id):
        one_week_ago = datetime.now() - timedelta(days=7)
        df_week = df[(df["user_id"] == user_id) & (df["start_time"] >= one_week_ago)]
        total_hours = df_week["duration"].sum()

        if total_hours > 14:
            return "Master"
        elif total_hours > 7:
            return "Expert"
        else:
            return "Beginner"

    @app_commands.command(name="studytime", description="指定したユーザーの学習時間を集計してグラフを表示します。")
    @app_commands.describe(user="対象ユーザー", period="集計期間: D(日)、W(週)、M(月)")
    async def studytime(self, interaction: discord.Interaction, user: discord.Member = None, period: str = "D"):
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        img_path = self.plot_study_time(df_sessions, user.id if user else None, period)

        if img_path:
            await interaction.response.send_message(file=discord.File(img_path))
        else:
            await interaction.response.send_message("指定された期間に学習記録がありません。")

    @app_commands.command(name="rank", description="サーバー内の学習時間ランキングを表示します。")
    async def rank(self, interaction: discord.Interaction):
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        ranking_text = self.generate_ranking(df_sessions)
        await interaction.response.send_message(f"**📊 学習時間ランキング**\n{ranking_text}")

    @app_commands.command(name="report", description="月次レポートを生成して表示します。")
    @app_commands.describe(year="対象年", month="対象月")
    async def report(self, interaction: discord.Interaction, year: int, month: int):
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        start_date = datetime(year, month, 1)
        end_date = (start_date + timedelta(days=32)).replace(day=1)
        df_month = df_sessions[(df_sessions["start_time"] >= start_date) & (df_sessions["start_time"] < end_date)]

        if df_month.empty:
            await interaction.response.send_message("指定された月に学習記録がありません。")
            return

        img_path = self.plot_study_time(df_month, period="D")
        total_hours = df_month["duration"].sum()
        avg_hours = df_month["duration"].mean()
        max_hours = df_month["duration"].max()

        report_text = (
            f"📅 **{year}年{month}月の学習レポート**\n"
            f"- 総学習時間: {total_hours:.2f} 時間\n"
            f"- 平均学習時間: {avg_hours:.2f} 時間/セッション\n"
            f"- 最長学習時間: {max_hours:.2f} 時間"
        )

        await interaction.response.send_message(report_text)
        await interaction.followup.send(file=discord.File(img_path))

async def setup(bot):
    await bot.add_cog(StudyTimeTracker(bot))
    await bot.tree.sync()
