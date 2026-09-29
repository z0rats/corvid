import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import SearchIcon from '@mui/icons-material/Search';

const SCAN_TYPES = ['followers', 'followees', 'posts'];

export default function ScanForm({ onScan, disabled, initialUsername, initialScanType }) {
  const { t } = useTranslation('instagramSearch');
  // `initialUsername`/`initialScanType` come from usePrefillFromQuery, which yields `null`
  // (not `undefined`) when absent - a default parameter wouldn't catch that.
  const [username, setUsername] = useState(initialUsername || '');
  const [scanType, setScanType] = useState(initialScanType || 'posts');

  const handleScanTypeChange = (_e, value) => {
    if (value) setScanType(value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) return;
    onScan({ username: trimmed, scanType });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <ToggleButtonGroup
        value={scanType}
        exclusive
        onChange={handleScanTypeChange}
        size="small"
        disabled={disabled}
        sx={{ mb: 1.5 }}
      >
        {SCAN_TYPES.map((type) => (
          <ToggleButton key={type} value={type}>{t(`scanForm.types.${type}`)}</ToggleButton>
        ))}
      </ToggleButtonGroup>

      {scanType !== 'posts' && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t('scanForm.sessionRequiredNote')}
        </Typography>
      )}

      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          size="small"
          label={t('form.usernameLabel')}
          placeholder={t('form.usernamePlaceholder')}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={disabled}
        />
        <Button
          type="submit"
          variant="contained"
          startIcon={<SearchIcon />}
          disabled={disabled || !username.trim()}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('scanForm.scanButton')}
        </Button>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        {t('scanForm.limitsNote')}
      </Typography>
    </Box>
  );
}
