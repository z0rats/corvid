import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';

import AppSnackbar from '../../../core/components/ui/AppSnackbar';
import OperationControls from './components/ui/OperationControls';
import InputForm from './components/ui/InputForm';
import ResultsTable from './components/ui/ResultsTable';
import WelcomeScreen from './components/ui/WelcomeScreen';
import HowToUseSection from './components/ui/HowToUseSection';
import { useDefanger } from './hooks/ui/useDefanger';

export default function IocDefanger() {
  const {
    inputText,
    results,
    operation,
    showOnlyChanged,
    snackbar,
    closeSnackbar,
    handleProcess,
    handleCopy,
    handleCopyAllResults,
    handleDownloadCsv,
    handleSetOperation,
    handleClear,
    handleInputChange,
    handleToggleShowOnlyChanged,
    hasResults,
  } = useDefanger();

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Grid container spacing={3}>
          <Grid size={12}>
            <OperationControls
              operation={operation}
              onSetOperation={handleSetOperation}
            />
          </Grid>
          <Grid size={12}>
            <InputForm
              inputText={inputText}
              onInputChange={handleInputChange}
              operation={operation}
              onProcess={handleProcess}
              onClear={handleClear}
              onCopyAllResults={handleCopyAllResults}
              onDownloadCsv={handleDownloadCsv}
              hasResults={hasResults}
            />
          </Grid>
        </Grid>
      </Paper>

      {hasResults && (
        <Paper sx={{ p: 3 }}>
          <ResultsTable
            results={results}
            operation={operation}
            showOnlyChanged={showOnlyChanged}
            onToggleShowOnlyChanged={handleToggleShowOnlyChanged}
            onCopy={handleCopy}
          />
        </Paper>
      )}

      {!hasResults && (
        <Paper sx={{ p: 3 }}>
          <WelcomeScreen />
          <Divider sx={{ my: 3 }} />
          <HowToUseSection />
        </Paper>
      )}
      <AppSnackbar
        open={snackbar.open}
        message={snackbar.message}
        severity={snackbar.severity}
        onClose={closeSnackbar}
      />
    </Box>
  );
}
