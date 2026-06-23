import React, { useState } from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import Chip from '@mui/material/Chip';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Grid from '@mui/material/Grid';
import EditIcon from '@mui/icons-material/Edit';
import AddCircleIcon from '@mui/icons-material/AddCircle';

import { generateUUIDv4 } from '../../../shared/utils/ruleUtils';
import { SIGMA_CONSTANTS } from '../../constants/sigmaConstants';
import licensesData from '../../data/licenses.json';

const licenses = licensesData.licenses.map((license) => license.licenseId);

export default function Metadata({ metadata, handleMetadataChange }) {
  const [authorInput, setAuthorInput] = useState('');

  const handleGenerateUUID = () => {
    handleMetadataChange((prev) => ({
      ...prev,
      id: generateUUIDv4(),
    }));
  };

  const handleAddAuthor = () => {
    const trimmedAuthor = authorInput.trim();
    if (trimmedAuthor && !metadata.authors.some((author) => author.value === trimmedAuthor)) {
      handleMetadataChange((prev) => ({
        ...prev,
        authors: [...prev.authors, { id: crypto.randomUUID(), value: trimmedAuthor }],
      }));
      setAuthorInput('');
    }
  };

  const handleDeleteAuthor = (idToDelete) => {
    handleMetadataChange((prev) => ({
      ...prev,
      authors: prev.authors.filter((author) => author.id !== idToDelete),
    }));
  };

  return (
    <Grid container spacing={2} rowSpacing={2}> 
      {/* Title */}
      <Grid size={{ xs: 12, sm: 6 }}>
        <TextField
          fullWidth
          label="Title"
          value={metadata.title}
          onChange={(e) => handleMetadataChange((prev) => ({ ...prev, title: e.target.value }))}
          required
          size="small"
          variant="outlined"
        />
      </Grid>
      {/* ID */}
      <Grid size={{ xs: 12, sm: 6 }}>
        <TextField
          fullWidth
          label="ID"
          value={metadata.id}
          onChange={(e) => handleMetadataChange((prev) => ({ ...prev, id: e.target.value }))}
          required
          size="small"
          variant="outlined"
          slotProps={{
            input: {
              endAdornment: (
                <Tooltip title="Generate New UUID">
                  <IconButton onClick={handleGenerateUUID} size="small" aria-label="Generate UUID">
                    <EditIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              ),
            },
          }}
        />
      </Grid>
      {/* Description */}
      <Grid size={12}>
        <TextField
          fullWidth
          label="Description"
          multiline
          rows={2}
          value={metadata.description}
          onChange={(e) => handleMetadataChange((prev) => ({ ...prev, description: e.target.value }))}
          size="small"
          variant="outlined"
        />
      </Grid>
      {/* Date and Modified Date */}
      <Grid size={{ xs: 12, sm: 6 }}> 
        <Stack direction="row" spacing={2} alignItems="center"> 
          <TextField
            fullWidth
            label="Date"
            type="date"
            value={metadata.date}
            onChange={(e) => handleMetadataChange((prev) => ({ ...prev, date: e.target.value }))}
            size="small"
            variant="outlined"
            slotProps={{
              inputLabel: { shrink: true },
            }}
          />
          <TextField
            fullWidth
            label="Modified Date"
            type="date"
            value={metadata.modified}
            onChange={(e) => handleMetadataChange((prev) => ({ ...prev, modified: e.target.value }))}
            size="small"
            variant="outlined"
            slotProps={{
              inputLabel: { shrink: true },
            }}
          />
        </Stack>
      </Grid>
      {/* Level and Status */}
      <Grid size={{ xs: 12, sm: 6 }}>
        <Stack direction="row" spacing={2} alignItems="center"> 
          <FormControl fullWidth size="small">
            <InputLabel>Level</InputLabel>
            <Select
              value={metadata.level}
              label="Level"
              onChange={(e) => handleMetadataChange((prev) => ({ ...prev, level: e.target.value }))}
            >
              {SIGMA_CONSTANTS.LEVELS.map((level) => (
                <MenuItem key={level} value={level}>
                  {level}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              value={metadata.status}
              label="Status"
              onChange={(e) => handleMetadataChange((prev) => ({ ...prev, status: e.target.value }))}
            >
              {SIGMA_CONSTANTS.STATUSES.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Grid>
      {/* Authors and License */}
      <Grid size={12}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            fullWidth
            label="Add Author"
            value={authorInput}
            onChange={(e) => setAuthorInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddAuthor();
              }
            }}
            slotProps={{
              input: {
                endAdornment: (
                  <IconButton onClick={handleAddAuthor} disabled={!authorInput.trim()} size="small" aria-label="Add author">
                    <AddCircleIcon fontSize="small" />
                  </IconButton>
                ),
              },
            }}
            size="small"
            variant="outlined"
          />
          <Autocomplete
            fullWidth
            freeSolo
            options={licenses}
            value={metadata.license}
            onChange={(event, newValue) => {
              handleMetadataChange((prev) => ({ ...prev, license: newValue }));
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label="License"
                size="small"
                variant="outlined"
              />
            )}
          />
        </Stack>
        {/* Display Authors */}
        {metadata.authors.length > 0 && (
          <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1 }}>
            {metadata.authors.map((author) => (
              <Chip
                key={author.id}
                label={author.value}
                onDelete={() => handleDeleteAuthor(author.id)}
                size="small"
                variant="outlined"
              />
            ))}
          </Stack>
        )}
      </Grid>
    </Grid>
  );
}
