import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';

import WebContextEditor from './WebContextEditor';

export default function WebContextsEditor({ contexts, onAdd, onUpdate, onDelete }) {
  const { t } = useTranslation('llmTemplates');

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('webContexts.helperText')}
        </Typography>
        <Button startIcon={<AddIcon />} size="small" onClick={onAdd}>{t('webContexts.addWebsiteButton')}</Button>
      </Box>
      {contexts.length > 0 ? (
        contexts.map((c, i) => (
          <WebContextEditor
            key={c.id || i}
            ctx={c}
            onUpdate={updated => onUpdate(i, updated)}
            onDelete={() => onDelete(i)}
          />
        ))
      ) : (
        <Typography color="text.secondary">{t('webContexts.emptyState')}</Typography>
      )}
    </Box>
  );
}
