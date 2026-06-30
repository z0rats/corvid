import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';

export default function CustomTagsSection({ tags, onTagsChange }) {
  const { t } = useTranslation('ruleCreator');
  const [currentTag, setCurrentTag] = useState('');

  const handleAdd = () => {
    if (!currentTag.trim()) {
      alert(t('snort.customTagsSection.requiredAlert'));
      return;
    }
    if (tags.some((tag) => tag.value === currentTag.trim())) {
      alert(t('snort.customTagsSection.duplicateAlert'));
      return;
    }
    onTagsChange([...tags, { id: crypto.randomUUID(), value: currentTag.trim() }]);
    setCurrentTag('');
  };

  const handleDelete = (idToDelete) => {
    onTagsChange(tags.filter((tag) => tag.id !== idToDelete));
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t('snort.customTagsSection.header')}
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 10 }}>
          <TextField
            fullWidth
            label={t('snort.customTagsSection.addLabel')}
            value={currentTag}
            onChange={(e) => setCurrentTag(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAdd();
              }
            }}
            size="small"
            variant="outlined"
            placeholder={t('snort.customTagsSection.addPlaceholder')}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddCircleIcon />}
            onClick={handleAdd}
            disabled={!currentTag.trim()}
            size="small"
            fullWidth
          >
            {t('common.actions.add')}
          </Button>
        </Grid>
      </Grid>

      {tags.length > 0 && (
        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {tags.map((tag) => (
            <Chip
              key={tag.id}
              label={tag.value}
              onDelete={() => handleDelete(tag.id)}
              size="small"
              variant="outlined"
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
