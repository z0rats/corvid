import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import CheckIcon from '@mui/icons-material/Check';
import SearchIcon from '@mui/icons-material/Search';

import { EMAIL_SOURCES, isFullEmail } from '../utils/sources';

export default function SearchForm({ onSearch, disabled, initialUsername, source, onSourceChange }) {
  const { t } = useTranslation('emailSearch');
  // `initialUsername` comes from usePrefillFromQuery, which yields `null` (not `undefined`) when
  // absent — a default parameter wouldn't catch that, so this normalizes it explicitly.
  const [username, setUsername] = useState(initialUsername || '');

  const needsEmail = source === 'user_scanner';
  const trimmed = username.trim();
  const invalid = needsEmail && trimmed !== '' && !isFullEmail(trimmed);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!trimmed || invalid) return;
    onSearch(trimmed, source);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
        {t('form.sourceLabel')}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
        {EMAIL_SOURCES.map((key) => {
          const selected = source === key;
          return (
            <Tooltip key={key} title={t(`form.source.${key}.hint`)} describeChild>
              <Chip
                label={t(`form.source.${key}.label`)}
                icon={selected ? <CheckIcon /> : undefined}
                color={selected ? 'primary' : 'default'}
                variant={selected ? 'filled' : 'outlined'}
                onClick={() => onSourceChange(key)}
                disabled={disabled}
              />
            </Tooltip>
          );
        })}
      </Stack>
      <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
          fullWidth
          size="small"
          label={t(needsEmail ? 'form.emailLabel' : 'form.usernameLabel')}
          placeholder={t(needsEmail ? 'form.emailPlaceholder' : 'form.usernamePlaceholder')}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={disabled}
          error={invalid}
          helperText={invalid ? t('form.emailRequired') : undefined}
        />
        <Button
          type="submit"
          variant="contained"
          startIcon={<SearchIcon />}
          disabled={disabled || !trimmed || invalid}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('form.searchButton')}
        </Button>
      </Box>
    </Box>
  );
}
