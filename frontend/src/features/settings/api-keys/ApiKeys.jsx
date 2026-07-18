import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useApiKeys } from '../hooks/api/useApiKeys';
import { useApiKeyFilters } from '../hooks/ui/useFilters';
import { calculateCompletionPercentage, getConfiguredCount } from '../utils/settingsUtils';

import ApiKeysHeader from './components/ui/ApiKeysHeader';
import ApiKeysFilters from './components/ui/ApiKeysFilters';
import ServiceCard from './components/ui/ServiceCard';
import QuotaPanel from './components/ui/QuotaPanel';

import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import ErrorIcon from '@mui/icons-material/Error';

export default function ApiKeys() {
  const { t } = useTranslation('settings');
  const [servicesConfig, setServicesConfig] = useState({});
  const [headerExpanded, setHeaderExpanded] = useState(false);
  const [error, setError] = useState(null);

  const { loading, getServicesConfig } = useApiKeys();
  const {
    searchFilter,
    showOnlyConfigured,
    filteredServices,
    updateSearchFilter,
    toggleShowOnlyConfigured,
  } = useApiKeyFilters(servicesConfig);

  useEffect(() => {
    let ignore = false;

    const loadServicesConfig = async () => {
      const result = await getServicesConfig();
      if (ignore) return;
      if (result.success) {
        setServicesConfig(result.data);
        setError(null);
      } else {
        setError(result.message);
      }
    };

    loadServicesConfig();
    return () => { ignore = true; };
  }, [getServicesConfig]);

  if (loading && Object.keys(servicesConfig).length === 0) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Stack spacing={2} alignItems="center">
          <CircularProgress size={48} />
          <Typography variant="h6" color="text.secondary">
            {t('apiKeys.loadingServices')}
          </Typography>
        </Stack>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
        <Alert severity="error" icon={<ErrorIcon />}>
          <AlertTitle>{t('apiKeys.errorTitle')}</AlertTitle>
          {error}
        </Alert>
      </Box>
    );
  }

  const configuredCount = getConfiguredCount(servicesConfig);
  const completionPercentage = calculateCompletionPercentage(servicesConfig);
  const totalServices = Object.keys(servicesConfig).length;

  return (
    <Box>
      <ApiKeysHeader
        configuredCount={configuredCount}
        totalServices={totalServices}
        completionPercentage={completionPercentage}
        expanded={headerExpanded}
        onToggle={() => setHeaderExpanded(!headerExpanded)}
      />

      <QuotaPanel />

      <ApiKeysFilters
        searchFilter={searchFilter}
        showOnlyConfigured={showOnlyConfigured}
        onSearchChange={updateSearchFilter}
        onToggleConfigured={toggleShowOnlyConfigured}
      />

      <Grid container spacing={3}>
        {filteredServices.map(([serviceKey, service]) => (
          <Grid size={{ xs: 12, lg: 6 }} key={serviceKey}>
            <ServiceCard serviceKey={serviceKey} service={service} />
          </Grid>
        ))}
      </Grid>

      {filteredServices.length === 0 && (
        <Paper elevation={0} sx={{ p: 4, textAlign: 'center', mt: '30px', borderRadius: 1 }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            {t('apiKeys.noServicesFound')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('apiKeys.noServicesFoundHelper')}
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
