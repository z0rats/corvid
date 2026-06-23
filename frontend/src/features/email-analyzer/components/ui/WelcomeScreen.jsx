import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function WelcomeScreen() {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Email Analyzer
      </Typography>
      <Box sx={{ mb: 4 }}>
        <Typography paragraph>
          Email Analyzer is a module that allows you to analyze .eml files for potential threats. 
          To use the module, simply drag an .eml file into it. The module will then parse the file 
          and perform basic security checks to identify any potential risks.
        </Typography>
        <Typography>
          It also extracts all indicators of compromise (IOCs) from the file and makes it possible 
          to analyze them using various open source intelligence (OSINT) services. In addition, 
          Email Analyzer generates hash values for every attachment in the file, allowing you to 
          perform a privacy-friendly analysis of these files.
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        Key Features
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              Security Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Performs basic security checks on .eml files
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              IOC Extraction
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Extracts and analyzes IOCs using OSINT services
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              Attachment Analysis
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Generates hash values for all email attachments
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              Privacy-Friendly
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Analyze attachments without exposing original files
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}
