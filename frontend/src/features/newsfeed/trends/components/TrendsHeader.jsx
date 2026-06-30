import React from "react";
import { useTranslation } from "react-i18next";
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import RefreshIcon from "@mui/icons-material/Refresh";

import { TIME_RANGE_OPTIONS } from "../../constants/newsfeedConstants";

export default function TrendsHeader({ timeRange, onTimeRangeChange, onRefresh }) {
  const { t } = useTranslation('newsfeed');

  return (
    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
      <Typography variant="h5" color="text.primary">
        {t('trends.header.title')}
      </Typography>

      <Box display="flex" alignItems="center" gap={2}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>{t('trends.header.timeRange')}</InputLabel>
          <Select value={timeRange} label={t('trends.header.timeRange')} onChange={onTimeRangeChange}>
            {TIME_RANGE_OPTIONS.filter((r) => r.value !== "alltime").map((range) => (
              <MenuItem key={range.value} value={range.value}>
                {range.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Tooltip title={t('trends.header.refreshData')}>
          <IconButton onClick={onRefresh} size="large" aria-label={t('trends.header.refresh')}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}
