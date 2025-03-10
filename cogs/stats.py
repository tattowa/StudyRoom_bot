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

    def load_data(self):
        """
        CSVからログを読み込み、timestampをdatetime型にパースして返す。
        CSV例: user_id, channel_id, action, timestamp
        """
        df = pd.read_csv("./data/vc_logs.csv", parse_dates=["timestamp"])
        df.sort_values("timestamp", inplace=True)
        return df

    def calculate_study_sessions(self, df):
        """
        join から leaveまでのVC滞在時間を集計し、
        user_id, channel_id, start_time, end_time, duration(hours) をDataFrameで返す
        """
        sessions = []
        user_sessions = {}  # user_idをキーにして開始時間・チャンネルを記憶

        for _, row in df.iterrows():
            user_id = row["user_id"]
            channel_id = row["channel_id"]
            if row["action"] == "join":
                # join時に記録
                user_sessions[user_id] = {
                    "channel_id": channel_id,
                    "start": row["timestamp"]
                }
            elif row["action"] == "leave" and user_id in user_sessions:
                # leave時に滞在時間を計算
                start_data = user_sessions.pop(user_id)
                if start_data["channel_id"] == channel_id:
                    duration = (row["timestamp"] - start_data["start"]).total_seconds() / 3600
                    sessions.append({
                        "user_id": user_id,
                        "channel_id": channel_id,
                        "start_time": start_data["start"],
                        "end_time": row["timestamp"],
                        "duration": duration
                    })

        df_sessions = pd.DataFrame(sessions)
        return df_sessions

    # ─────────────────────────────────────────────────────
    # (1) 今日のチャンネル使用時間: 棒グラフ
    # ─────────────────────────────────────────────────────
    def get_today_channel_usage(self, df_sessions):
        """
        今日の各チャンネル使用累計時間を取得して返す (単位: 時間)
        """
        today = datetime.date.today()
        # 今日の0:00～23:59の範囲
        start_of_day = datetime(today.year, today.month, today.day)
        end_of_day = start_of_day + timedelta(days=1)

        df_today = df_sessions[
            (df_sessions["start_time"] >= start_of_day) &
            (df_sessions["start_time"] < end_of_day)
        ]
        if df_today.empty:
            return pd.DataFrame()

        # チャンネルごとに合計
        usage_by_channel = df_today.groupby("channel_id")["duration"].sum().reset_index()
        return usage_by_channel

    def plot_today_channel_usage(self, usage_df):
        """
        今日のチャンネル使用時間を棒グラフで可視化し、画像ファイルを保存してパスを返す
        - カラーマップで使用時間が多いほど濃い色
        - 閾値ラインの例として、全チャンネル平均を追加
        """
        # 空チェック
        if usage_df.empty:
            return None

        usage_df.sort_values("duration", inplace=True, ascending=True)

        # カラーマップを使用時間に応じてスケールさせる
        norm = plt.Normalize(usage_df["duration"].min(), usage_df["duration"].max())
        cmap = sns.light_palette("blue", as_cmap=True)

        plt.figure(figsize=(8, 6))
        bar_container = plt.barh(
            usage_df["channel_id"],
            usage_df["duration"],
            color=[cmap(norm(val)) for val in usage_df["duration"]]
        )

        # 使用時間の平均にラインを引く (閾値ライン例)
        avg_usage = usage_df["duration"].mean()
        plt.axvline(avg_usage, color="red", linestyle="--", label=f"平均: {avg_usage:.2f}h")

        plt.title("今日のチャンネル使用時間 (時間)")
        plt.xlabel("使用時間 (時間)")
        plt.legend()

        # 棒に対して値を表示
        for rect, val in zip(bar_container, usage_df["duration"]):
            plt.text(val+0.01, rect.get_y() + rect.get_height()/2,
                    f"{val:.2f}h",
                    va="center", fontsize=8)

        plt.tight_layout()
        img_path = "today_channel_usage.png"
        plt.savefig(img_path, dpi=100)
        plt.close()
        return img_path

    @app_commands.command(name="todays_usage", description="今日のチャンネル使用時間の可視化を表示します。")
    async def todays_usage(self, interaction: discord.Interaction):
        """
        今日一日のチャンネル別使用時間を棒グラフで表示する
        """
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        usage_df = self.get_today_channel_usage(df_sessions)
        if usage_df.empty:
            await interaction.response.send_message("本日はまだチャンネル使用の記録がありません。")
            return

        img_path = self.plot_today_channel_usage(usage_df)
        await interaction.response.send_message(file=discord.File(img_path))

    # ─────────────────────────────────────────────────────
    # (2) 直近1週間の音声チャンネル使用時間: 積み上げ棒グラフ
    # ─────────────────────────────────────────────────────
    def get_weekly_channel_usage(self, df_sessions):
        """
        直近7日間の日付ごとのチャンネル使用時間を集計
        戻り値: pivot_table（日付をindex, channel_idをcolumn, 使用時間合計を値）
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        df_week = df_sessions[
            (df_sessions["start_time"] >= start_date) &
            (df_sessions["start_time"] < end_date)
        ].copy()

        if df_week.empty:
            return pd.DataFrame()

        # 日付ごと・チャンネルごとに集計
        df_week["day"] = df_week["start_time"].dt.date
        pivot_df = df_week.groupby(["day", "channel_id"])["duration"].sum().reset_index()
        pivot_df = pivot_df.pivot(index="day", columns="channel_id", values="duration").fillna(0)

        # 日付が抜けているところを補完（0埋め）
        all_days = [start_date.date() + timedelta(days=i) for i in range(7)]
        pivot_df = pivot_df.reindex(all_days).fillna(0)
        return pivot_df

    def plot_weekly_channel_usage(self, pivot_df):
        """
        直近1週間分のチャンネル使用時間を積み上げ棒グラフで可視化
        ・x軸のラベルで土日を赤字
        ・平均使用時間ライン
        """
        if pivot_df.empty:
            return None

        plt.figure(figsize=(10, 6))

        # 積み上げ棒グラフ
        bottom_vals = np.zeros(len(pivot_df))
        colors = sns.color_palette("hls", n_colors=len(pivot_df.columns))  # チャンネルごとに異なる色
        labels = pivot_df.columns.tolist()

        for i, col in enumerate(labels):
            plt.bar(
                pivot_df.index,
                pivot_df[col],
                bottom=bottom_vals,
                color=colors[i],
                label=col
            )
            bottom_vals += pivot_df[col].values

        # x軸の日付ラベルを土日で赤字にする（祝日は本実装ではAPI等で判断）
        ax = plt.gca()
        for tick_label in ax.get_xticklabels():
            # 文字列からdate型へ変換
            try:
                tick_date = datetime.strptime(tick_label.get_text(), "%Y-%m-%d").date()
                if tick_date.weekday() >= 5:  # 土日
                    tick_label.set_color("red")
            except:
                pass

        plt.xlabel("日付")
        plt.ylabel("使用時間 (時間)")
        plt.title("直近1週間のチャンネル使用時間")

        # 週の合計の平均ライン（総合計 / 7日）
        weekly_total = pivot_df.sum(axis=1).sum()
        avg_per_day = weekly_total / 7.0
        plt.axhline(avg_per_day, color="black", linestyle="--", label=f"平均: {avg_per_day:.2f} h/日")

        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        img_path = "weekly_channel_usage.png"
        plt.savefig(img_path, dpi=100)
        plt.close()
        return img_path

    @app_commands.command(name="weekly_usage", description="直近1週間の音声チャンネル使用時間を表示します。")
    async def weekly_usage(self, interaction: discord.Interaction):
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        pivot_df = self.get_weekly_channel_usage(df_sessions)

        if pivot_df.empty or pivot_df.sum().sum() == 0:
            await interaction.response.send_message("直近1週間のチャンネル使用記録がありません。")
            return

        img_path = self.plot_weekly_channel_usage(pivot_df)
        await interaction.response.send_message(file=discord.File(img_path))

    # ─────────────────────────────────────────────────────
    # (3) これまでのチャンネル使用累計時間: 棒グラフ
    # ─────────────────────────────────────────────────────
    def get_total_channel_usage(self, df_sessions):
        """
        これまでに記録されたチャンネルごとの累計使用時間を取得
        """
        if df_sessions.empty:
            return pd.DataFrame()

        usage_df = df_sessions.groupby("channel_id")["duration"].sum().reset_index()
        usage_df.sort_values("duration", ascending=False, inplace=True)
        return usage_df

    def plot_total_channel_usage(self, usage_df):
        """
        チャンネルごとの累計使用時間を棒グラフで可視化
        ・上位3チャンネルを金銀銅でハイライトする例
        ・バーに時間を表示
        """
        if usage_df.empty:
            return None

        plt.figure(figsize=(8, 6))

        # ハイライトの設定 (金銀銅 + 通常色)
        colors = []
        medals = {0: "gold", 1: "silver", 2: "darkorange"}  # 上位3位のみ
        for i in range(len(usage_df)):
            if i in medals.keys():
                colors.append(medals[i])
            else:
                colors.append("skyblue")

        bar_container = plt.barh(
            usage_df["channel_id"],
            usage_df["duration"],
            color=colors
        )
        plt.xlabel("累計使用時間 (時間)")
        plt.title("これまでのチャンネル使用累計時間")

        # 棒に値を表示 (ツールチップ代わり)
        for rect, val in zip(bar_container, usage_df["duration"]):
            plt.text(val + 0.1, rect.get_y() + rect.get_height()/2,
                    f"{val:.2f}h",
                    va="center")

        plt.tight_layout()
        img_path = "total_channel_usage.png"
        plt.savefig(img_path, dpi=100)
        plt.close()
        return img_path

    @app_commands.command(name="channel_total_usage", description="これまでのチャンネル使用累計時間を表示します。")
    async def channel_total_usage(self, interaction: discord.Interaction):
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        usage_df = self.get_total_channel_usage(df_sessions)

        if usage_df.empty:
            await interaction.response.send_message("チャンネル使用データがありません。")
            return

        img_path = self.plot_total_channel_usage(usage_df)
        await interaction.response.send_message(file=discord.File(img_path))

    # 既存コマンド（studytime, rank, report）もそのまま残す
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
        img_path = "study_time.png"
        plt.savefig(img_path)
        plt.close()
        return img_path

    @app_commands.command(name="rank", description="サーバー内の学習時間ランキングを表示します。")
    async def rank(self, interaction: discord.Interaction):
        df_logs = self.load_data()
        df_sessions = self.calculate_study_sessions(df_logs)
        ranking_text = self.generate_ranking(df_sessions)
        await interaction.response.send_message(f"**📊 学習時間ランキング**\n{ranking_text}")

    def generate_ranking(self, df):
        ranking = df.groupby("user_id")["duration"].sum().sort_values(ascending=False)
        ranking_text = "\n".join([
            f"{idx + 1}位: <@{user}> - {duration:.2f} 時間"
            for idx, (user, duration) in enumerate(ranking.head(3).items())
        ])
        return ranking_text

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



