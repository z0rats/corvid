import React, { useState, useCallback, useMemo } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { useServiceDefinitions } from '../shared/hooks/useServiceDefinitions';
import { useBulkLookupProcessor } from './hooks/useBulkLookupProcessor';
import { useBulkLookupSettings } from './hooks/api/useBulkLookupSettings';
import BulkLookupForm from './components/ui/BulkLookupForm';
import BulkLookupResults from './components/ui/BulkLookupResults';
import BulkLookupSettings from './components/ui/BulkLookupSettings';

export default function BulkLookup() {
  const [iocsInput, setIocsInput] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [formError, setFormError] = useState('');

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
          Bulk IOC Lookup
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
