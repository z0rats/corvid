import React, { useCallback } from "react";
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Skeleton from '@mui/material/Skeleton';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';

import { useNewsfeedSettings } from "../hooks/api/useSettingsApi";
import { useNotification } from "../../../core/hooks/ui/useNotification";
import { SETTINGS, RETENTION_OPTIONS, FETCH_INTERVAL_OPTIONS } from "../constants/newsfeedConstants";
import NotificationSnackbar from "../components/ui/NotificationSnackbar";
import { createLogger } from "../../../core/utils/logger";

const logger = createLogger("NewsfeedSettings");

const SettingHeader = ({ title, description }) => (
  <Box sx={{ mb: 2 }}>
    <Typography variant="h6" gutterBottom>
      {title}
    </Typography>
    <Typography variant="body2" color="text.secondary">
      {description}
    </Typography>
  </Box>
);

export default function Settings() {
  const {
    config,
    loading,
    saving,
    updateConfig,
  } = useNewsfeedSettings();

  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const handleError = useCallback((error) => {
    logger.error("Settings error:", error);
    showError(error.response?.data?.message || error.message || "An error occurred");
  }, [showError]);

  const handleBackgroundFetchToggle = useCallback(async (enabled) => {
    const result = await updateConfig({ background_fetch_enabled: enabled });
    if (result.success) {
      showSuccess("Settings updated successfully");
    } else {
      handleError(result.error);
    }
  }, [updateConfig, showSuccess, handleError]);

  const handleRetentionChange = useCallback(async (event) => {
    const result = await updateConfig({ retention_days: event.target.value });
    if (result.success) {
      showSuccess("Settings updated successfully");
    } else {
      handleError(result.error);
    }
  }, [updateConfig, showSuccess, handleError]);

  const handleFetchIntervalChange = useCallback(async (event) => {
    const result = await updateConfig({ fetch_interval_minutes: event.target.value });
    if (result.success) {
      showSuccess("Settings updated successfully");
    } else {
      handleError(result.error);
    }
  }, [updateConfig, showSuccess, handleError]);

  if (loading) {
    return (
      <Card sx={{ p: 3 }}>
        <Skeleton variant="rectangular" height={200} />
      </Card>
    );
  }

  return (
    <>
      <Card sx={{ p: 3 }}>
        <SettingHeader
          title="General Newsfeed Settings"
          description="Configure how your newsfeed behaves and manages content"
        />

        <Divider sx={{ my: 3 }} />

        <Box sx={{ mb: 4 }}>
          <Typography variant="subtitle1" gutterBottom>
            Content Retention
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Define how long articles should be kept in your feed before being
            automatically removed
          </Typography>

          <Box sx={{ maxWidth: SETTINGS.MAX_WIDTH }}>
            <FormControl fullWidth size="small" disabled={saving}>
              <InputLabel>Retention Period</InputLabel>
              <Select
                value={config.retention_days}
                label="Retention Period"
                onChange={handleRetentionChange}
              >
                {RETENTION_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        <Box>
          <Typography variant="subtitle1" gutterBottom>
            Background Fetch
          </Typography>

          <Box sx={{ maxWidth: SETTINGS.MAX_WIDTH }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                mb: 2,
              }}
            >
              <Typography variant="body2" color="text.secondary" sx={{ flex: 1, mr: 2 }}>
                Enable automatic fetching of new content at regular intervals
              </Typography>
              <Switch
                checked={config.background_fetch_enabled}
                onChange={(e) => handleBackgroundFetchToggle(e.target.checked)}
                disabled={saving}
                color="primary"
              />
            </Box>

            {config.background_fetch_enabled && (
              <FormControl fullWidth size="small" disabled={saving}>
                <InputLabel>Fetch Interval</InputLabel>
                <Select
                  value={config.fetch_interval_minutes}
                  label="Fetch Interval"
                  onChange={handleFetchIntervalChange}
                >
                  {FETCH_INTERVAL_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Box>
        </Box>
      </Card>

      <NotificationSnackbar
        open={notification.open}
        message={notification.message}
        severity={notification.severity}
        onClose={hideNotification}
      />

      {saving && (
        <Box
          sx={{
            position: "fixed",
            bottom: 16,
            right: 16,
            zIndex: 2000,
          }}
        >
          <CircularProgress size={24} />
        </Box>
      )}
    </>
  );
}
