import React from 'react';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import { useTheme } from '@mui/material/styles';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveChoropleth } from '@nivo/geo';
import worldCountries from '../../../data/world_countries.json';
import { transformDataForPie, transformDataForMap } from './utils/crowdSecDataUtils';

export default function CrowdSecCountriesSection({ targetCountries }) {
  const theme = useTheme();
  if (!targetCountries || Object.keys(targetCountries).length === 0) return null;

  const maxValue = Math.max(1, ...Object.values(targetCountries));

  return (
    <Grid size={12}>
      <Card sx={{ mt: 2, p: 2, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" component="h3" gutterBottom>
          Target Countries by Report Count
        </Typography>
        <Grid container spacing={2} alignItems="stretch">
          <Grid size={{ xs: 12, md: 5 }} sx={{ height: "400px" }}>
            <ResponsivePie
              data={transformDataForPie(targetCountries)}
              sortByValue={true}
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
              innerRadius={0.5}
              padAngle={1}
              cornerRadius={3}
              activeOuterRadiusOffset={8}
              colors={{ scheme: "blues" }}
              borderWidth={1}
              borderColor={{ from: "color", modifiers: [["darker", 0.2]] }}
              arcLinkLabelsSkipAngle={10}
              arcLinkLabelsTextColor={theme.palette.text.primary}
              arcLinkLabelsThickness={2}
              arcLinkLabelsColor={{ from: "color" }}
              arcLabelsSkipAngle={10}
              arcLabelsTextColor={{ from: "color", modifiers: [["darker", 2]] }}
              theme={{ tooltip: { container: { background: theme.palette.background.paper, color: theme.palette.text.primary, fontSize: "12px" } } }}
            />
          </Grid>
          <Grid size={{ xs: 12, md: 7 }} sx={{ height: "400px" }}>
            <ResponsiveChoropleth
              data={transformDataForMap(targetCountries)}
              features={worldCountries.features}
              margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
              colors="YlGnBu"
              domain={[0, maxValue]}
              unknownColor={theme.palette.divider}
              label="properties.name"
              valueFormat=".2s"
              projectionScale={Math.min(150, 150 * (400 / 600))}
              projectionTranslation={[0.5, 0.5]}
              borderWidth={0.5}
              borderColor={theme.palette.text.primary}
              theme={{ tooltip: { container: { background: theme.palette.background.paper, color: theme.palette.text.primary, fontSize: "12px" } } }}
              legends={[]}
            />
          </Grid>
        </Grid>
      </Card>
    </Grid>
  );
}
