import React, { useMemo } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';

import NoDetails from '../NoDetails';
import CrowdSecReputationCard from './CrowdSecReputationCard';
import CrowdSecScoresChart from './CrowdSecScoresChart';
import CrowdSecCountriesSection from './CrowdSecCountriesSection';
import { buildScoreData } from './utils/crowdSecDataUtils';

export default function CrowdSecDetails({ result, ioc }) {
  const scoreData = useMemo(() => result ? buildScoreData(result) : [], [result]);

  if (!result || result.error) {
    const message = result?.error
      ? `Error fetching CrowdSec details: ${result.message || result.error}`
      : (result?.message?.includes("not found"))
        ? "IP not found in CrowdSec CTI."
        : "CrowdSec details are unavailable.";
    return <NoDetails message={message} />;
  }

  if (Object.keys(result).length === 0 || typeof result.ip_range_score === 'undefined') {
    return <NoDetails message="Insufficient data received from CrowdSec CTI." />;
  }

  return (
    <Box sx={{ p: 1 }}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6, lg: 5 }}>
          <CrowdSecReputationCard result={result} ioc={ioc} />
        </Grid>

        <Grid size={{ xs: 12, md: 6, lg: 7 }}>
          <CrowdSecScoresChart scoreData={scoreData} />
        </Grid>

        <CrowdSecCountriesSection targetCountries={result.target_countries} />

        {result.behaviors?.length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ mt: 2, p: 2, borderRadius: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6" component="h3" gutterBottom>Behaviours</Typography>
              <List dense>
                {result.behaviors.map((behaviour) => (
                  <ListItem key={behaviour.name || behaviour.label} disablePadding>
                    <ListItemText primary={behaviour.name || behaviour.label} secondary={behaviour.description} />
                  </ListItem>
                ))}
              </List>
            </Card>
          </Grid>
        )}

        {result.attack_details?.length > 0 && (
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ mt: 2, p: 2, borderRadius: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6" component="h3" gutterBottom>Attack Details</Typography>
              <List dense>
                {result.attack_details.map((attack) => (
                  <ListItem key={attack.name || attack.label} disablePadding>
                    <ListItemText primary={attack.name || attack.label} secondary={attack.description} />
                  </ListItem>
                ))}
              </List>
            </Card>
          </Grid>
        )}

        {result.references?.length > 0 && (
          <Grid size={12}>
            <Card sx={{ mt: 2, p: 2, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="h6" component="h3" gutterBottom>References</Typography>
              <List dense>
                {result.references.map((ref, index) => (
                  <ListItem key={ref.name || ref.url || `ref-${index}`} disablePadding>
                    <ListItemText primary={ref.name || ref.label || `Reference ${index + 1}`} secondary={ref.description || ref.url || "No description"} />
                  </ListItem>
                ))}
              </List>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}
