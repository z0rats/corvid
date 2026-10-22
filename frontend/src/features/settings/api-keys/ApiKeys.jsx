import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router';
import { useApiKeys } from '../hooks/api/useApiKeys';
import { useApiKeyFilters } from '../hooks/ui/useFilters';
import { calculateCompletionPercentage, getConfiguredCount } from '../utils/settingsUtils';

import ApiKeysHeader from './components/ui/ApiKeysHeader';
import ApiKeysFilters from './components/ui/ApiKeysFilters';
import ServiceCard from './components/ui/ServiceCard';
import KeyTestPanel from './components/ui/KeyTestPanel';
import { useKeyTests } from '../hooks/api/useKeyTests';

import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import ErrorIcon from '@mui/icons-material/Error';

export default function ApiKeys() {
  const { t } = useTranslation('settings');
  const [servicesConfig, setServicesConfig] = useState({});
  const [headerExpanded, setHeaderExpanded] = useState(false);
  const [error, setError] = useState(null);
  const [configLoaded, setConfigLoaded] = useState(false);

  const [searchParams, setSearchParams] = useSearchParams();
  const focusKey = searchParams.get('service');
  const clearFocus = () => setSearchParams((prev) => {
    const next = new URLSearchParams(prev);
    next.delete('service');
    return next;
  }, { replace: true });

  const { getServicesConfig } = useApiKeys();
  const keyTests = useKeyTests();
  const {
    searchFilter,
    showOnlyConfigured,
    filteredServices,
    updateSearchFilter,
    toggleShowOnlyConfigured,
  } = useApiKeyFilters(servicesConfig, focusKey);

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
      setConfigLoaded(true);
    };

    loadServicesConfig();
    return () => { ignore = true; };
  }, [getServicesConfig]);

  // Gate on the first load finishing, not on `loading`: that starts false, so the page would
  // mount once before the spinner and again after it.
  if (!configLoaded) {
    return (
      <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Stack spacing={2} sx={{
          alignItems: "center"
        }}>
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

      <KeyTestPanel
        onTestAll={keyTests.testAll}
        testingAll={keyTests.testingAll}
        error={keyTests.error}
      />

      {focusKey && servicesConfig[focusKey] ? (
        <Alert
          severity="info"
          sx={{ mb: 3 }}
          action={<Button color="inherit" size="small" onClick={clearFocus}>{t('apiKeys.showAll')}</Button>}
        >
          {t('apiKeys.focusedOn', { name: servicesConfig[focusKey].name })}
        </Alert>
      ) : (
        <ApiKeysFilters
          searchFilter={searchFilter}
          showOnlyConfigured={showOnlyConfigured}
          onSearchChange={updateSearchFilter}
          onToggleConfigured={toggleShowOnlyConfigured}
        />
      )}

      <Grid container spacing={3}>
        {filteredServices.map(([serviceKey, service]) => (
          <Grid size={{ xs: 12, lg: 6 }} key={serviceKey}>
            <ServiceCard
              serviceKey={serviceKey}
              service={service}
              keyTest={keyTests.results[serviceKey]}
              keyTesting={keyTests.testing.has(serviceKey)}
              onTestKey={keyTests.testService}
            />
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
