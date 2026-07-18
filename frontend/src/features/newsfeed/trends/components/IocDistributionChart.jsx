import React from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

import { useIocDistribution } from "../../hooks/api/useTrendsApi";
import { getCategoricalColor } from "../../../../core/utils/chartColors";
import LoadingState from "../../../../core/components/ui/LoadingState";
import TrendsTooltipBox from "./shared/TrendsTooltipBox";

export default function IocDistributionChart({ timeRange, refreshKey }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const { data, loading } = useIocDistribution(timeRange, refreshKey);

  if (loading) {
    return <LoadingState minHeight="350px" />;
  }

  return (
    <Card sx={{ minHeight: "450px", height: "100%" }}>
      <CardContent>
        <Typography variant="h6" color="text.primary" mb={2}>
          {t('trends.iocDistribution.title')}
        </Typography>
        <Box sx={{ height: "400px" }}>
          {data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="label"
                  innerRadius="45%"
                  outerRadius="70%"
                  paddingAngle={2}
                  cornerRadius={5}
                  stroke={theme.palette.background.paper}
                  strokeWidth={2}
                  isAnimationActive={false}
                >
                  {data.map((entry, index) => (
                    <Cell key={entry.id} fill={getCategoricalColor(theme, index)} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const { label, value } = payload[0].payload;
                    return (
                      <TrendsTooltipBox
                        title={label}
                        lines={[{ text: t('trends.iocDistribution.totalOccurrences', { count: value }) }]}
                      />
                    );
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  align="center"
                  iconType="circle"
                  wrapperStyle={{ color: theme.palette.text.secondary, fontSize: 13 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <Box display="flex" justifyContent="center" alignItems="center" height="100%">
              <Typography variant="body1" color="text.secondary">
                {t('trends.iocDistribution.noData')}
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
