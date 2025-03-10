import React from "react";
import TodayUsageChart from "./components/TodayUsageChart";
import WeeklyUsageChart from "./components/WeeklyUsageChart.jsx";
import TotalUsageChart from "./components/TotalUsageChart";
import RankingChart from "./components/RankingChart";
import MonthlyReport from "./components/MonthlyReport";

function App() {
  return (
    <div style={{ margin: "20px" }}>
      <h1>Discord VC Usage Dashboard</h1>
      <hr />
      <h2>(1) 今日の使用時間</h2>
      <TodayUsageChart />
      <hr />
      <h2>(2) 直近1週間の使用時間</h2>
      <WeeklyUsageChart />
      <hr />
      <h2>(3) 全期間の累計時間</h2>
      <TotalUsageChart />
      <hr />
      <h2>(4) チャンネル使用量ランキング</h2>
      <RankingChart />
      <hr />
      <h2>(5) 月次レポート</h2>
      <MonthlyReport />
    </div>
  );
}

export default App;