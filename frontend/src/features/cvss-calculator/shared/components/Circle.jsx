import React from "react";
import { PieChart, Pie, ResponsiveContainer } from "recharts";
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { getFillColor } from "../utils/scoreUtils";

export default function Circle({ value }) {
  const theme = useTheme();
  const chart = theme.palette.chart;
  const data = [{ value: value }, { value: 10 - value, fill: chart.inactive }];

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          startAngle={90}
          endAngle={-270}
          innerRadius="80%"
          outerRadius="100%"
          minAngle={1}
          domain={[0, 10]}
          stroke="none"
          strokeWidth={0}
          fill={getFillColor(value, chart)}
        />
        <foreignObject
          width="100%"
          height="100%"
          style={{ textAlign: "center" }}
        >
          <Typography
            variant="h4"
            color="text.secondary"
            sx={{
              display: "inline-block",
              position: "relative",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          >
            {value}
          </Typography>
        </foreignObject>
      </PieChart>
    </ResponsiveContainer>
  );
}
