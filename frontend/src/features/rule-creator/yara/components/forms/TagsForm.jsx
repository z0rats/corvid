import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import FingerprintIcon from '@mui/icons-material/Fingerprint';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

/**
 * Form component for managing YARA rule tags
 * @param {Object} props - Component props
 * @param {Array} props.tags - Current tags array
 * @param {string} props.currentTag - Current tag being typed
 * @param {Function} props.onCurrentTagChange - Handler for current tag changes
 * @param {Function} props.onAddTag - Handler for adding a tag
 * @param {Function} props.onDeleteTag - Handler for deleting a tag
 * @param {boolean} props.canAddTag - Whether a tag can be added
 */
export default function TagsForm({ 
  tags, 
  currentTag, 
  onCurrentTagChange, 
  onAddTag, 
  onDeleteTag,
  canAddTag 
}) {
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && canAddTag) {
      event.preventDefault();
      onAddTag();
    }
  };

  const handleCurrentTagChange = (event) => {
    onCurrentTagChange(event.target.value);
  };

  return (
    <Accordion sx={{ border: 'none', boxShadow: 'none', mt: 1 }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          px: 1,
          py: 0.5,
          minHeight: '40px',
          '& .MuiAccordionSummary-content': {
            margin: 0,
          },
        }}
      >
        <Box display="flex" alignItems="center">
          <FingerprintIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Tags</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Stack spacing={1}>
          <TextField
            label="Add Tag"
            value={currentTag}
            onChange={handleCurrentTagChange}
            onKeyPress={handleKeyPress}
            size="small"
            variant="outlined"
            slotProps={{
              input: {
                endAdornment: (
                  <Tooltip title="Add Tag">
                    <IconButton
                      onClick={onAddTag}
                      disabled={!canAddTag}
                      size="small"
                      aria-label="Add tag"
                    >
                      <AddCircleIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                ),
              },
            }}
            placeholder="Enter tag and press Enter or click Add"
          />
          
          {/* Tags display */}
          {tags.length > 0 && (
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {tags.map((tag) => (
                <Chip
                  key={tag.id}
                  label={tag.value}
                  onDelete={() => onDeleteTag(tag.id)}
                  size="small"
                  variant="outlined"
                  color="primary"
                />
              ))}
            </Stack>
          )}
          
          {/* Help text */}
          <Typography variant="caption" color="text.secondary">
            Tags help categorize and identify rules. Common tags include malware family names, 
            attack techniques, or file types.
          </Typography>
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}
