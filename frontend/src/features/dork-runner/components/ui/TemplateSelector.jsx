import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

export default function TemplateSelector({ templates, selectedKeys, onToggle }) {
  const { t } = useTranslation('dorkRunner');

  if (!templates || templates.length === 0) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
        {t('form.templatesLabel')}
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {templates.map((template) => (
          <Tooltip key={template.key} title={template.pattern}>
            <FormControlLabel
              sx={{ mr: 1 }}
              control={
                <Checkbox
                  size="small"
                  checked={selectedKeys.includes(template.key)}
                  onChange={() => onToggle(template.key)}
                />
              }
              label={template.description}
            />
          </Tooltip>
        ))}
      </Box>
    </Box>
  );
}
