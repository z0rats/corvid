import React, { useState } from 'react';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Grow from '@mui/material/Grow';

import DomainSearchForm from './components/forms/DomainSearchForm';
import WelcomeScreen from './components/ui/WelcomeScreen';
import ResultTable from './components/ui/ResultTable';

export default function DomainMonitoring() {
  const [searchDomain, setSearchDomain] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = (domain) => {
    setSearchDomain(domain);
    setShowResults(true);
    setError(null);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setShowResults(false);
  };

  return (
    <>
      <DomainSearchForm onSearch={handleSearch} onError={handleError} />
      
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
                <b>Error</b>
              </AlertTitle>
              {error}
            </Alert>
          </Grow>
        )}

        {showResults ? (
          <ResultTable key={searchDomain} domain={searchDomain} />
        ) : (
          <WelcomeScreen />
        )}
      </Box>
    </>
  );
}
