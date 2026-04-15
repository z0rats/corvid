import { useState, useMemo } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import ChatIcon from '@mui/icons-material/Chat';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ShowAiAnswer from './ShowAiAnswer';

export default function MessageBody({ result }) {
  const [expanded, setExpanded] = useState(true);

  const lines = useMemo(() => String(result ?? '').split('\n'), [result]);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
      TransitionProps={{ unmountOnExit: false }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="message-body-content"
        id="message-body-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <ChatIcon sx={{ mr: 1 }} fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">
            Message body
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        <Box
          component="pre"
          sx={{
            fontSize: '0.8rem',
            fontFamily: 'monospace',
            maxWidth: '100%',
            overflow: 'auto',
            maxHeight: '600px',
            m: 0,
            p: 0,
            bgcolor: 'action.hover',
            borderRadius: 1,
          }}
        >
          <Box component="table" sx={{ borderCollapse: 'collapse', width: '100%', tableLayout: 'fixed' }}>
            <Box component="colgroup">
              <Box component="col" sx={{ width: '3.5rem' }} />
              <Box component="col" />
            </Box>
            <tbody>
              {lines.map((line, index) => (
                <Box component="tr" key={index}>
                  <Box
                    component="td"
                    sx={{
                      px: 1.5,
                      py: 0.25,
                      textAlign: 'right',
                      userSelect: 'none',
                      color: 'text.disabled',
                      borderRight: 1,
                      borderColor: 'divider',
                      verticalAlign: 'top',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {index + 1}
                  </Box>
                  <Box
                    component="td"
                    sx={{
                      px: 1.5,
                      py: 0.25,
                      whiteSpace: 'pre-wrap',
                      overflowWrap: 'break-word',
                      wordBreak: 'break-all',
                    }}
                  >
                    {line}
                  </Box>
                </Box>
              ))}
            </tbody>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        <ShowAiAnswer input={result} />
      </AccordionDetails>
    </Accordion>
  );
}
