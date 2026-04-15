import React, { useState } from 'react';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid2';

import { SIGMA_CONSTANTS } from '../../constants/sigmaConstants';
import KeywordsInput from './KeywordsInput';
import SelectionConditions from './SelectionConditions';

export default function Detection({
  detections,
  handleDetectionsChange,
  conditionsList,
  handleConditionsListChange,
}) {
  const [keywords, setKeywords] = useState([]);

  const handleAddKeyword = (keyword) => {
    setKeywords((prev) => [...prev, { id: crypto.randomUUID(), value: keyword }]);
  };

  const handleDeleteKeyword = (idToDelete) => {
    setKeywords((prev) => prev.filter((keyword) => keyword.id !== idToDelete));
  };

  const handleAddCondition = (condition) => {
    handleConditionsListChange((prev) => [...prev, condition]);
  };

  const handleDeleteCondition = (idToDelete) => {
    handleConditionsListChange((prev) => prev.filter((cond) => cond.id !== idToDelete));
  };

  return (
    <Box>
      <Typography variant="caption" display="block" gutterBottom>
        If your list consists of a single element, don't use a list.
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        Use only lowercase identifiers.
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        Put comments on lines if you like to (use 2 spaces to separate the expression
        from your comment, e.g. - 'cmd.exe' # command line).
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        Don't use regular expressions unless you really have to (e.g. instead of
        CommandLine|re: '\\payload.*\skeyset' use CommandLine|contains|all with
        the values \payload and keyset).
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        In new sources use the field names as they appear in the log source, remove
        spaces and keep hyphens (e.g. SAM User Account becomes SAMUserAccount).
      </Typography>
      <Typography variant="caption" display="block" gutterBottom>
        Don't use SIEM specific logic in your condition.
      </Typography>

      {/* Keywords Section */}
      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
        Keywords
      </Typography>
      <KeywordsInput
        keywords={keywords}
        onAddKeyword={handleAddKeyword}
        onDeleteKeyword={handleDeleteKeyword}
      />

      {/* Selection Conditions Section */}
      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
        Selection Conditions
      </Typography>
      <SelectionConditions
        conditionsList={conditionsList}
        onAddCondition={handleAddCondition}
        onDeleteCondition={handleDeleteCondition}
      />

      {/* Filter and Timeframe */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Filter"
            value={detections.filter}
            onChange={(e) =>
              handleDetectionsChange((prev) => ({ ...prev, filter: e.target.value }))
            }
            size="small"
            variant="outlined"
            placeholder="e.g., selection and some_other_condition"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <TextField
            fullWidth
            label="Timeframe"
            value={detections.timeframe}
            onChange={(e) =>
              handleDetectionsChange((prev) => ({ ...prev, timeframe: e.target.value }))
            }
            size="small"
            variant="outlined"
            placeholder="e.g., 1h, 30m"
          />
        </Grid>
      </Grid>

      {/* Condition Selection */}
      {(conditionsList.length > 0 || keywords.length > 0 || detections.filter || detections.timeframe) && (
        <FormControl fullWidth size="small" sx={{ mt: 2 }}>
          <InputLabel>Condition</InputLabel>
          <Select
            value={detections.condition}
            label="Condition"
            onChange={(e) =>
              handleDetectionsChange((prev) => ({ ...prev, condition: e.target.value }))
            }
          >
            {SIGMA_CONSTANTS.CONDITIONS.map((condition) => (
              <MenuItem key={condition} value={condition}>
                {condition}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
    </Box>
  );
}
