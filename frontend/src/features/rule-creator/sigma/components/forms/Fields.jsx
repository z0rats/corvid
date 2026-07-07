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

export default function Fields({ fields, handleFieldsChange }) {
  const { t } = useTranslation('ruleCreator');
  const [currentField, setCurrentField] = useState('');

  const handleAddField = () => {
    const trimmedField = currentField.trim();
    if (trimmedField && !fields.some((field) => field.value === trimmedField)) {
      handleFieldsChange((prev) => [...prev, { id: crypto.randomUUID(), value: trimmedField }]);
      setCurrentField('');
    }
  };

  const handleDeleteField = (idToDelete) => {
    handleFieldsChange((prev) => prev.filter((field) => field.id !== idToDelete));
  };

  return (
    <>
      {/* Info text */}
      <Typography variant="caption" sx={{ display: 'block' }} gutterBottom>
        {t('sigma.fields.helpText')}
      </Typography>

      <Grid container spacing={1} alignItems="center">
        <Grid size={12}>
          <TextField
            fullWidth
            label={t('sigma.fields.addLabel')}
            value={currentField}
            onChange={(e) => setCurrentField(e.target.value)}
            size="small"
            variant="outlined"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddField();
              }
            }}
            placeholder={t('sigma.fields.addPlaceholder')}
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title={t('sigma.fields.addLabel')}>
                      <IconButton
                        onClick={handleAddField}
                        disabled={!currentField.trim()}
                        size="small"
                        aria-label={t('sigma.fields.addAria')}
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

      {/* Display Fields */}
      {fields.length > 0 && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 2 }}>
          {fields.map((field) => (
            <Chip
              key={field.id}
              label={field.value}
              onDelete={() => handleDeleteField(field.id)}
              size="small"
              variant="outlined"
            />
          ))}
        </Stack>
      )}
    </>
  );
}
