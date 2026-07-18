import React from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LabelList, ResponsiveContainer } from "recharts";

import { useTopCves } from "../../hooks/api/useTrendsApi";
import { modeValue } from "../../../../core/utils/themeUtils";
import LoadingState from "../../../../core/components/ui/LoadingState";
import TrendsBarShape from "./shared/TrendsBarShape";
import TrendsTooltipBox from "./shared/TrendsTooltipBox";

export default function CveStatistics({ timeRange, refreshKey, onSelectArticleIds }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const { data, loading } = useTopCves(timeRange, refreshKey);

  const barChartData = Array.isArray(data)
    ? data.map((item) => ({
        value: item.value,
        count: item.count,
        color: modeValue(theme, theme.palette.error.light, theme.palette.error.dark),
        article_ids: item.article_ids || [],
      }))
    : [];

  if (loading) {
    return <LoadingState minHeight="250px" />;
  }

  return (
    <Card sx={{ minHeight: "450px", height: "100%" }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" color="text.primary">
            {t('trends.cve.title')}
          </Typography>
        </Box>

        <Box sx={{ height: "400px" }}>
          {barChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barChartData} margin={{ top: 20, right: 30, bottom: 80, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
                <XAxis
                  dataKey="value"
                  angle={-45}
                  textAnchor="end"
                  tickMargin={20}
                  interval={0}
                  tick={{ fontSize: 12, fill: theme.palette.text.primary }}
                  axisLine={{ stroke: theme.palette.divider }}
                  tickLine={{ stroke: theme.palette.divider }}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                  axisLine={{ stroke: theme.palette.divider }}
                  tickLine={{ stroke: theme.palette.divider }}
                />
                <Tooltip
                  cursor={{ fill: theme.palette.action.hover }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const { value, count } = payload[0].payload;
                    return (
                      <TrendsTooltipBox
                        title={value}
                        lines={[
                          { text: t('trends.cve.occurrences', { count }) },
                          { text: t('trends.cve.clickToView'), variant: 'caption' },
                        ]}
                      />
                    );
                  }}
                />
                <Bar
                  dataKey="count"
                  isAnimationActive={false}
                  shape={(props) => (
                    <TrendsBarShape
                      {...props}
                      onSelect={() => onSelectArticleIds(props.payload.article_ids || [], t('trends.cve.selectedTitle', { value: props.payload.value }))}
                    />
                  )}
                >
                  <LabelList dataKey="count" position="top" style={{ fontSize: 12, fill: theme.palette.text.primary }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <Box display="flex" justifyContent="center" alignItems="center" height="100%">
              <Typography variant="body1" color="text.secondary">
                {t('trends.cve.noData')}
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
