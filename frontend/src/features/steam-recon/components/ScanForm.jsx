import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import Paper from '@mui/material/Paper';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import SearchIcon from '@mui/icons-material/Search';

import { MAX_FRIENDS_CAP, MAX_FRIENDS_DEFAULT, estimateApiCalls } from '../utils/steamReconConfig';

export default function ScanForm({ onSubmit, disabled, initialTarget }) {
  const { t } = useTranslation('steamRecon');
  // `initialTarget` comes from usePrefillFromQuery, which yields `null` (not `undefined`) when
  // absent - a default parameter wouldn't catch that, so this normalizes it explicitly.
  const [target, setTarget] = useState(initialTarget || '');
  const [maxFriends, setMaxFriends] = useState(MAX_FRIENDS_DEFAULT);
  const [includeCsReport, setIncludeCsReport] = useState(true);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = target.trim();
    if (!trimmed) return;
    onSubmit(trimmed, { maxFriends, includeCsReport });
  };

  return (
    <Paper sx={{ p: 2, mb: 2 }} component="form" onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <TextField
          fullWidth
          size="small"
          label={t('scan.form.targetLabel')}
          placeholder={t('scan.form.targetPlaceholder')}
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          disabled={disabled}
        />

        <Box>
          <Typography variant="body2" gutterBottom>
            {t('scan.form.maxFriendsLabel')}: {maxFriends}
          </Typography>
          <Slider
            value={maxFriends}
            onChange={(_, value) => setMaxFriends(value)}
            min={1}
            max={MAX_FRIENDS_CAP}
            step={10}
            disabled={disabled}
            valueLabelDisplay="auto"
            aria-label={t('scan.form.maxFriendsLabel')}
          />
          <Typography variant="caption" color="text.secondary">
            {t('scan.form.maxFriendsHelper', { count: estimateApiCalls(maxFriends, includeCsReport) })}
          </Typography>
        </Box>

        <Box>
          <FormControlLabel
            control={
              <Checkbox
                checked={includeCsReport}
                onChange={(e) => setIncludeCsReport(e.target.checked)}
                disabled={disabled}
              />
            }
            label={t('scan.form.includeCsReportLabel')}
          />
          <Typography variant="caption" color="text.secondary" display="block">
            {t('scan.form.includeCsReportHelper')}
          </Typography>
        </Box>

        <Box>
          <Button
            type="submit"
            variant="contained"
            startIcon={<SearchIcon />}
            disabled={disabled || !target.trim()}
          >
            {t('scan.form.startButton')}
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}
