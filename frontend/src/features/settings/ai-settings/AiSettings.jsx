import { useMemo } from 'react';
import { useAtomValue } from 'jotai';
import { useTranslation } from 'react-i18next';
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

const MODULE_CONFIG_FIELDS = [
  'newsfeed_analysis_model',
  'newsfeed_report_model',
  'email_analyzer_model',
  'llm_templates_model',
];

function ModelSelector({ label, description, value, models, onChange, disabled, allowDefault = false }) {
  const { t } = useTranslation('settings');
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
          {allowDefault && <MenuItem value="">{t('aiSettings.useGlobalDefault')}</MenuItem>}
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
  const { t } = useTranslation('settings');
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
            {t('aiSettings.title')}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            {t('aiSettings.description')}
          </Typography>

          <Typography variant="h6" sx={{ mb: 2 }}>
            {t('aiSettings.globalDefaultTitle')}
          </Typography>
          <ModelSelector
            label={t('aiSettings.defaultModelLabel')}
            description={t('aiSettings.defaultModelDescription')}
            value={aiSettings.default_model}
            models={availableModels}
            onChange={value => handleUpdate('default_model', value)}
            disabled={loading || availableModels.length === 0}
          />

          <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
            {t('aiSettings.perModuleTitle')}
          </Typography>
          <Stack spacing={2}>
            {MODULE_CONFIG_FIELDS.map((field) => (
              <ModelSelector
                key={field}
                label={t(`aiSettings.modules.${field}.label`)}
                description={t(`aiSettings.modules.${field}.description`)}
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
