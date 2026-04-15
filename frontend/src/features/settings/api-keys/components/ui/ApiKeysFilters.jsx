import React from 'react';
import FormControlLabel from '@mui/material/FormControlLabel';
import InputAdornment from '@mui/material/InputAdornment';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import SearchIcon from '@mui/icons-material/Search';

export default function ApiKeysFilters({ searchFilter, showOnlyConfigured, onSearchChange, onToggleConfigured }) {
  return (
    <Paper
      elevation={0}
      sx={{ p: 3, mb: 3, borderRadius: 1 }}
    >
      <Stack direction="row" spacing={3} alignItems="center">
        <TextField
          placeholder="Search services..."
          value={searchFilter}
          onChange={(e) => onSearchChange(e.target.value)}
          variant="outlined"
          size="small"
          sx={{ flex: 1 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
            },
          }}
        />
        <FormControlLabel
          control={
            <Switch
              checked={showOnlyConfigured}
              onChange={onToggleConfigured}
              color="primary"
              sx={{ mr: 1 }}
            />
          }
          label="Show only configured"
        />
      </Stack>
    </Paper>
  );
}
