import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import DeleteIcon from '@mui/icons-material/Delete';
import LanguageIcon from '@mui/icons-material/Language';

import ResizableTextField from './ResizableTextField';

export default function WebContextEditor({ ctx, onUpdate, onDelete }) {
  const { t } = useTranslation('llmTemplates');

  return (
    <Paper sx={{ mb: 1.5, p: 1.5 }}>
      <Box display="flex" flexDirection="column" gap={1.5}>
        <Box display="flex" gap={2} alignItems="flex-start">
          <ResizableTextField
            label={t('webContexts.nameLabel')}
            value={ctx.name}
            onChange={e => onUpdate({ ...ctx, name: e.target.value })}
            size="small"
            sx={{ flex: 1 }}
            required
            error={!ctx.name.trim()}
            helperText={!ctx.name.trim() ? t('webContexts.nameRequiredHelper') : ''}
          />
          <ResizableTextField
            label={t('webContexts.descriptionLabel')}
            value={ctx.description}
            onChange={e => onUpdate({ ...ctx, description: e.target.value })}
            size="small"
            sx={{ flex: 2 }}
            placeholder={t('webContexts.descriptionPlaceholder')}
            helperText=""
          />
          <Box display="flex" alignItems="center">
            <IconButton color="error" onClick={onDelete} aria-label={t('webContexts.deleteContextAria')}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
        <ResizableTextField
          label={t('webContexts.urlLabel')}
          value={ctx.url}
          onChange={e => onUpdate({ ...ctx, url: e.target.value })}
          fullWidth
          required
          error={!ctx.url.trim()}
          helperText={!ctx.url.trim() ? t('webContexts.urlRequiredHelper') : t('webContexts.urlHelper')}
          placeholder={t('webContexts.urlPlaceholder')}
          slotProps={{
            input: {
              startAdornment: <LanguageIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            },
          }}
        />
      </Box>
    </Paper>
  );
}
