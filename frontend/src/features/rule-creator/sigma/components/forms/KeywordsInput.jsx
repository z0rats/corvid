import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';

export default function KeywordsInput({ keywords, onAddKeyword, onDeleteKeyword }) {
  const { t } = useTranslation('ruleCreator');
  const [keywordInput, setKeywordInput] = useState('');

  const handleAdd = () => {
    if (keywordInput.trim() === '') {
      alert(t('sigma.keywordsInput.requiredAlert'));
      return;
    }
    onAddKeyword(keywordInput.trim());
    setKeywordInput('');
  };

  return (
    <>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 11 }}>
          <TextField
            fullWidth
            label={t('sigma.keywordsInput.label')}
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            size="small"
            variant="outlined"
            placeholder={t('sigma.keywordsInput.placeholder')}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAdd();
              }
            }}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 1 }}>
          <Tooltip title={t('sigma.keywordsInput.addTooltip')}>
            <IconButton onClick={handleAdd} size="small" aria-label={t('sigma.keywordsInput.addAria')}>
              <AddCircleIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Grid>
      </Grid>
      <Box sx={{ mt: 1 }}>
        {keywords.map((keyword) => (
          <Chip
            key={keyword.id}
            label={keyword.value}
            onDelete={() => onDeleteKeyword(keyword.id)}
            sx={{ mr: 1, mb: 1 }}
          />
        ))}
      </Box>
    </>
  );
}
