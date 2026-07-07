import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Autocomplete from '@mui/material/Autocomplete';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import SearchIcon from '@mui/icons-material/Search';

import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchForm');

export default function SearchForm({ onSearch, disabled }) {
  const { t } = useTranslation('usernameSearch');
  const [username, setUsername] = useState('');
  const [source, setSource] = useState('maigret');
  const [tags, setTags] = useState([]);
  const [availableTags, setAvailableTags] = useState([]);

  useEffect(() => {
    let ignore = false;
    usernameSearchApi.getTags()
      .then((data) => { if (!ignore) setAvailableTags(data); })
      .catch((err) => logger.error('Failed to load tags:', err));
    return () => { ignore = true; };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) return;
    onSearch(trimmed, { source, tags: source === 'maigret' ? tags : undefined });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <ToggleButtonGroup
        exclusive
        size="small"
        value={source}
        onChange={(_, value) => value && setSource(value)}
        disabled={disabled}
        sx={{ mb: 2 }}
      >
        <ToggleButton value="maigret">{t('form.sourceMaigret')}</ToggleButton>
        <ToggleButton value="social_analyzer">{t('form.sourceSocialAnalyzer')}</ToggleButton>
      </ToggleButtonGroup>
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
          {t('form.searchButton')}
        </Button>
      </Box>
      {source === 'maigret' && (
        <Autocomplete
          multiple
          size="small"
          options={availableTags}
          value={tags}
          onChange={(_, newValue) => setTags(newValue)}
          disabled={disabled}
          sx={{ mt: 2 }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('form.tagsLabel')}
              placeholder={t('form.tagsPlaceholder')}
              helperText={t('form.tagsHelp')}
            />
          )}
        />
      )}
    </Box>
  );
}
