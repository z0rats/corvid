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

export default function FalsePositives({ falsePositives, handleFalsePositivesChange }) {
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
      <Typography variant="caption" display="block" gutterBottom>
        Think about possible false positive conditions that could also trigger the
        rule. This list should contain useful hints for an analyst. E.g. the
        comment "Legitimate processes that delete the shadow copies" can be a hint
        for an analyst to check for backup processes on that system or ask for any
        unusual administrative activity that involved the deletion of the local
        volume shadow copies.
      </Typography>

      <Grid container spacing={1} alignItems="center">
        <Grid size={12}>
          <TextField
            fullWidth
            label="Add False Positive"
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
            placeholder="Enter false positive"
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title="Add False Positive">
                      <IconButton
                        onClick={handleAddFalsePositive}
                        disabled={!currentFalsePositive.trim()}
                        size="small"
                        aria-label="Add false positive"
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
