import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import DeleteIcon from '@mui/icons-material/Delete';

import ResizableTextField from './ResizableTextField';

export default function StaticContextEditor({ ctx, onUpdate, onDelete }) {
  const { t } = useTranslation('llmTemplates');

  return (
    <Paper sx={{ mb: 1.5, p: 1.5 }}>
      <Box display="flex" flexDirection="column" gap={1.5}>
        <Box display="flex" gap={2} alignItems="flex-start">
          <ResizableTextField
            label={t('staticContexts.nameLabel')}
            value={ctx.name}
            onChange={e => onUpdate({ ...ctx, name: e.target.value })}
            size="small"
            sx={{ flex: 1 }}
            helperText=""
          />
          <ResizableTextField
            label={t('staticContexts.descriptionLabel')}
            value={ctx.description}
            onChange={e => onUpdate({ ...ctx, description: e.target.value })}
            size="small"
            sx={{ flex: 2 }}
            helperText=""
          />
          <Box display="flex" alignItems="center">
            <IconButton color="error" onClick={onDelete} aria-label={t('staticContexts.deleteContextAria')}>
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
        <ResizableTextField
          label={t('staticContexts.contentLabel')}
          value={ctx.content}
          onChange={e => onUpdate({ ...ctx, content: e.target.value })}
          multiline
          minRows={2}
          fullWidth
        />
      </Box>
    </Paper>
  );
}
