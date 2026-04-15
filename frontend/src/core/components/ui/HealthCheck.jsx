import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { alpha } from '@mui/material/styles';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useHealthCheck } from '../../hooks/api/useHealthCheck';

function HealthCheck({ children }) {
  const { status, handleRetry } = useHealthCheck();

  if (status === 'loading') {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <CircularProgress size={48} thickness={4} />
        <Typography variant="body1" color="text.secondary" sx={{ mt: 3 }}>
          Connecting to backend...
        </Typography>
      </Box>
    );
  }

  if (status === 'error') {
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
          sx={(theme) => ({
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
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
                ? alpha(theme.palette.error.main, 0.12)
                : alpha(theme.palette.error.main, 0.08),
              mb: 3,
            })}
          >
            <CloudOffIcon
              sx={(theme) => ({
                fontSize: 36,
                color: theme.palette.error.main,
              })}
            />
          </Box>

          <Typography variant="h5" sx={{ mb: 1, textAlign: 'center' }}>
            Connection Failed
          </Typography>

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 4, textAlign: 'center', lineHeight: 1.7 }}
          >
            Unable to reach the backend service. Please make sure the server is running and try again.
          </Typography>

          <Button
            variant="contained"
            color="primary"
            onClick={handleRetry}
            startIcon={<RefreshIcon />}
            fullWidth
          >
            Retry Connection
          </Button>
        </Box>
      </Box>
    );
  }

  return children;
}

export default HealthCheck;
