import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import styled from "styled-components";
import channelColors from "../config/channelColors.json"


const ChartContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 800px;
  margin: auto;
`;

function WeeklyUsageChart() {
  const [data, setData] = useState([]);
  const [averageUsage, setAverageUsage] = useState(0);
  const [channelColorMapping, setChannelColorMapping] = useState({});

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/weekly-usage", { mode: "cors" })
      .then((res) => res.json())
      .then((json) => {
        const today = new Date();
        const last7Days = [...Array(7)].map((_, i) => {
          const d = new Date();
          d.setDate(today.getDate() - (6 - i));
          return d.toISOString().split("T")[0];
        });

        const pivot = last7Days.reduce((acc, date) => {
          acc[date] = { date };
          return acc;
        }, {});
        
        let totalHours = 0;
        const chMapping = {};

        json.forEach(({ date, channel_id, channel_name, duration_hour }) => {
          if (!pivot[date]) pivot[date] = { date };
          pivot[date][channel_name] = duration_hour;
          totalHours += duration_hour;
          chMapping[channel_name] = channel_id;
        });

        setAverageUsage(totalHours / 7);

        // channel_name → color マッピングを作成
        const chColorMapping = Object.fromEntries(
            Object.keys(chMapping).map((chName) => [
              chName,
              channelColors[chMapping[chName]] || "#cccccc",
            ])
          );
        setChannelColorMapping(chColorMapping);
        setData(Object.values(pivot));
      })
      .catch(console.error);
  }, []);

  // X軸のラベル描画
  const renderDateTick = ({ x, y, payload }) => {
    const day = new Date(payload.value).getDay();
    return (
      <g transform={`translate(${x}, ${y})`}>
        <text x={0} y={0} dy={16} textAnchor="middle" fill={day === 0 || day === 6 ? "red" : "black"}>
          {payload.value}
        </text>
      </g>
    );
  };

  const channelKeys = Array.from(
    new Set(data.flatMap((item) => Object.keys(item).filter((key) => key !== "date")))
  );

  return (
    <ChartContainer>
      <h3>📦 週間チャンネル使用時間</h3>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={renderDateTick} interval={0} angle={-30} dx={-10} dy={5} />
          <YAxis label={{ value: "使用時間 (時間)", angle: -90, position: "insideLeft" }} />
          <Tooltip />
          <Legend />
          <ReferenceLine y={averageUsage} stroke="red" strokeDasharray="3 3" label="平均" />
          {channelKeys.map((chName) => (
            <Bar key={chName} dataKey={chName} stackId="weekly" fill={channelColorMapping[chName]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}

export default WeeklyUsageChart;
