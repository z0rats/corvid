import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';

export default function FalsePositives({ falsePositives, handleFalsePositivesChange }) {
  const { t } = useTranslation('ruleCreator');
  const [currentFalsePositive, setCurrentFalsePositive] = useState('');

  const handleAddFalsePositive = () => {
    const trimmedFP = currentFalsePositive.trim();
    if (trimmedFP && !falsePositives.some((fp) => fp.value === trimmedFP)) {
      handleFalsePositivesChange((prev) => [...prev, { id: crypto.randomUUID(), value: trimmedFP }]);
      setCurrentFalsePositive('');
    }
  };

  const handleDeleteFalsePositive = (idToDelete) => {
    handleFalsePositivesChange((prev) => prev.filter((fp) => fp.id !== idToDelete));
  };

  return (
    <>
      {/* Info text */}
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.falsePositives.helpText')}
      </Typography>

      <Grid container spacing={1} alignItems="center">
        <Grid size={12}>
          <TextField
            fullWidth
            label={t('sigma.falsePositives.addLabel')}
            value={currentFalsePositive}
            onChange={(e) => setCurrentFalsePositive(e.target.value)}
            size="small"
            variant="outlined"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddFalsePositive();
              }
            }}
            placeholder={t('sigma.falsePositives.addPlaceholder')}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title={t('sigma.falsePositives.addLabel')}>
                      <IconButton
                        onClick={handleAddFalsePositive}
                        disabled={!currentFalsePositive.trim()}
                        size="small"
                        aria-label={t('sigma.falsePositives.addAria')}
                      >
                        <AddCircleIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                ),
              },
            }}
          />
        </Grid>
      </Grid>

      {/* Display False Positives */}
      {falsePositives.length > 0 && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 2 }}>
          {falsePositives.map((fp) => (
            <Chip
              key={fp.id}
              label={fp.value}
              onDelete={() => handleDeleteFalsePositive(fp.id)}
              size="small"
              variant="outlined"
            />
          ))}
        </Stack>
      )}
    </>
  );
}
