import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Autocomplete from '@mui/material/Autocomplete';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import CheckIcon from '@mui/icons-material/Check';
import SearchIcon from '@mui/icons-material/Search';

import { usernameSearchApi } from '../services/api/usernameSearchApi';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('UsernameSearchForm');

const DEFAULT_MODULES = ['maigret'];

const MODULE_KEYS = ['maigret', 'social_analyzer', 'threat_actor_usernames', 'hudson_rock'];
const MODULE_LABEL_KEYS = {
  maigret: 'form.sourceMaigret',
  social_analyzer: 'form.sourceSocialAnalyzer',
  threat_actor_usernames: 'form.sourceThreatActorUsernames',
  hudson_rock: 'form.sourceHudsonRock',
};
// hudson_rock isn't a scan engine like the other three (no SSE progress panel of its own) - it's a
// separate, always-quick supplementary lookup, so it's set off from the engine chips visually.
const SUPPLEMENTARY_MODULE_KEYS = new Set(['hudson_rock']);

export default function SearchForm({ onSearch, disabled, initialUsername }) {
  const { t } = useTranslation('usernameSearch');
  // `initialUsername` comes from usePrefillFromQuery, which yields `null` (not `undefined`) when
  // absent — a default parameter wouldn't catch that, so this normalizes it explicitly.
  const [username, setUsername] = useState(initialUsername || '');
  const [modules, setModules] = useState(DEFAULT_MODULES);
  const [tags, setTags] = useState([]);
  const [availableTags, setAvailableTags] = useState([]);

  useEffect(() => {
    let ignore = false;
    usernameSearchApi.getTags()
      .then((data) => { if (!ignore) setAvailableTags(data); })
      .catch((err) => logger.error('Failed to load tags:', err));
    return () => { ignore = true; };
  }, []);

  const toggleModule = (moduleKey) => {
    setModules((prev) => (
      prev.includes(moduleKey) ? prev.filter((m) => m !== moduleKey) : [...prev, moduleKey]
    ));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed || modules.length === 0) return;
    onSearch(trimmed, { modules, tags: modules.includes('maigret') ? tags : undefined });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
        {t('form.modulesLabel')}
      </Typography>
      <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
        {MODULE_KEYS.map((moduleKey, index) => {
          const selected = modules.includes(moduleKey);
          const isSupplementary = SUPPLEMENTARY_MODULE_KEYS.has(moduleKey);
          const previousWasEngine = index > 0 && !SUPPLEMENTARY_MODULE_KEYS.has(MODULE_KEYS[index - 1]);
          const chip = (
            <Chip
              key={moduleKey}
              label={t(MODULE_LABEL_KEYS[moduleKey])}
              icon={selected ? <CheckIcon /> : undefined}
              color={selected ? 'primary' : 'default'}
              variant={selected ? 'filled' : 'outlined'}
              onClick={() => toggleModule(moduleKey)}
              disabled={disabled}
            />
          );
          return (
            <Box key={moduleKey} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {isSupplementary && previousWasEngine && (
                <Divider orientation="vertical" flexItem sx={{ height: 24, alignSelf: 'center' }} />
              )}
              {isSupplementary ? (
                <Tooltip title={t('form.sourceHudsonRockTooltip')}>{chip}</Tooltip>
              ) : chip}
            </Box>
          );
        })}
      </Stack>
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
          disabled={disabled || !username.trim() || modules.length === 0}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('form.searchButton')}
        </Button>
      </Box>
      {modules.includes('maigret') && (
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
