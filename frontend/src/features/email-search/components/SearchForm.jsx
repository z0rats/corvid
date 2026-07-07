import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import SearchIcon from '@mui/icons-material/Search';

export default function SearchForm({ onSearch, disabled }) {
  const { t } = useTranslation('emailSearch');
  const [username, setUsername] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) return;
    onSearch(trimmed);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2, display: 'flex', gap: 2 }}>
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
        {t('form.searchButton')}
      </Button>
    </Box>
  );
}
