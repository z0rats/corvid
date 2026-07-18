import React from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { ResponsiveBar } from "@nivo/bar";

import { useTopCves } from "../../hooks/api/useTrendsApi";
import { createChartTheme } from "../../utils/chartTheme";
import { modeValue } from "../../../../core/utils/themeUtils";
import LoadingState from "../../../../core/components/ui/LoadingState";

export default function CveStatistics({ timeRange, refreshKey, onSelectArticleIds }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const { data, loading } = useTopCves(timeRange, refreshKey);
  const chartTheme = createChartTheme(theme);

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

        <Box height="400px">
          {barChartData.length > 0 ? (
            <ResponsiveBar
              data={barChartData}
              keys={["count"]}
              indexBy="value"
              margin={{ top: 20, right: 30, bottom: 100, left: 80 }}
              padding={0.3}
              valueScale={{ type: "linear" }}
              colors={({ data }) => data.color}
              borderColor={{ from: "color", modifiers: [["darker", modeValue(theme, 0.6, 1.6)]] }}
              axisTop={null}
              axisRight={null}
              theme={chartTheme}
              axisBottom={{ tickSize: 5, tickPadding: 12, tickRotation: -45, legendPosition: "middle", legendOffset: 90 }}
              axisLeft={{ tickSize: 5, tickPadding: 8, tickRotation: 0, legendPosition: "middle", legendOffset: -60 }}
              labelSkipWidth={12}
              labelSkipHeight={12}
              onClick={(node) => onSelectArticleIds(node.data.article_ids || [], t('trends.cve.selectedTitle', { value: node.data.value }))}
              borderRadius={4}
              tooltip={({ value, indexValue }) => (
                <Box bgcolor="background.paper" p={1.5} border={1} borderColor="divider" borderRadius={1}>
                  <Typography variant="body2" color="text.primary" fontWeight="medium">{indexValue}</Typography>
                  <Typography variant="body2" color="text.secondary">{t('trends.cve.occurrences', { count: value })}</Typography>
                  <Typography variant="caption" color="text.secondary">{t('trends.cve.clickToView')}</Typography>
                </Box>
              )}
              role="application"
              aria-label="Top CVEs bar chart"
            />
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
