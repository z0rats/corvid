import React, { useState } from 'react';
import Autocomplete from '@mui/material/Autocomplete';
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
import Grid from '@mui/material/Grid';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import RadarIcon from '@mui/icons-material/Radar';

import { SIGMA_CONSTANTS, INITIAL_CONDITION } from '../../constants/sigmaConstants';
import fieldData from '../../data/FieldData.json';

export default function SelectionConditions({ conditionsList, onAddCondition, onDeleteCondition }) {
  const [currentCondition, setCurrentCondition] = useState(INITIAL_CONDITION);

  const handleAdd = () => {
    if (currentCondition.field.trim() === '' || currentCondition.value.trim() === '') {
      alert('Field and Value are required for a condition.');
      return;
    }
    onAddCondition({
      id: crypto.randomUUID(),
      field: currentCondition.field.trim(),
      modifier: currentCondition.modifier,
      value: currentCondition.value.trim(),
    });
    setCurrentCondition(INITIAL_CONDITION);
  };

  return (
    <>
      <Grid container spacing={1} alignItems="center">
        <Grid size={{ xs: 12, sm: 4 }}>
          <Autocomplete
            options={fieldData}
            value={currentCondition.field}
            onChange={(event, newValue) =>
              setCurrentCondition((prev) => ({ ...prev, field: newValue || '' }))
            }
            onInputChange={(event, newInputValue) =>
              setCurrentCondition((prev) => ({ ...prev, field: newInputValue }))
            }
            freeSolo
            renderInput={(params) => (
              <TextField {...params} label="Field" size="small" variant="outlined" />
            )}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 3 }}>
          <FormControl fullWidth size="small">
            <InputLabel>Modifier</InputLabel>
            <Select
              value={currentCondition.modifier}
              label="Modifier"
              onChange={(e) =>
                setCurrentCondition((prev) => ({ ...prev, modifier: e.target.value }))
              }
            >
              {SIGMA_CONSTANTS.MODIFIERS.map((mod) => (
                <MenuItem key={mod} value={mod}>
                  {mod}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <TextField
            fullWidth
            label="Value"
            value={currentCondition.value}
            onChange={(e) =>
              setCurrentCondition((prev) => ({ ...prev, value: e.target.value }))
            }
            size="small"
            variant="outlined"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAdd();
              }
            }}
            placeholder="Enter value and press Enter or click Add"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 1 }}>
          <Tooltip title="Add Condition">
            <IconButton
              onClick={handleAdd}
              disabled={!currentCondition.field.trim() || !currentCondition.value.trim()}
              size="small"
              aria-label="Add condition"
            >
              <AddCircleIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Grid>
      </Grid>

      {conditionsList.length > 0 && (
        <List sx={{ mt: 2, maxHeight: 150, overflow: 'auto' }}>
          {conditionsList.map((cond) => (
            <ListItem
              key={cond.id}
              secondaryAction={
                <Tooltip title="Delete Condition">
                  <IconButton edge="end" onClick={() => onDeleteCondition(cond.id)} size="small" aria-label="Delete condition">
                    <DeleteIcon fontSize="small" color="error" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <RadarIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={`${cond.field} ${
                  cond.modifier !== 'equals' ? `|${cond.modifier}` : ''
                } ${cond.modifier === 're' ? '' : cond.modifier} "${cond.value}"`}
              />
            </ListItem>
          ))}
        </List>
      )}
    </>
  );
}
