import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

export default function WelcomeScreen() {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Image Tools
      </Typography>
      <Box sx={{ mb: 4 }}>
        <Typography paragraph>
          Image Tools lets you inspect an image file for OSINT purposes. Upload a picture to see
          every piece of metadata it carries — camera/device info, capture timestamp, GPS
          location, and the software used to create or edit it.
        </Typography>
        <Typography>
          You can also kick off a reverse image search without any API keys: provide the
          image's URL (if it has one) to get deep links straight into Google Lens, Yandex,
          Bing, and TinEye, or use the same buttons to open each engine for a manual upload.
        </Typography>
      </Box>

      <Typography variant="h6" sx={{ mb: 2 }}>
        Key Features
      </Typography>

      <Grid container spacing={1}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              EXIF & GPS
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Full EXIF tag breakdown plus a map link when GPS data is present
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              File Properties & Hashes
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Format, dimensions, color mode, DPI, and MD5/SHA1/SHA256 hashes
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              Reverse Image Search
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Deep links into Google Lens, Yandex, Bing, and TinEye — no API keys required
            </Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <Paper elevation={0} sx={{ p: 1 }}>
            <Typography color="primary" fontWeight="medium">
              Privacy-Friendly
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your image is only sent to this app's own backend, never to a third party
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}
