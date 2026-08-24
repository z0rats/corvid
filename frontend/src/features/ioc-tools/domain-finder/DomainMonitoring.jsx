import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Grow from '@mui/material/Grow';

import DomainSearchForm from './components/forms/DomainSearchForm';
import WelcomeScreen from './components/ui/WelcomeScreen';
import ResultTable from './components/ui/ResultTable';
import WhoisPanel from './components/ui/WhoisPanel';
import CtSubdomainsPanel from './components/ui/CtSubdomainsPanel';
import HackertargetPanel from './components/ui/HackertargetPanel';
import RapidDnsPanel from './components/ui/RapidDnsPanel';
import WebCheckPanel from './components/ui/WebCheckPanel';
import DnsRecordsPanel from './components/ui/DnsRecordsPanel';
import DnsDumpsterPanel from './components/ui/DnsDumpsterPanel';
import WaybackPanel from './components/ui/WaybackPanel';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';
import { domainUtils } from './utils/domainUtils';

export default function DomainMonitoring() {
  const { t } = useTranslation('iocTools');
  const [searchDomain, setSearchDomain] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState(null);
  const handleSearch = (domain) => {
    const normalizedDomain = domainUtils.normalizeDomainInput(domain);
    if (!normalizedDomain) {
      setError(t('domainFinder.errors.invalidPattern'));
      setShowResults(false);
      return;
    }
    setSearchDomain(normalizedDomain);
    setShowResults(true);
    setError(null);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setShowResults(false);
  };

  usePrefillFromQuery(handleSearch);

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
            <WebCheckPanel key={`webcheck_${searchDomain}`} domain={searchDomain} />
            <DnsRecordsPanel key={`dns_${searchDomain}`} domain={searchDomain} />
            <DnsDumpsterPanel key={`dnsdumpster_${searchDomain}`} domain={searchDomain} />
            <CtSubdomainsPanel key={`ct_${searchDomain}`} domain={searchDomain} onScanSubdomain={handleSearch} />
            <HackertargetPanel key={`hackertarget_${searchDomain}`} domain={searchDomain} onScanSubdomain={handleSearch} />
            <RapidDnsPanel key={`rapiddns_${searchDomain}`} domain={searchDomain} onScanSubdomain={handleSearch} />
            <WaybackPanel key={`wayback_${searchDomain}`} domain={searchDomain} />
            <ResultTable key={searchDomain} domain={searchDomain} />
          </>
        ) : (
          <WelcomeScreen />
        )}
      </Box>
    </>
  );
}
