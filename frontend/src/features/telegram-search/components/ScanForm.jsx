import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import SearchIcon from '@mui/icons-material/Search';

import { MAX_POSTS_CAP, MAX_POSTS_DEFAULT, estimateRequests } from '../utils/telegramSearchConfig';

export default function ScanForm({ onSubmit, disabled, initialTarget }) {
  const { t } = useTranslation('telegramSearch');
  // usePrefillFromQuery yields `null` (not `undefined`) when absent.
  const [target, setTarget] = useState(initialTarget || '');
  const [maxPosts, setMaxPosts] = useState(MAX_POSTS_DEFAULT);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = target.trim();
    if (!trimmed) return;
    onSubmit(trimmed, { maxPosts });
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }} component="form" onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <TextField
          fullWidth
          size="small"
          label={t('form.targetLabel')}
          placeholder={t('form.targetPlaceholder')}
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          disabled={disabled}
        />

        <Box>
          <Typography variant="body2" gutterBottom>
            {t('form.maxPostsLabel')}: {maxPosts}
          </Typography>
          <Slider
            value={maxPosts}
            onChange={(_, value) => setMaxPosts(value)}
            min={20}
            max={MAX_POSTS_CAP}
            step={20}
            disabled={disabled}
            valueLabelDisplay="auto"
            aria-label={t('form.maxPostsLabel')}
          />
          <Typography variant="caption" color="text.secondary">
            {t('form.maxPostsHelper', { count: estimateRequests(maxPosts) })}
          </Typography>
        </Box>

        <Box>
          <Button
            type="submit"
            variant="contained"
            startIcon={<SearchIcon />}
            disabled={disabled || !target.trim()}
          >
            {t('form.startButton')}
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}
