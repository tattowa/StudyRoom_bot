from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import pandas as pd
from datetime import datetime, date, timedelta
import os

app = FastAPI()

# CORS の設定（localhost:3000 のみ許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # フロントエンドのオリジンを制限
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 必要なメソッドのみ許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

DATA_PATH = os.path.join("..", "data", "vc_logs.csv")  # ../data/vc_logs.csv を想定

class ChannelUsage(BaseModel):
    channel_id: int
    channel_name: str
    duration_hour: float

def load_data() -> pd.DataFrame:
    """
    CSVを読み込み、必要なら日時をdatetime型にパース。
    """
    if not os.path.exists(DATA_PATH):
        # CSVが存在しない場合は空のDataFrameを返す
        columns = ["user_id", "timestamp", "action", "channel_id", "channel_name"]
        return pd.DataFrame([], columns=columns)
    df = pd.read_csv(DATA_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    return df

def calculate_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """
    join と leave のペアからボイスチャット滞在時間を計算。
    結果として
      user_id, channel_id, start_time, end_time, duration_hour
    のデータを返す。
    """
    if df.empty:
        return pd.DataFrame(columns=["user_id", "channel_id", "channel_name", "start_time", "end_time", "duration_hour"])

    sessions = []
    user_in_channel = {}  # user_id: {"channel_id": x, "channel_name": y, "joined": time}

    for _, row in df.iterrows():
        uid = row["user_id"]
        ch = row["channel_id"]
        ch_name = row["channel_name"]
        act = row["action"]
        ts = row["timestamp"]
        if act == "join":
            user_in_channel[uid] = {
                "channel_id": ch,
                "channel_name": ch_name,
                "joined": ts
            }
        elif act == "leave":
            if uid in user_in_channel:
                # join時刻からの差分を計算
                start_t = user_in_channel[uid]["joined"]
                if user_in_channel[uid]["channel_id"] == ch:
                    duration_sec = (ts - start_t).total_seconds()
                    duration_hour = duration_sec / 3600.0
                    sessions.append({
                        "user_id": uid,
                        "channel_id": ch,
                        "channel_name": ch_name,
                        "start_time": start_t,
                        "end_time": ts,
                        "duration_hour": duration_hour
                    })
                # leave後は状態を削除
                del user_in_channel[uid]

    return pd.DataFrame(sessions)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/api/v1/today-usage", response_model=List[ChannelUsage])
def get_today_usage():
    df = load_data()
    df_sessions = calculate_sessions(df)
    if df_sessions.empty:
        return []

    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = start_of_day + timedelta(days=1)
    df_today = df_sessions[
        (df_sessions["start_time"] >= start_of_day) & 
        (df_sessions["start_time"] < end_of_day)
    ]
    # チャンネルごとの合計時間
    usage = df_today.groupby(["channel_id", "channel_name"])["duration_hour"].sum().reset_index()
    usage_list = []
    for _, row in usage.iterrows():
        usage_list.append(ChannelUsage(
            channel_id=int(row["channel_id"]),
            channel_name=row["channel_name"],
            duration_hour=float(row["duration_hour"])
        ))
    return usage_list

@app.get("/api/v1/weekly-usage")
def get_weekly_usage():
    """
    直近1週間の日付・チャンネル別利用時間を返す。
    React側で積み上げ棒グラフにしやすい形式。
    レスポンス例:
    [
      {"date": "2025-02-22", "channel_id": 12345, "channel_name": "channel_name", "duration_hour": 1.2},
      ...
    ]
    """
    df = load_data()
    df_sessions = calculate_sessions(df)
    if df_sessions.empty:
        return []

    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=7)
    df_week = df_sessions[
        (df_sessions["start_time"] >= start_dt) &
        (df_sessions["start_time"] < end_dt)
    ].copy()
    df_week["date"] = df_week["start_time"].dt.date
    grp = df_week.groupby(["date", "channel_id", "channel_name"])["duration_hour"].sum().reset_index()

    result = []
    for _, row in grp.iterrows():
        result.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "channel_id": int(row["channel_id"]),
            "channel_name": row["channel_name"],
            "duration_hour": float(row["duration_hour"])
        })
    return result

@app.get("/api/v1/total-usage", response_model=List[ChannelUsage])
def get_total_usage():
    """
    全期間のチャンネル累計利用時間を返す
    """
    df = load_data()
    df_sessions = calculate_sessions(df)
    if df_sessions.empty:
        return []

    usage = df_sessions.groupby(["channel_id", "channel_name"])["duration_hour"].sum().reset_index()
    usage.sort_values("duration_hour", ascending=False, inplace=True)

    result = []
    for _, row in usage.iterrows():
        result.append(ChannelUsage(
            channel_id=int(row["channel_id"]),
            channel_name=row["channel_name"],
            duration_hour=float(row["duration_hour"])
        ))
    return result

@app.get("/api/v1/ranking")
def get_ranking():
    """
    チャンネル使用量ランキング(上位10件など)を返す例
    [ {channel_id, channel_name, duration_hour}, ... ]
    """
    df = load_data()
    df_sessions = calculate_sessions(df)
    if df_sessions.empty:
        return []

    usage = df_sessions.groupby(["channel_id", "channel_name"])["duration_hour"].sum().reset_index()
    usage.sort_values("duration_hour", ascending=False, inplace=True)

    # 上位10位のみ
    usage_top = usage.head(10)
    result = []
    for i, row in usage_top.iterrows():
        result.append({
            "rank": i+1,
            "channel_id": int(row["channel_id"]),
            "channel_name": row["channel_name"],
            "duration_hour": float(row["duration_hour"])
        })
    return result

@app.get("/api/v1/monthly-report")
def get_monthly_report(year: int, month: int):
    """
    指定された年・月の合計時間・日毎のデータなどを返す例
    {
      "total_hour": 10.5,
      "daily_usage": [
         {"date": "2025-02-01", "duration_hour": 1.2},
         ...
      ]
    }
    """
    df = load_data()
    df_sessions = calculate_sessions(df)
    if df_sessions.empty:
        return {"total_hour": 0.0, "daily_usage": []}

    start_dt = datetime(year, month, 1)
    # 次月1日を求めるため、+32日してday=1にする簡易ロジック
    end_dt = (start_dt + timedelta(days=32)).replace(day=1)

    df_month = df_sessions[
        (df_sessions["start_time"] >= start_dt) &
        (df_sessions["start_time"] < end_dt)
    ].copy()

    if df_month.empty:
        return {"total_hour": 0.0, "daily_usage": []}

    total_hour = df_month["duration_hour"].sum()

    df_month["date"] = df_month["start_time"].dt.date
    daily_grp = df_month.groupby("date")["duration_hour"].sum().reset_index()

    daily_list = []
    for _, row in daily_grp.iterrows():
        daily_list.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "duration_hour": float(row["duration_hour"])
        })

    return {
        "total_hour": float(total_hour),
        "daily_usage": daily_list
    }

# サーバー起動は、以下コマンドなどで行う
# uvicorn main:app --reload --port 8000