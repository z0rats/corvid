import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { alpha } from '@mui/material/styles';
import LockIcon from '@mui/icons-material/Lock';
import { getAccessToken, setAccessToken } from '../../utils/accessToken';

function AccessGate({ children }) {
  const { t } = useTranslation();
  const [value, setValue] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!value.trim()) return;
    setAccessToken(value.trim());
    // Full reload so every on-mount data fetch (useAppSettings, etc.) runs
    // again with the token now attached, instead of staying stuck on the
    // failed state from before the token was entered.
    window.location.reload();
  };

  if (getAccessToken()) {
    return children;
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        bgcolor: 'background.default',
        p: 3,
        overflowY: 'auto',
      }}
    >
      <Box
        component="form"
        onSubmit={handleSubmit}
        sx={(theme) => ({
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
          maxWidth: 460,
          p: 5,
          borderRadius: 3,
          bgcolor: 'background.paper',
          border: `1px solid`,
          borderColor: 'divider',
          boxShadow: theme.palette.mode === 'dark'
            ? `0 8px 32px ${alpha('#000', 0.4)}`
            : `0 8px 32px ${alpha('#000', 0.08)}`,
        })}
      >
        <Box
          sx={(theme) => ({
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 72,
            height: 72,
            borderRadius: '50%',
            bgcolor: theme.palette.mode === 'dark'
              ? alpha(theme.palette.primary.main, 0.12)
              : alpha(theme.palette.primary.main, 0.08),
            mb: 3,
          })}
        >
          <LockIcon
            sx={(theme) => ({
              fontSize: 36,
              color: theme.palette.primary.main,
            })}
          />
        </Box>

        <Typography variant="h5" sx={{ mb: 1, textAlign: 'center' }}>
          {t('accessGate.title')}
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 3, textAlign: 'center', lineHeight: 1.7 }}
        >
          {t('accessGate.description')}
        </Typography>

        <Box sx={{ width: '100%', mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            {t('accessGate.whereToFindTitle')}
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2.5, color: 'text.secondary' }}>
            <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
              {t('accessGate.whereToFindStep1')}
            </Typography>
            <Typography component="li" variant="body2" sx={{ mb: 0.5 }}>
              {t('accessGate.whereToFindStep2')}
            </Typography>
            <Typography component="li" variant="body2">
              {t('accessGate.whereToFindStep3')}
            </Typography>
          </Box>
        </Box>

        <TextField
          type="password"
          label={t('accessGate.tokenLabel')}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          fullWidth
          autoFocus
          sx={{ mb: 3 }}
        />

        <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mb: 3 }}>
          {t('accessGate.continueButton')}
        </Button>

        <Box
          sx={(theme) => ({
            width: '100%',
            p: 2,
            borderRadius: 2,
            bgcolor: theme.palette.mode === 'dark'
              ? alpha(theme.palette.warning.main, 0.08)
              : alpha(theme.palette.warning.main, 0.06),
            border: `1px solid ${alpha(theme.palette.warning.main, 0.2)}`,
          })}
        >
          <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}>
            {t('accessGate.lostTokenTitle')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.6, display: 'block' }}>
            {t('accessGate.lostTokenBody')}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}

export default AccessGate;
