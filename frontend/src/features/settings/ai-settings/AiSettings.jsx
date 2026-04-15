import { useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { aiSettingsState } from '../../../core/state/atoms';
import { useAiSettings } from '../hooks/api/useAiSettings';
import { useNotification } from '../../../core/hooks/ui/useNotification';
import NotificationSnackbar from '../components/ui/NotificationSnackbar';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import FormControl from '@mui/material/FormControl';
import ListSubheader from '@mui/material/ListSubheader';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

const MODULE_CONFIGS = [
  { field: 'newsfeed_analysis_model', label: 'Newsfeed Article Analysis', description: 'Model used when analyzing individual news articles' },
  { field: 'newsfeed_report_model', label: 'Newsfeed Report Generation', description: 'Model used for ranking and analyzing top articles in reports' },
  { field: 'email_analyzer_model', label: 'Email Analyzer', description: 'Model used for AI-based email body analysis' },
  { field: 'llm_templates_model', label: 'LLM Templates (new template default)', description: 'Default model for newly created templates' },
];

function ModelSelector({ label, description, value, models, onChange, disabled, allowDefault = false }) {
  const grouped = useMemo(
    () => Object.groupBy(models, m => m.provider),
    [models]
  );

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        p: 2,
        borderRadius: 1,
        border: '1px solid',
        borderColor: 'divider',
        bgcolor: 'action.hover',
      }}
    >
      <Box>
        <Typography variant="h6">{label}</Typography>
        <Typography variant="body2" color="text.secondary">{description}</Typography>
      </Box>
      <FormControl sx={{ minWidth: 250 }}>
        <Select
          value={value || ''}
          onChange={e => onChange(e.target.value || null)}
          disabled={disabled}
          size="small"
          displayEmpty
        >
          {allowDefault && <MenuItem value="">Use global default</MenuItem>}
          {Object.entries(grouped).flatMap(([provider, providerModels]) => [
            <ListSubheader key={provider}>{provider}</ListSubheader>,
            ...providerModels.map(m => (
              <MenuItem key={m.id} value={m.id}>{m.name}</MenuItem>
            )),
          ])}
        </Select>
      </FormControl>
    </Box>
  );
}

export default function AiSettings() {
  const aiSettings = useAtomValue(aiSettingsState);
  const { loading, availableModels, updateAiSettings } = useAiSettings();
  const { notification, showNotification, hideNotification } = useNotification();

  const handleUpdate = async (field, value) => {
    const result = await updateAiSettings({ [field]: value === null ? '' : value });
    showNotification(result.message, result.success ? 'success' : 'error');
  };

  return (
    <Box>
      <Card elevation={0} sx={{ border: 'none' }}>
        <CardContent>
          <Typography variant="h5" sx={{ mb: 2 }}>
            AI Settings
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Configure which LLM models are used as defaults across the application.
            Per-module overrides take priority over the global default.
          </Typography>

          <Typography variant="h6" sx={{ mb: 2 }}>
            Global Default
          </Typography>
          <ModelSelector
            label="Default Model"
            description="Fallback model used when no per-module override is set."
            value={aiSettings.default_model}
            models={availableModels}
            onChange={value => handleUpdate('default_model', value)}
            disabled={loading || availableModels.length === 0}
          />

          <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
            Per-Module Overrides
          </Typography>
          <Stack spacing={2}>
            {MODULE_CONFIGS.map(({ field, label, description }) => (
              <ModelSelector
                key={field}
                label={label}
                description={description}
                value={aiSettings[field]}
                models={availableModels}
                onChange={value => handleUpdate(field, value)}
                disabled={loading || availableModels.length === 0}
                allowDefault
              />
            ))}
          </Stack>
        </CardContent>
      </Card>

      <NotificationSnackbar
        notification={notification}
        onClose={hideNotification}
      />
    </Box>
  );
}
