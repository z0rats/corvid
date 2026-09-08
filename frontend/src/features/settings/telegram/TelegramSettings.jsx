import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import SendIcon from '@mui/icons-material/SendOutlined';
import SaveIcon from '@mui/icons-material/SaveOutlined';

import { useTelegramSettings } from '../hooks/api/useTelegramSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

export default function TelegramSettings() {
  const { t } = useTranslation('settings');
  const theme = useTheme();
  const { settings, loading, saving, testing, updateSettings, sendTestMessage } =
    useTelegramSettings();
  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const [botToken, setBotToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [webBaseUrl, setWebBaseUrl] = useState('');

  useEffect(() => {
    if (settings) {
      setBotToken(settings.bot_token);
      setChatId(settings.chat_id);
      setWebBaseUrl(settings.web_base_url);
    }
  }, [settings]);

  const cardStyle = {
    p: 2,
    mb: 1,
    borderRadius: 1,
    border: 'none',
    backgroundColor: theme.palette.background.paper,
  };

  const handleSaveConnection = async () => {
    const result = await updateSettings(
      { bot_token: botToken, chat_id: chatId, web_base_url: webBaseUrl },
      t('telegram.connection.saveError')
    );
    if (result.success) {
      showSuccess(t('telegram.connection.saveSuccess'));
    } else {
      showError(result.message);
    }
  };

  const handleSendTest = async () => {
    const result = await sendTestMessage(t('telegram.connection.testError'));
    if (result.success) {
      showSuccess(result.message);
    } else {
      showError(result.message);
    }
  };

  const handleToggle = async (field) => {
    const result = await updateSettings(
      { [field]: !settings[field] },
      t('telegram.preferences.saveError')
    );
    if (!result.success) {
      showError(result.message);
    }
  };

  if (loading || !settings) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  const connectionUnchanged =
    botToken === settings.bot_token &&
    chatId === settings.chat_id &&
    webBaseUrl === settings.web_base_url;
  const canSendTest = Boolean(settings.bot_token.trim() && settings.chat_id.trim());

  return (
    <Box>
      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('telegram.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('telegram.description')}
        </Typography>
      </Card>

      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h6" gutterBottom>
          {t('telegram.connection.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('telegram.connection.description')}
        </Typography>

        <Stack spacing={2} sx={{ maxWidth: 480 }}>
          <TextField
            label={t('telegram.connection.botTokenLabel')}
            helperText={t('telegram.connection.botTokenHelper')}
            type="password"
            size="small"
            value={botToken}
            onChange={(e) => setBotToken(e.target.value)}
            autoComplete="off"
          />
          <TextField
            label={t('telegram.connection.chatIdLabel')}
            helperText={t('telegram.connection.chatIdHelper')}
            size="small"
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
          />
          <TextField
            label={t('telegram.connection.webBaseUrlLabel')}
            helperText={t('telegram.connection.webBaseUrlHelper')}
            size="small"
            value={webBaseUrl}
            onChange={(e) => setWebBaseUrl(e.target.value)}
            placeholder="https://corvid.example.com"
          />
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveConnection}
              disabled={saving || connectionUnchanged}
            >
              {t('telegram.connection.saveButton')}
            </Button>
            <Button
              variant="outlined"
              startIcon={<SendIcon />}
              onClick={handleSendTest}
              disabled={testing || !canSendTest}
            >
              {t('telegram.connection.testButton')}
            </Button>
          </Stack>
        </Stack>
      </Card>

      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h6" gutterBottom>
          {t('telegram.preferences.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('telegram.preferences.description')}
        </Typography>

        <Stack spacing={1}>
          <FormControlLabel
            control={
              <Switch
                checked={settings.enabled}
                onChange={() => handleToggle('enabled')}
                disabled={saving}
              />
            }
            label={t('telegram.preferences.enabled')}
          />
          <FormControlLabel
            control={
              <Switch
                checked={settings.notify_scan_events}
                onChange={() => handleToggle('notify_scan_events')}
                disabled={saving || !settings.enabled}
              />
            }
            label={t('telegram.preferences.notifyScanEvents')}
          />
          <FormControlLabel
            control={
              <Switch
                checked={settings.notify_job_failures}
                onChange={() => handleToggle('notify_job_failures')}
                disabled={saving || !settings.enabled}
              />
            }
            label={t('telegram.preferences.notifyJobFailures')}
          />
          <FormControlLabel
            control={
              <Switch
                checked={settings.notify_newsfeed_matches}
                onChange={() => handleToggle('notify_newsfeed_matches')}
                disabled={saving || !settings.enabled}
              />
            }
            label={t('telegram.preferences.notifyNewsfeedMatches')}
          />
        </Stack>
      </Card>

      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h6" gutterBottom>
          {t('telegram.commands.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('telegram.commands.description')}
        </Typography>

        <FormControlLabel
          control={
            <Switch
              checked={settings.bot_commands_enabled}
              onChange={() => handleToggle('bot_commands_enabled')}
              disabled={saving || !settings.enabled}
            />
          }
          label={t('telegram.commands.enabled')}
        />
      </Card>

      <NotificationSnackbar notification={notification} onClose={hideNotification} />
    </Box>
  );
}
