from discord.ext import commands, tasks
import discord
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

sns.set(style="whitegrid", palette="pastel")

class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = 'data/vc_logs.csv'
        self.ensure_csv()

    def ensure_csv(self):
        try:
            pd.read_csv(self.data_file)
        except FileNotFoundError:
            df = pd.DataFrame(columns=['user_id', 'timestamp', 'action', 'channel'])
            df.to_csv(self.data_file, index=False)

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
        elif before.channel and not after.channel:
            entry = {
                'user_id': member.id,
                'timestamp': datetime.datetime.now(),
                'action': 'leave',
                'channel': before.channel.name
            }
            df = pd.DataFrame([entry])
            df.to_csv(self.data_file, mode='a', header=False, index=False)

    @commands.command()
    async def show_study_stats(self, ctx):
        """勉強記録の可視化を表示します。"""
        df = pd.read_csv(self.data_file, parse_dates=["timestamp"])
        
        df = df.sort_values("timestamp")
        df["date"] = df["timestamp"].dt.date
        df["hour"] = df["timestamp"].dt.hour

        sessions = []
        active_sessions = {}
        for _, row in df.iterrows():
            if row["action"] == "join":
                active_sessions[row["user_id"]] = row["timestamp"]
            elif row["action"] == "leave" and row["user_id"] in active_sessions:
                start_time = active_sessions.pop(row["user_id"])
                duration = (row["timestamp"] - start_time).total_seconds() / 3600
                sessions.append([row["user_id"], start_time.date(), start_time.hour, duration])

        session_df = pd.DataFrame(sessions, columns=["user_id", "date", "hour", "study_duration"])
        if session_df.empty:
            await ctx.send("📉 記録された勉強データがありません。")
            return

        daily_study = session_df.groupby("date")["study_duration"].sum().reset_index()
        session_df["week"] = pd.to_datetime(session_df["date"]).dt.isocalendar().week
        weekly_study = session_df.groupby("week")["study_duration"].sum().reset_index()
        heatmap_data = session_df.groupby(["date", "hour"])["study_duration"].sum().unstack(fill_value=0)

        fig, axs = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("📚 勉強記録の可視化", fontsize=20)

        sns.barplot(x="date", y="study_duration", data=daily_study, ax=axs[0, 0], color="#89CFF0")
        axs[0, 0].set_title("日次勉強時間")
        axs[0, 0].set_xlabel("日付")
        axs[0, 0].set_ylabel("時間 (h)")
        axs[0, 0].tick_params(axis='x', rotation=45)

        sns.lineplot(x="week", y="study_duration", data=weekly_study, ax=axs[0, 1], marker="o", color="#FF6961")
        axs[0, 1].set_title("週次勉強時間の推移")
        axs[0, 1].set_xlabel("週")
        axs[0, 1].set_ylabel("時間 (h)")

        daily_study["cumulative"] = daily_study["study_duration"].cumsum()
        sns.lineplot(x="date", y="cumulative", data=daily_study, ax=axs[1, 0], marker="o", color="#77DD77")
        axs[1, 0].set_title("累積勉強時間")
        axs[1, 0].set_xlabel("日付")
        axs[1, 0].set_ylabel("累積時間 (h)")
        axs[1, 0].tick_params(axis='x', rotation=45)

        sns.heatmap(heatmap_data, cmap="YlGnBu", ax=axs[1, 1])
        axs[1, 1].set_title("時間帯ごとの学習活動量")
        axs[1, 1].set_xlabel("時間帯")
        axs[1, 1].set_ylabel("日付")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        file = discord.File(fp=buffer, filename='study_stats.png')
        await ctx.send(file=file)

async def setup(bot):
    await bot.add_cog(VCTracker(bot))