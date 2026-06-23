import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import InputLabel from '@mui/material/InputLabel';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import LinkIcon from '@mui/icons-material/Link';
import { SNORT_CONSTANTS } from '../../constants/snortConstants';

export default function ReferencesSection({ references, onReferencesChange }) {
  const [currentReference, setCurrentReference] = useState({ type: 'url', value: '' });

  const handleAdd = () => {
    if (!currentReference.value.trim()) {
      alert('Reference value is required.');
      return;
    }
    onReferencesChange([...references, { id: crypto.randomUUID(), ...currentReference, value: currentReference.value.trim() }]);
    setCurrentReference({ type: 'url', value: '' });
  };

  const handleDelete = (idToDelete) => {
    onReferencesChange(references.filter((ref) => ref.id !== idToDelete));
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="subtitle2" gutterBottom>
        References
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Type</InputLabel>
            <Select
              value={currentReference.type}
              label="Type"
              onChange={(e) => setCurrentReference(prev => ({ ...prev, type: e.target.value }))}
            >
              {SNORT_CONSTANTS.REFERENCE_TYPES.map((type) => (
                <MenuItem key={type} value={type}>
                  {type.toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 7 }}>
          <TextField
            fullWidth
            label="Reference Value"
            value={currentReference.value}
            onChange={(e) => setCurrentReference(prev => ({ ...prev, value: e.target.value }))}
            size="small"
            variant="outlined"
            placeholder="URL, CVE ID, etc."
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddCircleIcon />}
            onClick={handleAdd}
            disabled={!currentReference.value.trim()}
            size="small"
            fullWidth
          >
            Add
          </Button>
        </Grid>
      </Grid>

      {references.length > 0 && (
        <List sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
          {references.map((ref) => (
            <ListItem
              key={ref.id}
              secondaryAction={
                <Tooltip title="Delete Reference">
                  <IconButton edge="end" onClick={() => handleDelete(ref.id)} size="small" aria-label="Delete reference">
                    <DeleteIcon fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <LinkIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={`${ref.type.toUpperCase()}: ${ref.value}`} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
