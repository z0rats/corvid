import React from 'react';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveLine } from '@nivo/line';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import { useTheme } from '@mui/material/styles';
import SecurityIcon from '@mui/icons-material/Security';
import WarningIcon from '@mui/icons-material/Warning';
import DescriptionIcon from '@mui/icons-material/Description';
import DonutLargeIcon from '@mui/icons-material/DonutLarge';
import TimelineIcon from '@mui/icons-material/Timeline';

export default function MandiantSummary({
  categoryStats,
  pieData,
  lineChartData,
  riskScore,
  indicatorCount,
  reportCount,
  chartTheme,
  currentTheme,
}) {
  const theme = useTheme();

  const summaryPaperSx = {
    p: 2,
    backgroundColor: (t) => t.palette.mode === 'dark' ? t.palette.background.default : t.palette.grey[100],
    height: '100%',
  };

  const emptyStateSx = {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: (t) => t.palette.mode === 'dark' ? t.palette.background.default : t.palette.grey[100],
    borderRadius: 1,
    p: 2,
  };

  return (
    <Card sx={{ p: 2, mb: 2, borderRadius: 1, boxShadow: 0 }}>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <DonutLargeIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="h4">Threat Categories</Typography>
          </Box>
          <Box sx={{ height: 300 }}>
            {Object.keys(categoryStats).length > 0 ? (
              <ResponsivePie
                data={pieData}
                margin={{ top: 40, right: 80, bottom: 80, left: 80 }}
                innerRadius={0.5}
                padAngle={5}
                cornerRadius={3}
                colors={{ scheme: 'red_yellow_blue' }}
                borderWidth={1}
                borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
                radialLabelsSkipAngle={10}
                radialLabelsTextColor={theme.palette.text.primary}
                radialLabelsLinkColor={{ from: 'color' }}
                sliceLabelsSkipAngle={10}
                sliceLabelsTextColor={theme.palette.background.paper}
                theme={chartTheme}
              />
            ) : (
              <Box sx={emptyStateSx}>
                <DonutLargeIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
                <Typography variant="body1" color="text.secondary" align="center">No threat categories available</Typography>
              </Box>
            )}
          </Box>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <TimelineIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="h4">Observations Timeline</Typography>
          </Box>
          <Box sx={{ height: 300 }}>
            {lineChartData.length > 0 && lineChartData[0].data.length > 0 ? (
              <ResponsiveLine
                data={lineChartData}
                margin={{ top: 50, right: 50, bottom: 50, left: 60 }}
                xScale={{ type: 'point' }}
                yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false, reverse: false }}
                curve="cardinal"
                axisBottom={{ tickSize: 5, tickPadding: 5, tickRotation: 45, legend: 'Month', legendPosition: 'middle', legendOffset: 40 }}
                axisLeft={{ tickSize: 5, tickPadding: 5, tickRotation: 0, legend: 'Indicators', legendPosition: 'middle', legendOffset: -50 }}
                colors={{ scheme: 'category10' }}
                pointSize={10}
                pointColor={{ theme: 'background' }}
                pointBorderWidth={2}
                pointBorderColor={{ from: 'serieColor' }}
                pointLabelYOffset={-12}
                useMesh={true}
                theme={chartTheme}
              />
            ) : (
              <Box sx={emptyStateSx}>
                <TimelineIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
                <Typography variant="body1" color="text.secondary" align="center">No timeline data available</Typography>
              </Box>
            )}
          </Box>
        </Grid>

        <Grid size={12}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Paper sx={summaryPaperSx}>
                <Box display="flex" alignItems="center">
                  <SecurityIcon fontSize="large" sx={{ mr: 1, color: riskScore < 20 ? 'success.main' : riskScore < 40 ? 'warning.main' : 'error.main' }} />
                  <Box>
                    <Typography variant="h6">Average Risk Score</Typography>
                    <Typography variant="h4" color={riskScore < 20 ? 'success.main' : riskScore < 40 ? 'warning.main' : 'error.main'}>
                      {riskScore !== null ? riskScore : 'N/A'}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Paper sx={summaryPaperSx}>
                <Box display="flex" alignItems="center">
                  <WarningIcon fontSize="large" sx={{ mr: 1, color: 'warning.main' }} />
                  <Box>
                    <Typography variant="h6">Indicators Found</Typography>
                    <Typography variant="h4">{indicatorCount}</Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Paper sx={summaryPaperSx}>
                <Box display="flex" alignItems="center">
                  <DescriptionIcon fontSize="large" sx={{ mr: 1, color: 'info.main' }} />
                  <Box>
                    <Typography variant="h6">Related Reports</Typography>
                    <Typography variant="h4">{reportCount}</Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Card>
  );
}
