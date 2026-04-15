import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
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
import CodeIcon from '@mui/icons-material/Code';

export default function PcreSection({ pcreList, onPcreChange }) {
  const [currentPcre, setCurrentPcre] = useState({ pattern: '' });

  const handleAdd = () => {
    if (!currentPcre.pattern.trim()) {
      alert('PCRE pattern is required.');
      return;
    }
    onPcreChange([...pcreList, { id: crypto.randomUUID(), pattern: currentPcre.pattern.trim() }]);
    setCurrentPcre({ pattern: '' });
  };

  const handleDelete = (idToDelete) => {
    onPcreChange(pcreList.filter((pcre) => pcre.id !== idToDelete));
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle2" gutterBottom>
        PCRE (Perl Compatible Regular Expressions)
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 10 }}>
          <TextField
            fullWidth
            label="PCRE Pattern"
            value={currentPcre.pattern}
            onChange={(e) => setCurrentPcre(prev => ({ ...prev, pattern: e.target.value }))}
            size="small"
            variant="outlined"
            placeholder="/pattern/flags (e.g., /GET\s+\/admin/i)"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddCircleIcon />}
            onClick={handleAdd}
            disabled={!currentPcre.pattern.trim()}
            size="small"
            fullWidth
          >
            Add
          </Button>
        </Grid>
      </Grid>

      {pcreList.length > 0 && (
        <List sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
          {pcreList.map((pcre) => (
            <ListItem
              key={pcre.id}
              secondaryAction={
                <Tooltip title="Delete PCRE">
                  <IconButton edge="end" onClick={() => handleDelete(pcre.id)} size="small" aria-label="Delete PCRE">
                    <DeleteIcon fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <CodeIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={pcre.pattern} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
