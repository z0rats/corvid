import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { alpha } from '@mui/material/styles';
import LockIcon from '@mui/icons-material/Lock';
import { getAccessToken, setAccessToken } from '../../utils/accessToken';

function AccessGate({ children }) {
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
        height: '100vh',
        bgcolor: 'background.default',
        p: 3,
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
          maxWidth: 420,
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
          Access Token Required
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 4, textAlign: 'center', lineHeight: 1.7 }}
        >
          This OSINT Toolkit instance requires an access token. Find it on the
          server at <code>data/.access_token</code>, or in the backend startup logs.
        </Typography>

        <TextField
          type="password"
          label="Access token"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          fullWidth
          autoFocus
          sx={{ mb: 3 }}
        />

        <Button type="submit" variant="contained" color="primary" fullWidth>
          Continue
        </Button>
      </Box>
    </Box>
  );
}

export default AccessGate;
