import React, { useState } from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import { SNORT_CONSTANTS } from '../../constants/snortConstants';

export default function ContentMatching({ contentList, onContentChange }) {
  const [currentContent, setCurrentContent] = useState({ value: '', modifiers: [] });

  const handleAdd = () => {
    if (!currentContent.value.trim()) {
      alert('Content value is required.');
      return;
    }
    onContentChange([...contentList, {
      id: crypto.randomUUID(),
      value: currentContent.value.trim(),
      modifiers: [...currentContent.modifiers],
    }]);
    setCurrentContent({ value: '', modifiers: [] });
  };

  const handleDelete = (idToDelete) => {
    onContentChange(contentList.filter((content) => content.id !== idToDelete));
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle2" gutterBottom>
        Content Matching
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Content"
            value={currentContent.value}
            onChange={(e) => setCurrentContent(prev => ({ ...prev, value: e.target.value }))}
            size="small"
            variant="outlined"
            placeholder="String to match (e.g., GET /admin)"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Autocomplete
            multiple
            options={SNORT_CONSTANTS.CONTENT_MODIFIERS}
            value={currentContent.modifiers}
            onChange={(_, newValue) => setCurrentContent(prev => ({ ...prev, modifiers: newValue }))}
            renderInput={(params) => (
              <TextField {...params} label="Modifiers" placeholder="Select modifiers" size="small" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip variant="outlined" label={option} size="small" {...getTagProps({ index })} />
              ))
            }
            size="small"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddCircleIcon />}
            onClick={handleAdd}
            disabled={!currentContent.value.trim()}
            size="small"
            fullWidth
          >
            Add
          </Button>
        </Grid>
      </Grid>

      {contentList.length > 0 && (
        <List sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
          {contentList.map((content) => (
            <ListItem
              key={content.id}
              secondaryAction={
                <Tooltip title="Delete Content">
                  <IconButton edge="end" onClick={() => handleDelete(content.id)} size="small" aria-label="Delete content">
                    <DeleteIcon fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <SearchIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={`"${content.value}"`}
                secondary={content.modifiers.length > 0 ? `Modifiers: ${content.modifiers.join(', ')}` : 'No modifiers'}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
