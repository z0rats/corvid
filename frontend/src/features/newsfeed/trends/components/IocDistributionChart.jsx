import React from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { ResponsivePie } from "@nivo/pie";

import { useIocDistribution } from "../../hooks/api/useTrendsApi";
import { createChartTheme } from "../../utils/chartTheme";
import LoadingState from "../../../../core/components/ui/LoadingState";

export default function IocDistributionChart({ timeRange, refreshKey }) {
  const { t } = useTranslation('newsfeed');
  const theme = useTheme();
  const { data, loading } = useIocDistribution(timeRange, refreshKey);
  const chartTheme = createChartTheme(theme);

  if (loading) {
    return <LoadingState minHeight="350px" />;
  }

  return (
    <Card sx={{ minHeight: "450px", height: "100%" }}>
      <CardContent>
        <Typography variant="h6" color="text.primary" mb={2}>
          {t('trends.iocDistribution.title')}
        </Typography>
        <Box height="400px">
          {data.length > 0 ? (
            <ResponsivePie
              data={data}
              margin={{ top: 40, right: 80, bottom: 100, left: 80 }}
              innerRadius={0.5}
              padAngle={3}
              cornerRadius={5}
              activeOuterRadiusOffset={0}
              activeInnerRadiusOffset={0}
              arcLabelsRadiusOffset={0.5}
              arcLabelsTextColor={theme.palette.mode === "dark" ? theme.palette.common.white : theme.palette.common.black}
              colors={{ scheme: "paired" }}
              borderWidth={1}
              borderColor={{ from: "color", modifiers: [["darker", 0.2]] }}
              arcLinkLabelsSkipAngle={10}
              arcLinkLabelsTextColor={theme.palette.text.secondary}
              arcLinkLabelsThickness={1}
              arcLinkLabelsColor={{ from: "color" }}
              arcLabelsSkipAngle={10}
              defs={[
                { id: "dots", type: "patternDots", background: "inherit", color: "rgba(255, 255, 255, 0.3)", size: 4, padding: 1, stagger: true },
                { id: "lines", type: "patternLines", background: "inherit", color: "rgba(255, 255, 255, 0.3)", rotation: -45, lineWidth: 6, spacing: 10 },
              ]}
              legends={[
                {
                  anchor: "bottom",
                  direction: "row",
                  justify: false,
                  translateX: 0,
                  translateY: 56,
                  itemsSpacing: 0,
                  itemWidth: 100,
                  itemHeight: 18,
                  itemTextColor: theme.palette.text.secondary,
                  itemDirection: "left-to-right",
                  itemOpacity: 1,
                  symbolSize: 18,
                  symbolShape: "circle",
                },
              ]}
              tooltip={({ datum: { id, value, label } }) => (
                <Box bgcolor="background.paper" p={1.5} border={1} borderColor="divider" borderRadius={1}>
                  <Typography variant="body2" color="text.primary" fontWeight="medium">{label}</Typography>
                  <Typography variant="body2" color="text.secondary">{t('trends.iocDistribution.totalOccurrences', { count: value })}</Typography>
                </Box>
              )}
              role="application"
              aria-label="IOC type distribution pie chart"
              theme={chartTheme}
            />
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
