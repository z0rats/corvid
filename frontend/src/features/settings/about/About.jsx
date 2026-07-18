import React, { useState } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import { appVersionAtom } from '../../../core/state/atoms';
import { getAccessToken, clearAccessToken } from '../../../core/utils/accessToken';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

export default function About() {
  const { t } = useTranslation('settings');
  const theme = useTheme();
  const appVersion = useAtomValue(appVersionAtom);
  const { notification, showSuccess, hideNotification } = useNotification();
  const [tokenVisible, setTokenVisible] = useState(false);
  const [forgetDialogOpen, setForgetDialogOpen] = useState(false);
  const token = getAccessToken();

  const handleCopy = async () => {
    await navigator.clipboard.writeText(token);
    showSuccess(t('about.accessToken.copied'));
  };

  const handleForget = () => {
    clearAccessToken();
    window.location.reload();
  };

  return (
    <Box>
      {/* Main About Card */}
      <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('about.title')} {appVersion && `v${appVersion}`}
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          {t('about.body')}
        </Typography>
        <Typography variant="body1">
          {t('about.nameNote')}
        </Typography>
      </Card>

      {/* Access Token Card */}
      {token && (
        <Card elevation={0} sx={{ p: 2, mb: 1, borderRadius: 1, border: 'none', backgroundColor: theme.palette.background.paper }}>
          <Typography variant="h6" gutterBottom>
            {t('about.accessToken.title')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('about.accessToken.description')}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, maxWidth: 480 }}>
            <TextField
              type={tokenVisible ? 'text' : 'password'}
              value={token}
              size="small"
              fullWidth
              slotProps={{ input: { readOnly: true } }}
            />
            <Tooltip title={t(tokenVisible ? 'about.accessToken.hide' : 'about.accessToken.show')}>
              <IconButton onClick={() => setTokenVisible((v) => !v)}>
                {tokenVisible ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title={t('about.accessToken.copy')}>
              <IconButton onClick={handleCopy}>
                <ContentCopyIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Button
            variant="outlined"
            color="error"
            size="small"
            sx={{ mt: 2 }}
            onClick={() => setForgetDialogOpen(true)}
          >
            {t('about.accessToken.forgetButton')}
          </Button>
        </Card>
      )}

      <Dialog open={forgetDialogOpen} onClose={() => setForgetDialogOpen(false)}>
        <DialogTitle>{t('about.accessToken.forgetButton')}</DialogTitle>
        <DialogContent>
          <DialogContentText>{t('about.accessToken.forgetConfirm')}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setForgetDialogOpen(false)} variant="outlined">Cancel</Button>
          <Button onClick={handleForget} variant="contained" color="error" autoFocus>
            {t('about.accessToken.forgetButton')}
          </Button>
        </DialogActions>
      </Dialog>

      <NotificationSnackbar notification={notification} onClose={hideNotification} />
    </Box>
  );
}
