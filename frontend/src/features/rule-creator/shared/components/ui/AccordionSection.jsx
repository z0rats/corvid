import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function AccordionSection({ icon, title, children, defaultExpanded = false, sx = {} }) {
  return (
    <Accordion sx={{ border: 'none', boxShadow: 'none', ...sx }} defaultExpanded={defaultExpanded}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          px: 1,
          py: 0.5,
          minHeight: '40px',
          '& .MuiAccordionSummary-content': { margin: 0 },
        }}
      >
        <Box display="flex" alignItems="center">
          {icon}
          <Typography variant="subtitle2">{title}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        {children}
      </AccordionDetails>
    </Accordion>
  );
}
