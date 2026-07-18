import React, { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { ResponsiveBar } from "@nivo/bar";

import { createChartTheme } from "../../utils/chartTheme";
import { modeValue } from "../../../../core/utils/themeUtils";
import LoadingState from "../../../../core/components/ui/LoadingState";

function BlacklistLayer({ bars, onBlacklist, t }) {
  return bars.map((bar) => {
    const x = bar.x + bar.width / 2;
    const y = bar.y + bar.height + 12;

    return (
      <Tooltip key={`blacklist-${bar.key}`} title={t('trends.wordFrequency.hideFromTrends', { value: bar.data.indexValue })} arrow placement="bottom">
        <g
          transform={`translate(${x}, ${y})`}
          onClick={(e) => {
            e.stopPropagation();
            onBlacklist(bar.data.indexValue);
          }}
          style={{ cursor: "pointer" }}
        >
          <circle r={8} fill="transparent" />
          <text
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={12}
            fill="currentColor"
            opacity={0.4}
          >
            ✕
          </text>
        </g>
      </Tooltip>
    );
  });
}

export default function WordFrequencyChart({ data, loading, error, onSelectArticleIds, onBlacklistWord }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const chartTheme = createChartTheme(theme);

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

  const blacklistLayer = useCallback(
    (props) => <BlacklistLayer {...props} onBlacklist={onBlacklistWord} t={t} />,
    [onBlacklistWord, t]
  );

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
        <Box height="400px">
          {barChartData.length > 0 ? (
            <ResponsiveBar
              data={barChartData}
              keys={["count"]}
              indexBy="word"
              margin={{ top: 50, right: 60, bottom: 100, left: 80 }}
              padding={0.3}
              valueScale={{ type: "linear" }}
              colors={({ data }) => data.color}
              borderColor={{ from: "color", modifiers: [["darker", modeValue(theme, 0.6, 1.6)]] }}
              axisTop={null}
              axisRight={null}
              theme={chartTheme}
              axisBottom={{ tickSize: 5, tickPadding: 26, tickRotation: -45, legendPosition: "middle", legendOffset: 100 }}
              axisLeft={{ tickSize: 5, tickPadding: 8, tickRotation: 0, legendPosition: "middle", legendOffset: -60 }}
              labelSkipWidth={12}
              labelSkipHeight={12}
              onClick={(node) => onSelectArticleIds(node.data.article_ids || [], t('trends.wordFrequency.selectedTitle', { word: node.data.word }))}
              borderRadius={4}
              layers={["grid", "axes", "bars", "markers", "legends", "annotations", ...(onBlacklistWord ? [blacklistLayer] : [])]}
              tooltip={({ value, indexValue }) => (
                <Box bgcolor="background.paper" p={1.5} border={1} borderColor="divider" borderRadius={1}>
                  <Typography variant="body2" color="text.primary" fontWeight="medium">{indexValue}</Typography>
                  <Typography variant="body2" color="text.secondary">{t('trends.wordFrequency.occurrences', { count: value })}</Typography>
                  <Typography variant="caption" color="text.secondary">{t('trends.wordFrequency.clickToView')}</Typography>
                </Box>
              )}
              role="application"
              aria-label="Word frequency bar chart"
            />
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
