import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Grow from '@mui/material/Grow';

import DomainSearchForm from './components/forms/DomainSearchForm';
import WelcomeScreen from './components/ui/WelcomeScreen';
import ResultTable from './components/ui/ResultTable';
import WhoisPanel from './components/ui/WhoisPanel';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function DomainMonitoring() {
  const { t } = useTranslation('iocTools');
  const [searchDomain, setSearchDomain] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState(null);
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  const handleSearch = (domain) => {
    setSearchDomain(domain);
    setShowResults(true);
    setError(null);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setShowResults(false);
  };

  useEffect(() => {
    if (!prefillValue) return;
    handleSearch(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return (
    <>
      <DomainSearchForm onSearch={handleSearch} onError={handleError} initialValue={searchDomain} />
      
      <Box sx={{ mt: 2 }}>
        {error && (
          <Grow in={true}>
            <Alert
              severity="error"
              variant="filled"
              onClose={() => setError(null)}
              sx={{ borderRadius: 5, mb: 2 }}
            >
              <AlertTitle>
                <b>{t('domainFinder.errors.title')}</b>
              </AlertTitle>
              {error}
            </Alert>
          </Grow>
        )}

        {showResults ? (
          <>
            <WhoisPanel key={`whois_${searchDomain}`} domain={searchDomain} />
            <ResultTable key={searchDomain} domain={searchDomain} />
          </>
        ) : (
          <WelcomeScreen />
        )}
      </Box>
    </>
  );
}
