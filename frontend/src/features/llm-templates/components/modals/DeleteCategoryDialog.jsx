import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Typography from '@mui/material/Typography';

export default function DeleteCategoryDialog({ open, category, templateCount, onClose, onConfirm }) {
  const { t } = useTranslation('llmTemplates');
  const [action, setAction] = useState('move_to_default');

  const handleConfirm = () => {
    onConfirm(category?.id, action);
    setAction('move_to_default');
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('deleteCategoryDialog.title')}</DialogTitle>
      <DialogContent>
        <Typography sx={{ mb: 2 }}>
          {t('deleteCategoryDialog.confirmMessagePrefix')} <strong>{category?.name}</strong>?
          {templateCount > 0 && t('deleteCategoryDialog.containsTemplates', { count: templateCount })}
        </Typography>
        {templateCount > 0 && (
          <RadioGroup value={action} onChange={e => setAction(e.target.value)}>
            <FormControlLabel
              value="move_to_default"
              control={<Radio />}
              label={t('deleteCategoryDialog.moveToDefault')}
            />
            <FormControlLabel
              value="delete_templates"
              control={<Radio />}
              label={t('deleteCategoryDialog.deleteTemplatesInGroup')}
            />
          </RadioGroup>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('deleteCategoryDialog.cancelButton')}</Button>
        <Button onClick={handleConfirm} color="error" variant="contained">
          {t('deleteCategoryDialog.deleteButton')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
