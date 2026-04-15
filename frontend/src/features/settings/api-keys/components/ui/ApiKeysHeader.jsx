import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useTheme } from '@mui/material/styles';

export default function ApiKeysHeader({ configuredCount, totalServices, completionPercentage, expanded, onToggle }) {
  const theme = useTheme();

  return (
    <Paper
      elevation={0}
      sx={{
        mb: 2,
        borderRadius: 1,
        border: 'none !important',
        boxShadow: 'none !important',
      }}
    >
      <Accordion
        expanded={expanded}
        onChange={onToggle}
        elevation={0}
        sx={{
          backgroundColor: 'transparent',
          border: 'none !important',
          boxShadow: 'none !important',
          '&:before': { display: 'none' },
          '&.Mui-expanded': { border: 'none !important' },
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          sx={{
            p: 2,
            '& .MuiAccordionSummary-content': { margin: 0 },
            '& .MuiAccordionSummary-content.Mui-expanded': { margin: 0 },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <VpnKeyIcon sx={{ fontSize: 32, color: theme.palette.text.secondary }} />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                API Key Management
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {configuredCount}/{totalServices} services configured ({completionPercentage}% complete)
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>

        <AccordionDetails sx={{ px: 2, pb: 2, pt: 0 }}>
          <Stack spacing={3}>
            <Typography variant="body1" color="text.secondary">
              Configure your threat intelligence and security API keys to unlock the full potential of this platform.
            </Typography>

            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Configuration Progress ({configuredCount}/{totalServices} services)
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {completionPercentage}% Complete
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={completionPercentage}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: theme.palette.grey[200],
                  '& .MuiLinearProgress-bar': { borderRadius: 4 },
                }}
              />
            </Box>

            <Box sx={{ p: 2, backgroundColor: theme.palette.action.hover, borderRadius: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Getting Started
              </Typography>
              <Typography variant="body2" color="text.secondary">
                While initial setup requires generating multiple API keys, the enhanced security and intelligence capabilities make it worthwhile. Most services offer free tiers to get you started.
              </Typography>
            </Box>
          </Stack>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
}
