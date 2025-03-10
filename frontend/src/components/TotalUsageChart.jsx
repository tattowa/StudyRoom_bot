import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import styled from "styled-components";

const ChartContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

function TotalUsageChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/total-usage", {mode: 'cors'})
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error(err));
  }, []);

  // デフォルトで降順に返ってくる前提
  // 上位3つをハイライトにするなどの例（ここでは単に色を変えるだけ）
  const getBarColor = (index) => {
    if (index === 0) return "gold";
    if (index === 1) return "silver";
    if (index === 2) return "chocolate"; // bronze
    return "#8884d8";
  };

  const chartData = data.map((d, i) => ({
    channel_id: d.channel_id,
    duration_hour: d.duration_hour,
    rank: i + 1
  }));

  return (
    <ChartContainer>
      <BarChart width={600} height={300} data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="channel_id" />
        <YAxis />
        <Tooltip />
        <Bar
          dataKey="duration_hour"
          fill="#8884d8"
          label={{ position: 'top' }}
          isAnimationActive={true}
        >
          {
            chartData.map((entry, index) => (
              <cell key={`cell-${index}`} fill={getBarColor(index)} />
            ))
          }
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}

export default TotalUsageChart;