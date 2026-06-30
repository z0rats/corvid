import React from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Snackbar from '@mui/material/Snackbar';
import ResultTable from './components/ui/ResultTable';
import SearchBar from '../../../../core/components/ui/SearchBar';
import WelcomeScreen from './components/ui/WelcomeScreen';
import { useSingleLookup } from './hooks/ui/useSingleLookup';

export default function SingleLookup() {
  const { t } = useTranslation('iocTools');
  const {
    searchValue,
    currentIocType,
    snackbarOpen,
    shouldShowTable,
    inputRef,
    handleSubmitSearch,
    handleKeyPress,
    handleCloseError,
  } = useSingleLookup();

  return (
    <>
      <SearchBar
        ref={inputRef}
        placeholder={t('singleLookup.searchBar.placeholder')}
        buttonLabel={t('singleLookup.searchBar.buttonLabel')}
        onKeyDown={handleKeyPress}
        onSearchClick={handleSubmitSearch}
        size="medium"
        fullWidth
      />

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseError}
          severity="error"
          variant="filled"
          elevation={6}
        >
          <AlertTitle>
            <b>{t('singleLookup.invalidInputAlert.title')}</b>
          </AlertTitle>
          {t('singleLookup.invalidInputAlert.message')}
        </Alert>
      </Snackbar>
      <Box sx={{ mb: 2 }} />
      {shouldShowTable && searchValue && currentIocType ? (
        <ResultTable
          ioc={searchValue}
          iocType={currentIocType}
        />
      ) : (
        <WelcomeScreen />
      )}
    </>
  );
}
