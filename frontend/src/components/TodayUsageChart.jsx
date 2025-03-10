import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";
import styled from "styled-components";

const ChartContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

function TodayUsageChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/today-usage", { mode: 'cors' })
      .then((res) => res.json())
      .then((json) => {
        setData(json);
      })
      .catch((err) => console.error(err));
  }, []);

  // 平均値ラインを引く場合
  const average = data.length > 0
    ? data.reduce((acc, cur) => acc + cur.duration_hour, 0) / data.length
    : 0;

  return (
    <ChartContainer>
      <BarChart width={600} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="channel_id" />
        <YAxis />
        <Tooltip />
        {/* 参考線: 平均 */}
        <ReferenceLine y={average} stroke="red" label={`平均 ${average.toFixed(2)}h`} />
        <Bar dataKey="duration_hour" fill="#8884d8" />
      </BarChart>
    </ChartContainer>
  );
}

export default TodayUsageChart;