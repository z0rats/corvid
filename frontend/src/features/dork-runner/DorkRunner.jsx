import React from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Grow from '@mui/material/Grow';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import CircularProgress from '@mui/material/CircularProgress';

import EngineWarningBanner from './components/ui/EngineWarningBanner';
import ResultsTable from './components/ui/ResultsTable';
import TemplateSelector from './components/ui/TemplateSelector';
import WelcomeScreen from './components/ui/WelcomeScreen';
import { useDorkRunner } from './hooks/ui/useDorkRunner';

const TARGET_TYPES = ['domain', 'username', 'email'];
const ENGINES = ['duckduckgo', 'google', 'bing'];

export default function DorkRunner() {
  const { t } = useTranslation('dorkRunner');
  const {
    target,
    setTarget,
    targetType,
    setTargetType,
    engine,
    setEngine,
    templates,
    selectedTemplateKeys,
    toggleTemplate,
    result,
    loading,
    error,
    runDorks,
  } = useDorkRunner();

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      runDorks();
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
              label={t('form.targetLabel')}
              placeholder={t('form.targetPlaceholder')}
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <Select
              size="small"
              value={engine}
              onChange={(e) => setEngine(e.target.value)}
              sx={{ minWidth: 160 }}
            >
              {ENGINES.map((engineKey) => (
                <MenuItem key={engineKey} value={engineKey}>
                  {t(`engines.${engineKey}`)}
                </MenuItem>
              ))}
            </Select>
          </Stack>

          <ToggleButtonGroup
            size="small"
            exclusive
            value={targetType}
            onChange={(_, value) => value && setTargetType(value)}
          >
            {TARGET_TYPES.map((type) => (
              <ToggleButton key={type} value={type}>
                {t(`targetTypes.${type}`)}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>

          <TemplateSelector
            templates={templates}
            selectedKeys={selectedTemplateKeys}
            onToggle={toggleTemplate}
          />

          {engine !== 'duckduckgo' && <EngineWarningBanner />}

          <Box>
            <Button
              variant="contained"
              onClick={() => runDorks()}
              disabled={loading || !target.trim() || selectedTemplateKeys.length === 0}
            >
              {loading ? <CircularProgress size={20} /> : t('form.runButton')}
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
