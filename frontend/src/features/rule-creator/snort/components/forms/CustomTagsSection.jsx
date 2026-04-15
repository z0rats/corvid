import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import AddCircleIcon from '@mui/icons-material/AddCircle';

export default function CustomTagsSection({ tags, onTagsChange }) {
  const [currentTag, setCurrentTag] = useState('');

  const handleAdd = () => {
    if (!currentTag.trim()) {
      alert('Tag is required.');
      return;
    }
    if (tags.some((tag) => tag.value === currentTag.trim())) {
      alert('Tag already exists.');
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
        Custom Tags
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 10 }}>
          <TextField
            fullWidth
            label="Add Tag"
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
            placeholder="Enter custom tag"
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
            Add
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
