import React, { useState } from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import AddCircleIcon from '@mui/icons-material/AddCircle';

import tagData from '../../data/TagData.json';

const tagSuggestions = Object.values(tagData).flat();

export default function Tags({ tags, handleTagsChange }) {
  const [tagInput, setTagInput] = useState('');

  const handleAddTag = () => {
    const trimmedTag = tagInput.trim().toLowerCase();
    if (trimmedTag && !tags.some((tag) => tag.value === trimmedTag)) {
      handleTagsChange((prev) => [...prev, { id: crypto.randomUUID(), value: trimmedTag }]);
      setTagInput('');
    }
  };

  const handleDeleteTag = (idToDelete) => {
    handleTagsChange((prev) => prev.filter((tag) => tag.id !== idToDelete));
  };

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>
        Use tags from MITRE ATT&CK, CAR and tags for CVE numbers.
      </Typography>
      <Typography variant="caption" gutterBottom>
        Examples tags: attack.credential_access, attack.t1003.002, car.2013-07-001, cve.2020.10189
        <br />
        Use lower-case tags only. Use . or - as divider in tag names. Replace space with an underscore _.
      </Typography>
      <Autocomplete
        freeSolo
        options={tagSuggestions}
        value={tagInput}
        onChange={(event, newValue) => {
          setTagInput(newValue || ''); 
          if (newValue) {
            handleAddTag();
          }
        }}
        onInputChange={(event, newInputValue) => {
          setTagInput(newInputValue);
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Add Tag"
            size="small"
            variant="outlined"
            placeholder="Enter tag and press Enter or click Add"
            slotProps={{
              input: {
                ...params.InputProps,
                endAdornment: (
                  <IconButton onClick={handleAddTag} disabled={!tagInput.trim()} size="small" aria-label="Add tag">
                    <AddCircleIcon fontSize="small" />
                  </IconButton>
                ),
              },
            }}
          />
        )}
        sx={{ mt: 2 }}
      />
      {/* Display Tags */}
      {tags.length > 0 && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 2 }}>
          {tags.map((tag) => (
            <Chip
              key={tag.id}
              label={`#${tag.value}`}
              onDelete={() => handleDeleteTag(tag.id)}
              size="small"
              variant="outlined"
            />
          ))}
        </Stack>
      )}
    </Box>
  );
}
