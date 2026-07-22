import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import SearchForm from './SearchForm';
import ResultsList from './ResultsList';
import { useRedditSearch } from '../hooks/useRedditSearch';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export default function NewSearch() {
  const { t } = useTranslation('redditSearch');
  const [kind, setKind] = useState('posts');
  const { username, posts, comments, search, goNext, goPrev } = useRedditSearch();
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

  useEffect(() => {
    // Hand-off from a command-palette pivot (e.g. "john_doe reddit") — see crossFeatureNav.js.
    if (!prefillValue) return;
    search(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  const active = kind === 'posts' ? posts : comments;
  const hasSearched = Boolean(username);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 1 }}>{t('page.title')}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('page.description')}
      </Typography>

      <SearchForm onSearch={search} disabled={posts.loading || comments.loading} initialUsername={prefillValue} />

      {hasSearched && (
        <Box>
          <Tabs value={kind} onChange={(_e, value) => setKind(value)} sx={{ mb: 2 }}>
            <Tab value="posts" label={t('results.postsTab', { count: posts.items.length })} />
            <Tab value="comments" label={t('results.commentsTab', { count: comments.items.length })} />
          </Tabs>

          {active.loading && <LinearProgress sx={{ mb: 2 }} />}
          {active.error && (
            <Typography color="error" sx={{ mb: 2 }}>{active.error}</Typography>
          )}

          <ResultsList items={active.items} sources={active.sources} />

          {active.items.length > 0 && (
            <Stack direction="row" spacing={1} justifyContent="center" alignItems="center" sx={{ mt: 2 }}>
              <IconButton
                size="small"
                onClick={() => goPrev(kind)}
                disabled={active.page <= 1 || active.loading}
                aria-label={t('results.prevPage')}
              >
                <ArrowBackIcon fontSize="small" />
              </IconButton>
              <Typography variant="body2">{t('results.page', { page: active.page })}</Typography>
              <IconButton
                size="small"
                onClick={() => goNext(kind)}
                disabled={!active.hasMore || active.loading}
                aria-label={t('results.nextPage')}
              >
                <ArrowForwardIcon fontSize="small" />
              </IconButton>
            </Stack>
          )}
        </Box>
      )}
    </Box>
  );
}
