import React, { useState } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import LinkIcon from '@mui/icons-material/Link';

export default function References({ references, handleReferencesChange }) {
  const [currentReference, setCurrentReference] = useState('');

  const handleAddReference = () => {
    const trimmedReference = currentReference.trim();
    if (trimmedReference && !references.some((ref) => ref.value === trimmedReference)) {
      handleReferencesChange((prev) => [...prev, { id: crypto.randomUUID(), value: trimmedReference }]);
      setCurrentReference('');
    }
  };

  const handleDeleteReference = (idToDelete) => {
    handleReferencesChange((prev) => prev.filter((ref) => ref.id !== idToDelete));
  };

  return (
    <Box> 
      <Typography variant="subtitle2" gutterBottom>
        Add references to web pages or documents that provide more context about the detected threat.
      </Typography>
      <Typography variant="body2" ml={2} gutterBottom component="div"> 
        <ul>
          <li>Use links to web pages or documents only.</li>
          <li>Do not link to EVTX files, PCAPs, or other raw content.</li>
          <li>Do not include links to MITRE ATT&CK techniques (we use tags for that).</li>
        </ul>
      </Typography>
      <Typography variant="caption" gutterBottom>
        Examples: blog posts, tweets, project pages, manual pages, advisories, discussions.
      </Typography>
      <TextField
        fullWidth
        label="Reference"
        value={currentReference}
        onChange={(e) => setCurrentReference(e.target.value)}
        size="small"
        variant="outlined"
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            handleAddReference();
          }
        }}
        placeholder="Enter reference and press Enter or click Add"
        slotProps={{
          input: {
            endAdornment: (
              <Tooltip title="Add Reference">
                <IconButton
                  onClick={handleAddReference}
                  disabled={!currentReference.trim()}
                  size="small"
                  aria-label="Add reference"
                >
                  <AddCircleIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            ),
          },
        }}
        sx={{ mt: 2 }} 
      />
      {/* List of References */}
      {references.length > 0 && (
        <List sx={{ mt: 2, maxHeight: 150, overflow: 'auto' }}>
          {references.map((ref) => (
            <ListItem
              key={ref.id}
              secondaryAction={
                <IconButton
                  edge="end"
                  onClick={() => handleDeleteReference(ref.id)}
                  size="small"
                  aria-label="Delete reference"
                >
                  <DeleteIcon fontSize="small" color="error" />
                </IconButton>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <LinkIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={ref.value} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
