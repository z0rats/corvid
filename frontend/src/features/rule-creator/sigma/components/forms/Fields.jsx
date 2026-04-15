import React, { useState } from 'react';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import AddCircleIcon from '@mui/icons-material/AddCircle';

export default function Fields({ fields, handleFieldsChange }) {
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
      <Typography variant="caption" display="block" gutterBottom>
        These are the fields that are very helpful in the evaluation of a certain
        event. For example, it is helpful to know the parent process of a process
        that contains suspicious strings in its command line parameters. These
        fields could be extracted automatically and presented to the analyst in
        order to speed up the analysis.
      </Typography>

      <Grid container spacing={1} alignItems="center">
        <Grid size={12}>
          <TextField
            fullWidth
            label="Add Field"
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
            placeholder="Enter field"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title="Add Field">
                      <IconButton
                        onClick={handleAddField}
                        disabled={!currentField.trim()}
                        size="small"
                        aria-label="Add field"
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
