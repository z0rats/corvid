import React, { useMemo } from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import ChartTooltip from './ChartTooltip';
import { buildCvss31ChartData } from '../../cvss-3.1/utils/chartDataBuilder';
import { buildCvss40ChartData } from '../../cvss-4.0/utils/chartDataBuilder';

export default function EnhancedSpiderChart({
  version,
  metrics,
  scores,
  title = "CVSS Metrics Visualization",
  height = 400,
}) {
  const theme = useTheme();

  const chartData = useMemo(() => {
    if (version === '3.1') return buildCvss31ChartData(metrics, scores);
    if (version === '4.0') return buildCvss40ChartData(metrics, scores);
    return [];
  }, [version, metrics, scores]);

  return (
    <Box sx={{ width: '100%', height }}>
      <Typography variant="h6" align="center" gutterBottom>
        {title}
      </Typography>
      <ResponsiveContainer width="100%" height="90%">
        <RadarChart data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
          <PolarGrid
            stroke={theme.palette.divider}
            strokeDasharray="3 3"
          />
          <PolarAngleAxis
            dataKey="subject"
            tick={{
              fontSize: 12,
              fill: theme.palette.text.primary,
            }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 10]}
            tick={{
              fontSize: 10,
              fill: theme.palette.text.secondary,
            }}
            tickCount={6}
          />
          <Radar
            name="CVSS Metrics"
            dataKey="normalizedScore"
            stroke={theme.palette.primary.main}
            fill={theme.palette.primary.main}
            fillOpacity={0.3}
            strokeWidth={2}
            dot={{
              r: 4,
              fill: theme.palette.primary.main,
              strokeWidth: 2,
              stroke: theme.palette.background.paper,
            }}
          />
          <Tooltip content={<ChartTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </Box>
  );
}
