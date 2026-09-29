import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import SearchIcon from '@mui/icons-material/Search';
import { isPhoneNumberTarget } from '../../../core/utils/iocTypeDetection';

export default function SearchForm({ onSearch, disabled, initialPhoneNumber }) {
  const { t } = useTranslation('phoneSearch');
  // `initialPhoneNumber` comes from usePrefillFromQuery, which yields `null` (not `undefined`)
  // when absent - a default parameter wouldn't catch that, so this normalizes it explicitly.
  const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber || '');

  const trimmed = phoneNumber.trim();
  const isValid = isPhoneNumberTarget(trimmed);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid) return;
    onSearch(trimmed);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2, display: 'flex', gap: 2 }}>
      <TextField
        fullWidth
        size="small"
        label={t('form.phoneNumberLabel')}
        placeholder={t('form.phoneNumberPlaceholder')}
        helperText={t('form.phoneNumberHelp')}
        value={phoneNumber}
        onChange={(e) => setPhoneNumber(e.target.value)}
        disabled={disabled}
      />
      <Button
        type="submit"
        variant="contained"
        startIcon={<SearchIcon />}
        disabled={disabled || !isValid}
        sx={{ whiteSpace: 'nowrap' }}
      >
        {t('form.searchButton')}
      </Button>
    </Box>
  );
}
