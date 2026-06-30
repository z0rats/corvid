import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';

export default function RenameCategoryDialog({ open, category, onClose, onConfirm }) {
  const { t } = useTranslation('llmTemplates');
  const [name, setName] = useState('');

  useEffect(() => {
    if (category) setName(category.name);
  }, [category]);

  const handleConfirm = () => {
    const trimmed = name.trim();
    if (trimmed) {
      onConfirm(category.id, trimmed);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('renameCategoryDialog.title')}</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          label={t('renameCategoryDialog.nameLabel')}
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleConfirm()}
          sx={{ mt: 1 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('renameCategoryDialog.cancelButton')}</Button>
        <Button onClick={handleConfirm} variant="contained" disabled={!name.trim()}>
          {t('renameCategoryDialog.saveButton')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
