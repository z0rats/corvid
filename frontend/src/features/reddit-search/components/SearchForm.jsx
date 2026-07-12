import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Link from '@mui/material/Link';
import SearchIcon from '@mui/icons-material/Search';
import TuneIcon from '@mui/icons-material/Tune';

export default function SearchForm({ onSearch, disabled }) {
  const { t } = useTranslation('redditSearch');
  const [username, setUsername] = useState('');
  const [subreddit, setSubreddit] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [includeNsfw, setIncludeNsfw] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) return;

    const filters = { include_nsfw: includeNsfw };
    if (subreddit.trim()) filters.subreddit = subreddit.trim();
    if (dateFrom) filters.date_from = Math.floor(new Date(dateFrom).getTime() / 1000);
    if (dateTo) filters.date_to = Math.floor(new Date(dateTo).getTime() / 1000);

    onSearch(trimmed, filters);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mb: 2 }}>
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
          variant="outlined"
          startIcon={<TuneIcon />}
          onClick={() => setShowFilters((prev) => !prev)}
          sx={{ whiteSpace: 'nowrap' }}
        >
          {t('form.filtersButton')}
        </Button>
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

      <Collapse in={showFilters}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
          <TextField
            size="small"
            label={t('filters.subredditLabel')}
            placeholder={t('filters.subredditPlaceholder')}
            value={subreddit}
            onChange={(e) => setSubreddit(e.target.value)}
            disabled={disabled}
          />
          <TextField
            size="small"
            type="date"
            label={t('filters.dateFromLabel')}
            slotProps={{ inputLabel: { shrink: true } }}
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            disabled={disabled}
          />
          <TextField
            size="small"
            type="date"
            label={t('filters.dateToLabel')}
            slotProps={{ inputLabel: { shrink: true } }}
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            disabled={disabled}
          />
          <FormControlLabel
            control={<Switch checked={includeNsfw} onChange={(e) => setIncludeNsfw(e.target.checked)} disabled={disabled} />}
            label={t('filters.includeNsfwLabel')}
          />
        </Box>
      </Collapse>

      <Link
        href="https://github.com/zuxu4n/Rosint"
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
