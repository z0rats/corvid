import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import SearchIcon from '@mui/icons-material/Search';
import TuneIcon from '@mui/icons-material/Tune';

const MODES = ['search', 'url', 'nickname'];

export default function ScanForm({ onScan, disabled, initialTarget, initialMode }) {
  const { t } = useTranslation('gitRecon');
  // `initialTarget`/`initialMode` come from usePrefillFromQuery via NewSearch, which yields
  // `null` (not `undefined`) when absent — a default parameter wouldn't catch that.
  const [mode, setMode] = useState(initialMode || 'search');
  const [target, setTarget] = useState(initialTarget || '');
  const [includeForks, setIncludeForks] = useState(false);
  const [resolveGithubLogins, setResolveGithubLogins] = useState(true);
  const [ignoreNoreply, setIgnoreNoreply] = useState(true);
  const [showOptions, setShowOptions] = useState(false);

  const handleModeChange = (_e, value) => {
    if (value) setMode(value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = target.trim();
    if (!trimmed) return;

    onScan({
      mode,
      target: trimmed,
      include_forks: includeForks,
      resolve_github_logins: resolveGithubLogins,
      ignore_noreply: ignoreNoreply,
    });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <ToggleButtonGroup
        value={mode}
        exclusive
        onChange={handleModeChange}
        size="small"
        disabled={disabled}
        sx={{ mb: 1.5 }}
      >
        {MODES.map((m) => (
          <ToggleButton key={m} value={m}>{t(`form.modes.${m}`)}</ToggleButton>
        ))}
      </ToggleButtonGroup>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t(`form.modeDescriptions.${mode}`)}
      </Typography>

      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          size="small"
          label={t(`form.targetLabels.${mode}`)}
          placeholder={t(`form.targetPlaceholders.${mode}`)}
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          disabled={disabled}
        />
        {mode !== 'search' && (
          <Button
            variant="outlined"
            startIcon={<TuneIcon />}
            onClick={() => setShowOptions((prev) => !prev)}
            sx={{ whiteSpace: 'nowrap' }}
          >
            {t('form.optionsButton')}
          </Button>
        )}
        <Button
          type="submit"
          variant="contained"
          startIcon={<SearchIcon />}
          disabled={disabled || !target.trim()}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('form.scanButton')}
        </Button>
      </Box>

      {mode !== 'search' && (
        <Collapse in={showOptions}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            {mode === 'nickname' && (
              <FormControlLabel
                control={<Switch checked={includeForks} onChange={(e) => setIncludeForks(e.target.checked)} disabled={disabled} />}
                label={t('form.includeForksLabel')}
              />
            )}
            <FormControlLabel
              control={<Switch checked={resolveGithubLogins} onChange={(e) => setResolveGithubLogins(e.target.checked)} disabled={disabled} />}
              label={t('form.resolveGithubLoginsLabel')}
            />
          </Box>
        </Collapse>
      )}

      {mode === 'search' && (
        <FormControlLabel
          sx={{ mt: 1 }}
          control={<Switch checked={ignoreNoreply} onChange={(e) => setIgnoreNoreply(e.target.checked)} disabled={disabled} />}
          label={t('form.ignoreNoreplyLabel')}
        />
      )}

      <Link
        href="https://github.com/Soxoj/gitcolombo"
        target="_blank"
        rel="noopener noreferrer"
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block', mt: 1 }}
      >
        {t('page.poweredBy')}
      </Link>
    </Box>
  );
}
