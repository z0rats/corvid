import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import CodeIcon from '@mui/icons-material/Code';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

/**
 * Component for displaying the list of added strings
 * @param {Object} props - Component props
 * @param {Array} props.strings - Array of string objects
 * @param {Function} props.onDeleteString - Handler for deleting a string
 */
export default function StringsList({ strings, onDeleteString }) {
  if (strings.length === 0) {
    return null;
  }

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
          <CodeIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">
            Strings ({strings.length})
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <List sx={{ maxHeight: 200, overflow: 'auto' }}>
          {strings.map((string) => (
            <ListItem
              key={string.id}
              secondaryAction={
                <Tooltip title="Delete String">
                  <IconButton
                    edge="end"
                    onClick={() => onDeleteString(string.id)}
                    size="small"
                    color="error"
                    aria-label="Delete string"
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              }
              sx={{ py: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <CodeIcon fontSize="small" color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={`$${string.identifier}`}
                secondary={
                  <>
                    <Typography component="span" variant="caption" color="text.primary">
                      Type: {string.type.toUpperCase()}
                    </Typography>
                    {string.modifiers.length > 0 && (
                      <>
                        {' | '}
                        <Typography component="span" variant="caption" color="text.primary">
                          Modifiers: {string.modifiers.join(', ')}
                        </Typography>
                      </>
                    )}
                    <br />
                    <Typography 
                      component="span" 
                      variant="caption" 
                      color="text.secondary"
                      sx={{ 
                        wordBreak: 'break-word',
                        display: 'block',
                        maxWidth: '100%'
                      }}
                    >
                      Value: {string.value}
                    </Typography>
                  </>
                }
              />
            </ListItem>
          ))}
        </List>
      </AccordionDetails>
    </Accordion>
  );
}
