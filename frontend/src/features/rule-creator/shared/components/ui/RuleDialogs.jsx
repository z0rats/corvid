import React from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Snackbar from '@mui/material/Snackbar';

/**
 * The reset-confirmation dialog and generation-error alert every rule page's
 * use*RuleActions hook drives (useConfirmDialog/useErrorAlert state).
 */
export default function RuleDialogs({ confirmDialog, onConfirm, onCancel, errorAlert, onCloseError }) {
  const { t } = useTranslation('ruleCreator');

  return (
    <>
      <Dialog open={confirmDialog.open} onClose={onCancel}>
        <DialogTitle>{confirmDialog.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{confirmDialog.message}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCancel} size="small">{t('common.actions.cancel')}</Button>
          <Button onClick={onConfirm} color="error" variant="contained" size="small">
            {t('common.actions.confirm')}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={errorAlert.open}
        autoHideDuration={6000}
        onClose={onCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={onCloseError} severity="error" variant="filled" sx={{ width: '100%' }}>
          {errorAlert.message}
        </Alert>
      </Snackbar>
    </>
  );
}
