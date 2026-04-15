import React, { useState } from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { emailUtils } from '../../utils/emailUtils';

export default function SecurityCheck({ result }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="security-checks-content"
        id="security-checks-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <VerifiedUserIcon sx={{ mr: 1 }} fontSize="small" />
          <Typography variant="subtitle1" fontWeight="medium">Basic security checks</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ p: 1 }}>
        {result.map((warning, index) => (
          <Alert
            key={`ema_warnings_alert_${index}`}
            severity={emailUtils.getWarningLevel(warning.warning_tlp)}
            variant="outlined"
            sx={{ mb: 1, borderRadius: 1, borderLeftWidth: 4, '& .MuiAlert-message': { p: 0 } }}
          >
            <AlertTitle sx={{ m: 0, fontSize: '0.875rem', fontWeight: 500 }}>
              {warning.warning_title}
            </AlertTitle>
            <Typography variant="body2">{warning.warning_message}</Typography>
          </Alert>
        ))}
      </AccordionDetails>
    </Accordion>
  );
}
