import React, { useState } from "react";
import styled from "styled-components";

/*
  月次レポートは年月を指定 → /api/v1/monthly-report?year=XXXX&month=XX を取得。

  例レスポンス:
  {
    "total_hour": 12.3,
    "daily_usage": [
       {"date": "2025-02-01", "duration_hour": 1.2},
       {"date": "2025-02-02", "duration_hour": 0.5},
       ...
    ]
  }
*/

const ReportContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
`;

function MonthlyReport() {
  const [year, setYear] = useState(2025);
  const [month, setMonth] = useState(2);
  const [report, setReport] = useState(null);

  const handleSubmit = () => {
    fetch(`http://localhost:8000/api/v1/monthly-report?year=${year}&month=${month}`, { mode: 'cors' })
      .then((res) => res.json())
      .then((json) => {
        setReport(json);
      })
      .catch((err) => console.error(err));
  };

  return (
    <ReportContainer>
      <div style={{ marginBottom: "10px" }}>
        <label>
          Year:
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            style={{ width: "80px", marginLeft: "5px" }}
          />
        </label>
        <label style={{ marginLeft: "10px" }}>
          Month:
          <input
            type="number"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            style={{ width: "50px", marginLeft: "5px" }}
          />
        </label>
        <button style={{ marginLeft: "10px" }} onClick={handleSubmit}>
          レポート取得
        </button>
      </div>
      {report && (
        <div>
          <p>合計時間: {report.total_hour.toFixed(2)} h</p>
          <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Duration (h)</th>
              </tr>
            </thead>
            <tbody>
              {report.daily_usage.map((row) => (
                <tr key={row.date}>
                  <td>{row.date}</td>
                  <td>{row.duration_hour.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!report && <p>月次レポートを取得してください。</p>}
    </ReportContainer>
  );
}

export default MonthlyReport;