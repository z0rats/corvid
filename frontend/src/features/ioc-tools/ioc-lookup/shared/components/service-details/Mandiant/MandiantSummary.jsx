import React from 'react';
import { useTranslation } from 'react-i18next';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import { useTheme } from '@mui/material/styles';
import SecurityIcon from '@mui/icons-material/Security';
import WarningIcon from '@mui/icons-material/Warning';
import DescriptionIcon from '@mui/icons-material/Description';
import DonutLargeIcon from '@mui/icons-material/DonutLarge';
import TimelineIcon from '@mui/icons-material/Timeline';
import { getCategoricalColor } from '../../../../../../../core/utils/chartColors';

export default function MandiantSummary({
  categoryStats,
  pieData,
  lineChartData,
  riskScore,
  indicatorCount,
  reportCount,
}) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const theme = useTheme();
  const tooltipStyle = {
    background: theme.palette.background.paper,
    color: theme.palette.text.primary,
    fontSize: 12,
    border: `1px solid ${theme.palette.divider}`,
    borderRadius: theme.shape.borderRadius,
  };

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
            <Typography variant="h6" component="h4">{t('providers.mandiant.threatCategories')}</Typography>
          </Box>
          <Box sx={{ height: 300 }}>
            {Object.keys(categoryStats).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="label"
                    innerRadius="50%"
                    outerRadius="80%"
                    paddingAngle={2}
                    cornerRadius={3}
                    stroke={theme.palette.background.paper}
                    strokeWidth={1}
                    isAnimationActive={false}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={entry.id} fill={getCategoricalColor(theme, index)} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={{ color: theme.palette.text.secondary, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={emptyStateSx}>
                <DonutLargeIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
                <Typography variant="body1" color="text.secondary" align="center">{t('providers.mandiant.noThreatCategories')}</Typography>
              </Box>
            )}
          </Box>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Box display="flex" alignItems="center" mb={1}>
            <TimelineIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="h4">{t('providers.mandiant.observationsTimeline')}</Typography>
          </Box>
          <Box sx={{ height: 300 }}>
            {lineChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineChartData} margin={{ top: 20, right: 30, bottom: 30, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis
                    dataKey="date"
                    label={{ value: t('providers.mandiant.month'), position: 'insideBottom', offset: -10, fill: theme.palette.text.primary }}
                    tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                    axisLine={{ stroke: theme.palette.divider }}
                    tickLine={{ stroke: theme.palette.divider }}
                  />
                  <YAxis
                    allowDecimals={false}
                    label={{ value: t('providers.mandiant.indicatorsAxisLabel'), angle: -90, position: 'insideLeft', fill: theme.palette.text.primary }}
                    tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                    axisLine={{ stroke: theme.palette.divider }}
                    tickLine={{ stroke: theme.palette.divider }}
                  />
                  <Tooltip contentStyle={tooltipStyle} labelFormatter={(date) => date} />
                  <Line
                    type="monotone"
                    dataKey="count"
                    name={t('providers.mandiant.observationsTimeline')}
                    stroke={getCategoricalColor(theme, 0)}
                    strokeWidth={2}
                    dot={{ r: 4, fill: theme.palette.background.paper, stroke: getCategoricalColor(theme, 0), strokeWidth: 2 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={emptyStateSx}>
                <TimelineIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
                <Typography variant="body1" color="text.secondary" align="center">{t('providers.mandiant.noTimelineData')}</Typography>
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
                    <Typography variant="h6">{t('providers.mandiant.averageRiskScore')}</Typography>
                    <Typography variant="h4" color={riskScore < 20 ? 'success.main' : riskScore < 40 ? 'warning.main' : 'error.main'}>
                      {riskScore !== null ? riskScore : notAvailable}
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
                    <Typography variant="h6">{t('providers.mandiant.indicatorsFound')}</Typography>
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
                    <Typography variant="h6">{t('providers.mandiant.relatedReports')}</Typography>
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
