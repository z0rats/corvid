import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function WelcomeScreen() {
  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" component="h1" gutterBottom>
          Domain Finder
        </Typography>
        <Typography paragraph>
          Domain Finder is a module that helps you protect your organization from phishing attacks 
          by allowing you to search for recently registered domains that match a specific pattern. 
          This can help you identify potential threats before they occur.
        </Typography>
        <Typography paragraph>
          Using the URLScan.io API, the module allows you to view screenshots of websites to see what 
          is behind a domain without the need to visit the site and potentially expose yourself to danger. 
          Additionally, with just a single click, you can check each domain and the IP it resolves to 
          against multiple threat intelligence services to further protect your organization.
        </Typography>
        <Typography variant="body2" sx={{ 
          p: 2, 
          borderRadius: 1,
          fontFamily: 'monospace'
        }}>
          For example, you can use the module to search for domains that start with "google-" by using 
          the search pattern "google-*".
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        Features
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">Pattern Matching</Typography>
            <Typography variant="body2" color="text.secondary">
              Search for recently registered domains using specific patterns
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">Safe Preview</Typography>
            <Typography variant="body2" color="text.secondary">
              View website screenshots via URLScan.io integration
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">Threat Intelligence</Typography>
            <Typography variant="body2" color="text.secondary">
              Check domains and IPs against multiple security services
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">Proactive Defense</Typography>
            <Typography variant="body2" color="text.secondary">
              Identify potential phishing threats before they become active
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}
