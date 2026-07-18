import React, { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { ResponsiveBar } from "@nivo/bar";

import { useTopIocs } from "../../hooks/api/useTrendsApi";
import { createChartTheme } from "../../utils/chartTheme";
import { IOC_TYPE_SELECT_OPTIONS } from "../../constants/newsfeedConstants";
import LoadingState from "../../../../core/components/ui/LoadingState";

function BlacklistLayer({ bars, onBlacklist, t }) {
  return bars.map((bar) => {
    const x = bar.x + bar.width / 2;
    const y = bar.y + bar.height + 12;

    return (
      <Tooltip key={`blacklist-${bar.key}`} title={t('trends.ioc.hideFromTrends', { value: bar.data.indexValue })} arrow placement="bottom">
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

export default function IocStatistics({ timeRange, refreshKey, onSelectArticleIds, onBlacklistIoc }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const [selectedIocType, setSelectedIocType] = useState("ips");
  const { data, loading } = useTopIocs(selectedIocType, timeRange, refreshKey);
  const chartTheme = createChartTheme(theme);

  const barChartData = Array.isArray(data)
    ? data.map((item) => ({
        value: item.value,
        count: item.count,
        color: theme.palette.mode === "dark" ? theme.palette.success.light : theme.palette.success.main,
        article_ids: item.article_ids || [],
      }))
    : [];

  const blacklistLayer = useCallback(
    (props) => <BlacklistLayer {...props} onBlacklist={onBlacklistIoc} t={t} />,
    [onBlacklistIoc, t]
  );

  if (loading) {
    return <LoadingState minHeight="250px" />;
  }

  return (
    <Card sx={{ minHeight: "450px", height: "100%" }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" color="text.primary">
            {t('trends.ioc.title')}
          </Typography>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>{t('trends.ioc.type')}</InputLabel>
            <Select value={selectedIocType} label={t('trends.ioc.type')} onChange={(e) => setSelectedIocType(e.target.value)}>
              {IOC_TYPE_SELECT_OPTIONS.map((type) => (
                <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
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
              borderColor={{ from: "color", modifiers: [["darker", theme.palette.mode === "dark" ? 0.6 : 1.6]] }}
              axisTop={null}
              axisRight={null}
              theme={chartTheme}
              axisBottom={{ tickSize: 5, tickPadding: 26, tickRotation: -45, legendPosition: "middle", legendOffset: 65 }}
              axisLeft={{ tickSize: 5, tickPadding: 8, tickRotation: 0, legendPosition: "middle", legendOffset: -60 }}
              labelSkipWidth={12}
              labelSkipHeight={12}
              onClick={(node) => onSelectArticleIds(node.data.article_ids || [], t('trends.ioc.selectedTitle', { value: node.data.value }))}
              borderRadius={4}
              layers={["grid", "axes", "bars", "markers", "legends", "annotations", ...(onBlacklistIoc ? [blacklistLayer] : [])]}
              tooltip={({ value, indexValue }) => (
                <Box bgcolor="background.paper" p={1.5} border={1} borderColor="divider" borderRadius={1}>
                  <Typography variant="body2" color="text.primary" fontWeight="medium">{indexValue}</Typography>
                  <Typography variant="body2" color="text.secondary">{t('trends.ioc.occurrences', { count: value })}</Typography>
                  <Typography variant="caption" color="text.secondary">{t('trends.ioc.clickToView')}</Typography>
                </Box>
              )}
              role="application"
              aria-label={`Top ${selectedIocType} IOCs bar chart`}
            />
          ) : (
            <Box display="flex" justifyContent="center" alignItems="center" height="100%">
              <Typography variant="body1" color="text.secondary">
                {t('trends.ioc.noData')}
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
