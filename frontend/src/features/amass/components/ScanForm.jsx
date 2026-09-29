import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Link from '@mui/material/Link';
import SearchIcon from '@mui/icons-material/Search';

export default function ScanForm({ onScan, disabled, initialTarget }) {
  const { t } = useTranslation('amass');
  // `initialTarget` comes from usePrefillFromQuery via NewScan, which yields
  // `null` (not `undefined`) when absent - a default parameter wouldn't catch that.
  const [domain, setDomain] = useState(initialTarget || '');
  const [bruteForce, setBruteForce] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = domain.trim();
    if (!trimmed) return;

    onScan({ domain: trimmed, brute_force: bruteForce });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          size="small"
          label={t('form.targetLabel')}
          placeholder={t('form.targetPlaceholder')}
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          disabled={disabled}
        />
        <Button
          type="submit"
          variant="contained"
          startIcon={<SearchIcon />}
          disabled={disabled || !domain.trim()}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('form.scanButton')}
        </Button>
      </Box>

      <FormControlLabel
        sx={{ mt: 1 }}
        control={
          <Switch
            checked={bruteForce}
            onChange={(e) => setBruteForce(e.target.checked)}
            disabled={disabled}
          />
        }
        label={t('form.bruteForceLabel')}
      />

      <Link
        href="https://github.com/owasp-amass/amass"
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
