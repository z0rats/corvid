import React from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LabelList, ResponsiveContainer } from "recharts";

import { modeValue } from "../../../../core/utils/themeUtils";
import LoadingState from "../../../../core/components/ui/LoadingState";
import TrendsBarShape from "./shared/TrendsBarShape";
import TrendsTooltipBox from "./shared/TrendsTooltipBox";

export default function WordFrequencyChart({ data, loading, error, onSelectArticleIds, onBlacklistWord }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();

  const barChartData = Array.isArray(data)
    ? data.map((item, index) => ({
        word: item.word,
        count: item.count,
        color:
          index < 5
            ? modeValue(theme, theme.palette.primary.light, theme.palette.primary.main)
            : modeValue(theme, theme.palette.secondary.light, theme.palette.secondary.main),
        article_ids: item.article_ids || [],
      }))
    : [];

  if (loading) {
    return (
      <Card sx={{ minHeight: "450px", height: "100%" }}>
        <CardContent>
          <Typography variant="h6" color="text.primary" mb={2}>{t('trends.wordFrequency.title')}</Typography>
          <LoadingState minHeight="400px" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ minHeight: "450px", height: "100%" }}>
        <CardContent>
          <Typography variant="h6" color="text.primary" mb={2}>{t('trends.wordFrequency.title')}</Typography>
          <Box height="400px" display="flex" justifyContent="center" alignItems="center">
            <Typography variant="body1" color="text.secondary">
              {t('trends.wordFrequency.noData')}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ minHeight: "450px", height: "100%" }}>
      <CardContent>
        <Typography variant="h6" color="text.primary" mb={2}>{t('trends.wordFrequency.title')}</Typography>
        <Box sx={{ height: "400px" }}>
          {barChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barChartData} margin={{ top: 30, right: 30, bottom: 90, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
                <XAxis
                  dataKey="word"
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
                    const { word, count } = payload[0].payload;
                    return (
                      <TrendsTooltipBox
                        title={word}
                        lines={[
                          { text: t('trends.wordFrequency.occurrences', { count }) },
                          { text: t('trends.wordFrequency.clickToView'), variant: 'caption' },
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
                      onSelect={() => onSelectArticleIds(props.payload.article_ids || [], t('trends.wordFrequency.selectedTitle', { word: props.payload.word }))}
                      onBlacklist={onBlacklistWord ? () => onBlacklistWord(props.payload.word) : null}
                      blacklistTitle={onBlacklistWord ? t('trends.wordFrequency.hideFromTrends', { value: props.payload.word }) : undefined}
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
                {t('trends.wordFrequency.noData')}
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
