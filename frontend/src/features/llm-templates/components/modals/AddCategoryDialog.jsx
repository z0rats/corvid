import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';

export default function AddCategoryDialog({ open, onClose, onConfirm }) {
  const { t } = useTranslation('llmTemplates');
  const [name, setName] = useState('');

  const handleConfirm = () => {
    const trimmed = name.trim();
    if (trimmed) {
      onConfirm(trimmed);
      setName('');
    }
  };

  const handleClose = () => {
    setName('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('addCategoryDialog.title')}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label={t('addCategoryDialog.nameLabel')}
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleConfirm()}
          sx={{ mt: 1 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t('addCategoryDialog.cancelButton')}</Button>
        <Button onClick={handleConfirm} variant="contained" disabled={!name.trim()}>
          {t('addCategoryDialog.createButton')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
