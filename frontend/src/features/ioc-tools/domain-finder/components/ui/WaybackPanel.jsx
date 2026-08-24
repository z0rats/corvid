import React, { useMemo, useState } from "react";
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import { useWaybackLookup } from "../../hooks/api/useWaybackLookup";
import { domainUtils } from "../../utils/domainUtils";
import { modeValue } from "../../../../../core/utils/themeUtils";

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import ClearIcon from "@mui/icons-material/Clear";
import HistoryIcon from "@mui/icons-material/HistoryOutlined";
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import SearchIcon from "@mui/icons-material/Search";
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function formatCdxTimestamp(timestamp) {
  // CDX timestamps are always UTC, in "YYYYMMDDhhmmss" form
  const match = /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$/.exec(timestamp || '');
  if (!match) return timestamp;
  const [, year, month, day, hour, minute, second] = match;
  return domainUtils.formatDate(`${year}-${month}-${day}T${hour}:${minute}:${second}Z`);
}

function capturesPerYear(snapshots) {
  const counts = new Map();
  for (const snapshot of snapshots) {
    const year = (snapshot.timestamp || '').slice(0, 4);
    if (!year) continue;
    counts.set(year, (counts.get(year) || 0) + 1);
  }
  return Array.from(counts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([year, count]) => ({ year, count }));
}

export default function WaybackPanel({ domain }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const [pathInput, setPathInput] = useState('');
  const [appliedPath, setAppliedPath] = useState(null);
  const { data, loading, error, unsupported } = useWaybackLookup(domain, appliedPath);
  const chartData = useMemo(() => capturesPerYear(data?.snapshots || []), [data]);

  if (unsupported) return null;

  const handleApplyPath = () => {
    const trimmed = pathInput.trim();
    setAppliedPath(trimmed ? trimmed : null);
  };

  const handleClearPath = () => {
    setPathInput('');
    setAppliedPath(null);
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleApplyPath();
    }
  };

  const barColor = modeValue(theme, theme.palette.primary.light, theme.palette.primary.main);

  return (
    <Card sx={{ mb: 2, p: 1, borderRadius: 1, boxShadow: 0 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('domainFinder.wayback.title')}
        </Typography>

        <Stack direction="row" spacing={1} sx={{ mb: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            value={pathInput}
            onChange={(event) => setPathInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('domainFinder.wayback.pathPlaceholder')}
            sx={{ maxWidth: 320 }}
          />
          <IconButton
            size="small"
            onClick={handleApplyPath}
            title={t('domainFinder.wayback.applyPath')}
          >
            <SearchIcon fontSize="small" />
          </IconButton>
          {appliedPath && (
            <>
              <Chip label={appliedPath} size="small" variant="outlined" />
              <IconButton size="small" onClick={handleClearPath} title={t('domainFinder.wayback.clearPath')}>
                <ClearIcon fontSize="small" />
              </IconButton>
            </>
          )}
        </Stack>

        {loading && (
          <>
            <LinearProgress />
            <br />
          </>
        )}

        {error && (
          <Alert severity="warning" variant="outlined" sx={{ borderRadius: 1, mb: 2 }}>
            {t('domainFinder.wayback.errorPrefix')} {error}
          </Alert>
        )}

        {!loading && !error && data && (
          data.snapshots.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t('domainFinder.wayback.noSnapshots')}
            </Typography>
          ) : (
            <>
              <Stack direction="row" spacing={1} sx={{ mb: 1, gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <HistoryIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {t('domainFinder.wayback.captureRange', {
                    count: data.total_snapshots,
                    first: domainUtils.formatDate(data.first_capture),
                    last: domainUtils.formatDate(data.last_capture)
                  })}
                </Typography>
              </Stack>

              {chartData.length > 1 && (
                <Box sx={{ height: 160, mb: 2 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
                      <XAxis
                        dataKey="year"
                        tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                        axisLine={{ stroke: theme.palette.divider }}
                        tickLine={{ stroke: theme.palette.divider }}
                      />
                      <YAxis
                        allowDecimals={false}
                        width={30}
                        tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                        axisLine={{ stroke: theme.palette.divider }}
                        tickLine={{ stroke: theme.palette.divider }}
                      />
                      <Tooltip
                        cursor={{ fill: theme.palette.action.hover }}
                        contentStyle={{
                          background: theme.palette.background.paper,
                          border: `1px solid ${theme.palette.divider}`,
                          borderRadius: 4,
                          fontSize: 12
                        }}
                        labelFormatter={(year) => year}
                        formatter={(count) => [count, t('domainFinder.wayback.capturesLabel')]}
                      />
                      <Bar dataKey="count" fill={barColor} radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              )}

              <List dense sx={{ maxHeight: 320, overflowY: 'auto' }}>
                {data.snapshots
                  .slice()
                  .reverse()
                  .map((snapshot) => (
                    <ListItem
                      key={`${snapshot.timestamp}_${snapshot.original_url}`}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          size="small"
                          component="a"
                          href={snapshot.snapshot_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={t('domainFinder.wayback.openSnapshot')}
                        >
                          <OpenInNewIcon fontSize="small" />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={formatCdxTimestamp(snapshot.timestamp)}
                        secondary={snapshot.original_url}
                      />
                      {snapshot.status_code && (
                        <Chip label={snapshot.status_code} size="small" variant="outlined" sx={{ mr: 1 }} />
                      )}
                    </ListItem>
                  ))}
              </List>
            </>
          )
        )}
      </CardContent>
    </Card>
  );
}
