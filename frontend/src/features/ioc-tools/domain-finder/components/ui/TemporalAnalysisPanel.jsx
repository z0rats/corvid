import React, { useMemo } from "react";
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import { useTemporalAnalysis } from "../../hooks/api/useTemporalAnalysis";
import { domainUtils } from "../../utils/domainUtils";
import { modeValue } from "../../../../../core/utils/themeUtils";

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

const SOURCE_LABELS = {
  whois: 'WHOIS',
  ssl_certificate: 'SSL Certificate',
  wayback: 'Wayback Machine',
  schema_org: 'Schema.org'
};

function sourceCounts(events) {
  const counts = new Map();
  for (const event of events) {
    counts.set(event.source, (counts.get(event.source) || 0) + 1);
  }
  return Array.from(counts.entries());
}

export default function TemporalAnalysisPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const { data, loading, error, unsupported } = useTemporalAnalysis(domain);

  const events = useMemo(() => data?.events || [], [data]);
  const chartData = useMemo(
    () => events.map((event) => ({ ...event, x: new Date(event.date).getTime() })),
    [events]
  );
  const serverPoints = useMemo(() => chartData.filter((e) => e.category === 'server'), [chartData]);
  const pagePoints = useMemo(() => chartData.filter((e) => e.category === 'page'), [chartData]);
  const counts = useMemo(() => sourceCounts(events), [events]);

  if (unsupported) return null;

  const serverColor = modeValue(theme, theme.palette.info.light, theme.palette.info.main);
  const pageColor = modeValue(theme, theme.palette.primary.light, theme.palette.primary.main);

  const renderTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const point = payload[0].payload;
    return (
      <Box
        sx={{
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 1,
          p: 1
        }}
      >
        <Typography variant="caption" display="block" fontWeight="bold">
          {domainUtils.formatDate(point.date)}
        </Typography>
        <Typography variant="caption" display="block">
          {point.label}
        </Typography>
        <Typography variant="caption" display="block" color="text.secondary">
          {SOURCE_LABELS[point.source] || point.source}
        </Typography>
      </Box>
    );
  };

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.temporalAnalysis.title')}
        </Typography>

        {loading && (
          <>
            <LinearProgress />
            <br />
          </>
        )}

        {error && (
          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
            {t('domainFinder.temporalAnalysis.errorPrefix')} {error}
          </Alert>
        )}

        {!loading && !error && data && (
          events.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.temporalAnalysis.noEvents')}
            </Typography>
          ) : (
            <>
              {data.sources_failed.length > 0 && (
                <Alert severity="info" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
                  {t('domainFinder.temporalAnalysis.sourcesFailed', {
                    sources: data.sources_failed.map((s) => SOURCE_LABELS[s] || s).join(', ')
                  })}
                </Alert>
              )}

              <Box sx={{ height: 220, mb: 2 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                    <XAxis
                      type="number"
                      dataKey="x"
                      domain={['dataMin', 'dataMax']}
                      tickFormatter={(ts) => new Date(ts).getFullYear()}
                      tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={{ stroke: theme.palette.divider }}
                    />
                    <YAxis
                      type="category"
                      dataKey="category"
                      allowDuplicatedCategory={false}
                      width={70}
                      tickFormatter={(value) => t(`domainFinder.temporalAnalysis.categories.${value}`)}
                      tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                      axisLine={{ stroke: theme.palette.divider }}
                      tickLine={{ stroke: theme.palette.divider }}
                    />
                    <Tooltip content={renderTooltip} cursor={{ strokeDasharray: '3 3' }} />
                    <ReferenceLine
                      x={Date.now()}
                      stroke={theme.palette.error.main}
                      strokeDasharray="4 4"
                      label={{
                        value: t('domainFinder.temporalAnalysis.today'),
                        position: 'insideTopRight',
                        fill: theme.palette.error.main,
                        fontSize: 11
                      }}
                    />
                    <Scatter name="server" data={serverPoints} fill={serverColor} shape="diamond" />
                    <Scatter name="page" data={pagePoints} fill={pageColor} />
                  </ScatterChart>
                </ResponsiveContainer>
              </Box>

              <Stack direction="row" spacing={1} sx={{ mb: 1, gap: 1, flexWrap: 'wrap' }}>
                {counts.map(([source, count]) => (
                  <Chip
                    key={source}
                    label={`${SOURCE_LABELS[source] || source} ${count}`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Stack>

              <TableContainer sx={{ maxHeight: 320 }}>
                <Table size="small" stickyHeader>
                  <TableBody>
                    {events.map((event, index) => (
                      <TableRow key={`${event.source}_${event.date}_${index}`}>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>
                          {domainUtils.formatDate(event.date)}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={t(`domainFinder.temporalAnalysis.categories.${event.category}`)}
                            size="small"
                            color={event.category === 'server' ? 'info' : 'primary'}
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={SOURCE_LABELS[event.source] || event.source}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>{event.label}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )
        )}
      </CardContent>
    </Card>
  );
}
