import React, { useId, useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { generalSettingsState } from '../../../core/state/atoms';
import { useGeneralSettings } from '../hooks/api/useGeneralSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import { FONT_OPTIONS } from '../constants/settingsConstants';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

/**
 * General settings component
 */
export default function General() {
  const generalSettings = useAtomValue(generalSettingsState);
  const theme = useTheme();
  
  const fontSelectId = useId();
  const { loading, updateFont, updateDarkmode } = useGeneralSettings();
  const { notification, showNotification, hideNotification } = useNotification();

  const cardStyle = useMemo(() => ({
    p: 1,
    pl: 2,
    m: 1,
    boxShadow: '0',
    backgroundColor: theme.palette.background.card,
    borderRadius: 1,
  }), [theme.palette.background.card]);

  const handleFontChange = async (event) => {
    const result = await updateFont(event.target.value);
    if (result.success) {
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  const handleDarkmodeChange = async () => {
    const result = await updateDarkmode(!generalSettings.darkmode);
    if (result.success) {
      showNotification(result.message);
    } else {
      showNotification(result.message, 'error');
    }
  };

  return (
    <Box>
      <Card sx={cardStyle}>
        <Typography variant="h4" component="h2" gutterBottom>
          General
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Application wide settings can be configured here.
        </Typography>
      </Card>

      <Card sx={cardStyle}>
        <Typography variant="h5" component="h3" gutterBottom>
          Visual
        </Typography>
        
        <Stack spacing={3}>
          <FormControlLabel
            control={
              <Switch
                checked={generalSettings.darkmode}
                onChange={handleDarkmodeChange}
                disabled={loading}
              />
            }
            label="Dark mode"
          />

          <Box>
            <Typography variant="body1" gutterBottom>
              Custom font
            </Typography>
            <FormControl sx={{ minWidth: 200 }}>
              <Select
                id={fontSelectId}
                value={generalSettings.font}
                onChange={handleFontChange}
                disabled={loading}
                size="small"
                displayEmpty
                slotProps={{ htmlInput: { 'aria-label': 'Font selection' } }}
              >
                {FONT_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
              <FormHelperText>
                Change the application wide font for OSINT Toolkit
              </FormHelperText>
            </FormControl>
          </Box>
        </Stack>
      </Card>

      <NotificationSnackbar 
        notification={notification} 
        onClose={hideNotification} 
      />
    </Box>
  );
}
