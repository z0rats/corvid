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
import Grid from '@mui/material/Grid2';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import FlowIcon from '@mui/icons-material/AccountTree';
import { SNORT_CONSTANTS } from '../../constants/snortConstants';

export default function FlowbitsSection({ flowbitsList, onFlowbitsChange }) {
  const [currentFlowbit, setCurrentFlowbit] = useState({ action: 'set', name: '' });

  const handleAdd = () => {
    if (!currentFlowbit.name.trim()) {
      alert('Flowbit name is required.');
      return;
    }
    onFlowbitsChange([...flowbitsList, {
      id: crypto.randomUUID(),
      action: currentFlowbit.action,
      name: currentFlowbit.name.trim(),
    }]);
    setCurrentFlowbit({ action: 'set', name: '' });
  };

  const handleDelete = (idToDelete) => {
    onFlowbitsChange(flowbitsList.filter((flowbit) => flowbit.id !== idToDelete));
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle2" gutterBottom>
        Flowbits
      </Typography>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Action</InputLabel>
            <Select
              value={currentFlowbit.action}
              label="Action"
              onChange={(e) => setCurrentFlowbit(prev => ({ ...prev, action: e.target.value }))}
            >
              {SNORT_CONSTANTS.FLOWBIT_ACTIONS.map((action) => (
                <MenuItem key={action} value={action}>
                  {action}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 7 }}>
          <TextField
            fullWidth
            label="Flowbit Name"
            value={currentFlowbit.name}
            onChange={(e) => setCurrentFlowbit(prev => ({ ...prev, name: e.target.value }))}
            size="small"
            variant="outlined"
            placeholder="flowbit_name"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddCircleIcon />}
            onClick={handleAdd}
            disabled={!currentFlowbit.name.trim()}
            size="small"
            fullWidth
          >
            Add
          </Button>
        </Grid>
      </Grid>

      {flowbitsList.length > 0 && (
        <List sx={{ mt: 1, maxHeight: 150, overflow: 'auto' }}>
          {flowbitsList.map((flowbit) => (
            <ListItem
              key={flowbit.id}
              secondaryAction={
                <Tooltip title="Delete Flowbit">
                  <IconButton edge="end" onClick={() => handleDelete(flowbit.id)} size="small" aria-label="Delete flowbit">
                    <DeleteIcon fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <FlowIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary={`${flowbit.action},${flowbit.name}`} />
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
}
