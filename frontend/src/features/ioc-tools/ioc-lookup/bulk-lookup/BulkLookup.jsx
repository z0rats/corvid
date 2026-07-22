import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { useServiceDefinitions } from '../shared/hooks/useServiceDefinitions';
import { useBulkLookupProcessor } from './hooks/useBulkLookupProcessor';
import { useBulkLookupSettings } from './hooks/api/useBulkLookupSettings';
import { usePrefillFromQuery } from '../../../../core/hooks/usePrefillFromQuery';
import BulkLookupForm from './components/ui/BulkLookupForm';
import BulkLookupResults from './components/ui/BulkLookupResults';
import BulkLookupSettings from './components/ui/BulkLookupSettings';

export default function BulkLookup() {
  const { t } = useTranslation('iocTools');
  const [iocsInput, setIocsInput] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [formError, setFormError] = useState('');
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  useEffect(() => {
    // Command palette's ⌘⇧B ("add focused value to Bulk Lookup") and any other cross-feature
    // hand-off land here as a plain value appended to the existing input, not a replace.
    if (!prefillValue) return;
    setIocsInput((prev) => (prev.trim() ? `${prev}\n${prefillValue}` : prefillValue));
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  const { serviceDefinitions, loading: serviceDefsLoading } = useServiceDefinitions();

  const {
    categorizedIocs,
    loading: processing,
    progress,
    processorError,
    setProcessorError,
    performLookup,
    orderedIocTypes,
  } = useBulkLookupProcessor();

  const {
    loadingSettings,
    serviceSettings,
    settingsError,
    hasEnabledServices,
    enabledServiceNames,
    refreshSettings,
  } = useBulkLookupSettings(serviceDefinitions, serviceDefsLoading);

  const handleInputChange = useCallback((value) => {
    setIocsInput(value);
    if (processorError) setProcessorError('');
    if (formError) setFormError('');
  }, [processorError, setProcessorError, formError]);

  const handleTabChange = useCallback((event, newValue) => {
    setActiveTab(newValue);
  }, []);

  const handleSubmit = useCallback(() => {
    if (formError) setFormError('');
    performLookup(iocsInput, enabledServiceNames);
  }, [formError, iocsInput, enabledServiceNames, performLookup]);

  const isSubmitDisabled = useMemo(() => {
    return processing || !iocsInput.trim() || !hasEnabledServices;
  }, [processing, iocsInput, hasEnabledServices]);

  if (loadingSettings) {
    return (
      <Box sx={{ mb: 2, p: 2 }}>
        <Typography variant="h5" gutterBottom>
          {t('bulkLookup.title')}
        </Typography>
        <Box display="flex" justifyContent="center" sx={{ my: 4 }}>
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ mb: 2 }}>
      <BulkLookupSettings
        services={serviceSettings}
        onSettingsChange={refreshSettings}
        serviceDefinitions={serviceDefinitions}
      />

      <BulkLookupForm
        iocsInput={iocsInput}
        onInputChange={handleInputChange}
        onSubmit={handleSubmit}
        isSubmitDisabled={isSubmitDisabled}
        processing={processing}
        hasEnabledServices={hasEnabledServices}
        onFormError={setFormError}
      />

      {(formError || settingsError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {formError || settingsError}
        </Alert>
      )}

      <BulkLookupResults
        categorizedIocs={categorizedIocs}
        orderedIocTypes={orderedIocTypes}
        activeTab={activeTab}
        onTabChange={handleTabChange}
        loading={processing}
        progress={progress}
        error={processorError}
      />
    </Box>
  );
}
