import React, { useEffect, useState } from "react";

function RankingChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/ranking",{mode: 'cors'})
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div>
      <h3>チャンネル使用量ランキング Top 10</h3>
      <table border="1" cellPadding="6" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Channel ID</th>
            <th>Duration (h)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={row.channel_id}>
              <td>{row.rank}</td>
              <td>{row.channel_id}</td>
              <td>{row.duration_hour.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RankingChart;
