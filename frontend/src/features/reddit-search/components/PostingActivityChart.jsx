import React from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { modeValue } from '../../../core/utils/themeUtils';
import { buildHourlyActivity, buildMonthlyActivity } from '../utils/activityUtils';

function ActivityTooltip({ active, payload, label, formatLabel, formatCount }) {
  if (!active || !payload?.length) return null;
  return (
    <Box bgcolor="background.paper" p={1} border={1} borderColor="divider" borderRadius={1}>
      <Typography variant="body2" color="text.primary" fontWeight="medium">
        {formatLabel ? formatLabel(label) : label}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {formatCount(payload[0].value)}
      </Typography>
    </Box>
  );
}

export default function PostingActivityChart({ items }) {
  const { t } = useTranslation('redditSearch');
  const theme = useTheme();

  const hourly = React.useMemo(() => buildHourlyActivity(items), [items]);
  const monthly = React.useMemo(() => buildMonthlyActivity(items), [items]);
  const barColor = modeValue(theme, theme.palette.primary.light, theme.palette.primary.main);
  const formatCount = (count) => t('activity.postsCount', { count });

  if (!items || items.length === 0) return null;

  const monthTickInterval = monthly.length > 12 ? Math.ceil(monthly.length / 12) - 1 : 0;

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>{t('activity.sectionTitle')}</Typography>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.primary" sx={{ mb: 1 }}>
                {t('activity.byHourTitle')}
              </Typography>
              <Box sx={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourly} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
                    <XAxis
                      dataKey="hour"
                      tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={{ stroke: theme.palette.divider }}
                      interval={1}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={{ stroke: theme.palette.divider }}
                    />
                    <Tooltip
                      cursor={{ fill: theme.palette.action.hover }}
                      content={(props) => (
                        <ActivityTooltip
                          {...props}
                          formatLabel={(hour) => t('activity.hourLabel', { hour })}
                          formatCount={formatCount}
                        />
                      )}
                    />
                    <Bar dataKey="count" fill={barColor} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.primary" sx={{ mb: 1 }}>
                {t('activity.byMonthTitle')}
              </Typography>
              <Box sx={{ height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthly} margin={{ top: 8, right: 8, bottom: 30, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
                    <XAxis
                      dataKey="month"
                      angle={-45}
                      textAnchor="end"
                      tickMargin={10}
                      interval={monthTickInterval}
                      tick={{ fontSize: 10, fill: theme.palette.text.secondary }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={{ stroke: theme.palette.divider }}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={{ stroke: theme.palette.divider }}
                    />
                    <Tooltip
                      cursor={{ fill: theme.palette.action.hover }}
                      content={(props) => <ActivityTooltip {...props} formatCount={formatCount} />}
                    />
                    <Bar dataKey="count" fill={barColor} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
