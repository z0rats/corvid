import React, { useState } from 'react';
import IocLookupDialog from '../../../ioc-tools/ioc-lookup/shared/components/IocLookupDialog';
import { useIocLookupDialog } from '../../../ioc-tools/ioc-lookup/shared/hooks/useIocLookupDialog';
import { emailUtils } from '../../utils/emailUtils';
import { EMAIL_CONSTANTS } from '../../constants/emailConstants';
import EmailMetadata from './EmailMetadata';
import EmlHashValues from './EmlHashValues';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import InfoIcon from '@mui/icons-material/Info';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function GeneralInfo({ result, hashes }) {
  const [expanded, setExpanded] = useState(true);
  const { open, ioc, iocType, openDialog, closeDialog } = useIocLookupDialog();

  const senderEmail = emailUtils.extractEmailAddress(result['from']);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mt: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="general-info-content"
        id="general-info-header"
        sx={{ minHeight: '48px', padding: '0 16px' }}
      >
        <Box display="flex" alignItems="center">
          <InfoIcon sx={{ mr: 1 }} />
          <Typography variant="subtitle1" fontWeight="medium">General information</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 2, py: 1 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <EmailMetadata result={result} />
            <Box sx={{ mt: 1 }}>
              <Button
                variant="outlined"
                disableElevation
                size="small"
                sx={{ py: 0.25, px: 1.5, fontSize: '0.8125rem' }}
                onClick={() => openDialog(senderEmail, EMAIL_CONSTANTS.IOC_TYPES.EMAIL)}
              >
                Analyze sender address
              </Button>
            </Box>
          </Box>

          <Divider orientation="vertical" flexItem />

          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
              .eml file hashes
            </Typography>
            <EmlHashValues hashes={hashes} />
          </Box>
        </Box>

        <IocLookupDialog open={open} onClose={closeDialog} ioc={ioc} iocType={iocType} />
      </AccordionDetails>
    </Accordion>
  );
}
