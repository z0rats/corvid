import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import DeleteIcon from '@mui/icons-material/Delete';

import ResizableTextField from './ResizableTextField';

export default function PayloadFieldEditor({ field, onUpdate, onDelete }) {
  const { t } = useTranslation('llmTemplates');

  return (
    <Paper sx={{ mb: 1.5, p: 1.5, position: 'relative' }}>
      <Box display="flex" gap={2} alignItems="flex-start">
        <ResizableTextField
          label={t('payloadFields.nameLabel')}
          value={field.name}
          onChange={e => onUpdate({ ...field, name: e.target.value })}
          size="small"
          sx={{ flex: 1 }}
          required
          error={field.required && !field.name.trim()}
          helperText={field.required && !field.name.trim() ? t('payloadFields.nameRequiredHelper') : ''}
        />
        <ResizableTextField
          label={t('payloadFields.descriptionLabel')}
          value={field.description}
          onChange={e => onUpdate({ ...field, description: e.target.value })}
          size="small"
          sx={{ flex: 2 }}
        />
        <Box display="flex" alignItems="center">
          <IconButton color="error" onClick={onDelete} aria-label={t('payloadFields.deleteFieldAria')}>
            <DeleteIcon />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
}
