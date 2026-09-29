import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Grow from '@mui/material/Grow';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';

import ResultsTable from './components/ui/ResultsTable';
import WelcomeScreen from './components/ui/WelcomeScreen';
import { useSanctionsSearch } from './hooks/ui/useSanctionsSearch';

export default function SanctionsSearch() {
  const { t } = useTranslation('sanctionsSearch');
  const {
    query,
    setQuery,
    schema,
    setSchema,
    schemas,
    result,
    loading,
    error,
    runSearch,
    minQueryLength,
  } = useSanctionsSearch();

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      runSearch();
    }
  };

  return (
    <>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              fullWidth
              size="small"
              label={t('form.queryLabel')}
              placeholder={t('form.queryPlaceholder')}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <Select
              size="small"
              displayEmpty
              value={schema}
              onChange={(e) => setSchema(e.target.value)}
              sx={{ minWidth: 220 }}
            >
              <MenuItem value="">{t('form.allSchemas')}</MenuItem>
              {schemas.map((schemaOption) => (
                <MenuItem key={schemaOption} value={schemaOption}>
                  {schemaOption}
                </MenuItem>
              ))}
            </Select>
          </Stack>

          <Box>
            <Button
              variant="contained"
              onClick={() => runSearch()}
              disabled={loading || query.trim().length < minQueryLength}
            >
              {loading ? <CircularProgress size={20} /> : t('form.searchButton')}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {error && (
        <Grow in={true}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        </Grow>
      )}

      {result ? <ResultsTable result={result} /> : <WelcomeScreen />}
    </>
  );
}
