import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import DownloadIcon from '@mui/icons-material/DownloadOutlined';
import RestoreIcon from '@mui/icons-material/SettingsBackupRestoreOutlined';

import { useBackup } from '../hooks/api/useBackup';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

const RESTORE_CONFIRMATION_PHRASE = 'RESTORE';

export default function BackupSettings() {
  const { t } = useTranslation('settings');
  const theme = useTheme();
  const { exporting, restoring, getStatus, exportBackup, restoreBackup } = useBackup();
  const { notification, showSuccess, showError, hideNotification } = useNotification();

  const [status, setStatus] = useState(null);
  const [includeAccessToken, setIncludeAccessToken] = useState(false);
  const [exportPassphrase, setExportPassphrase] = useState('');

  const [restoreFile, setRestoreFile] = useState(null);
  const [restorePassphrase, setRestorePassphrase] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  useEffect(() => {
    let cancelled = false;
    getStatus()
      .then((result) => {
        if (!cancelled) setStatus(result);
      })
      .catch(() => {
        if (!cancelled) setStatus({ supported: false, db_dialect: 'unknown' });
      });
    return () => {
      cancelled = true;
    };
  }, [getStatus]);

  const cardStyle = {
    p: 2,
    mb: 1,
    borderRadius: 1,
    border: 'none',
    backgroundColor: theme.palette.background.paper,
  };

  const unsupported = Boolean(status) && !status.supported;

  const handleExport = async () => {
    const result = await exportBackup(
      { includeAccessToken, passphrase: exportPassphrase || null },
      t('backup.export.error')
    );
    if (!result.success) {
      showError(result.message);
      return;
    }
    const url = window.URL.createObjectURL(result.blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = result.filename;
    link.click();
    window.URL.revokeObjectURL(url);
    showSuccess(t('backup.export.success'));
  };

  const handleRestoreClick = () => {
    if (restoreFile) {
      setConfirmText('');
      setDialogOpen(true);
    }
  };

  const handleConfirmRestore = async () => {
    const result = await restoreBackup(
      { file: restoreFile, passphrase: restorePassphrase || null },
      t('backup.restore.error')
    );
    setDialogOpen(false);
    if (!result.success) {
      showError(result.message);
      return;
    }
    showSuccess(
      result.access_token_restored ? t('backup.restore.successWithToken') : t('backup.restore.success')
    );
    setRestoreFile(null);
    setRestorePassphrase('');
  };

  return (
    <Box>
      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h4" component="h2" gutterBottom>
          {t('backup.title')}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('backup.description')}
        </Typography>
      </Card>

      {unsupported && (
        <Card elevation={0} sx={cardStyle}>
          <Alert severity="warning">
            {t('backup.unsupported', { dialect: status.db_dialect })}
          </Alert>
        </Card>
      )}

      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h6" gutterBottom>
          {t('backup.export.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('backup.export.description')}
        </Typography>

        <Stack spacing={2} sx={{ maxWidth: 480 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={includeAccessToken}
                onChange={(e) => setIncludeAccessToken(e.target.checked)}
                disabled={unsupported}
              />
            }
            label={t('backup.export.includeAccessToken')}
          />
          <TextField
            label={t('backup.export.passphraseLabel')}
            helperText={t('backup.export.passphraseHelper')}
            type="password"
            size="small"
            value={exportPassphrase}
            onChange={(e) => setExportPassphrase(e.target.value)}
            disabled={unsupported}
          />
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
            disabled={unsupported || exporting}
            sx={{ alignSelf: 'flex-start' }}
          >
            {t('backup.export.button')}
          </Button>
        </Stack>
      </Card>

      <Card elevation={0} sx={cardStyle}>
        <Typography variant="h6" gutterBottom>
          {t('backup.restore.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('backup.restore.description')}
        </Typography>

        <Stack spacing={2} sx={{ maxWidth: 480 }}>
          <Button variant="outlined" component="label" disabled={unsupported}>
            {restoreFile ? restoreFile.name : t('backup.restore.chooseFile')}
            <input
              type="file"
              hidden
              accept=".gz,.enc"
              onChange={(e) => setRestoreFile(e.target.files?.[0] || null)}
            />
          </Button>
          <TextField
            label={t('backup.restore.passphraseLabel')}
            type="password"
            size="small"
            value={restorePassphrase}
            onChange={(e) => setRestorePassphrase(e.target.value)}
            disabled={unsupported}
          />
          <Alert severity="warning">{t('backup.restore.warning')}</Alert>
          <Button
            variant="contained"
            color="error"
            startIcon={<RestoreIcon />}
            onClick={handleRestoreClick}
            disabled={unsupported || !restoreFile || restoring}
            sx={{ alignSelf: 'flex-start' }}
          >
            {t('backup.restore.button')}
          </Button>
        </Stack>
      </Card>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>{t('backup.restore.confirmTitle')}</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>{t('backup.restore.confirmBody')}</DialogContentText>
          <TextField
            fullWidth
            size="small"
            label={t('backup.restore.confirmFieldLabel', { phrase: RESTORE_CONFIRMATION_PHRASE })}
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            autoFocus
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} variant="outlined">
            {t('backup.restore.cancel')}
          </Button>
          <Button
            onClick={handleConfirmRestore}
            variant="contained"
            color="error"
            disabled={confirmText !== RESTORE_CONFIRMATION_PHRASE || restoring}
          >
            {t('backup.restore.button')}
          </Button>
        </DialogActions>
      </Dialog>

      <NotificationSnackbar notification={notification} onClose={hideNotification} />
    </Box>
  );
}
