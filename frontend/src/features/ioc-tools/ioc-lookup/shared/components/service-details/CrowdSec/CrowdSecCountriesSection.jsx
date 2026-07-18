import React from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import MuiTooltip from '@mui/material/Tooltip';
import { useTheme } from '@mui/material/styles';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { NaturalEarth } from '@visx/geo';
import { scaleSequential } from '@visx/vendor/d3-scale';
import { format } from '@visx/vendor/d3-format';
import { interpolateYlGnBu } from 'd3-scale-chromatic';
import worldCountries from '../../../data/world_countries.json';
import { transformDataForPie, transformDataForMap } from './utils/crowdSecDataUtils';
import { getCategoricalColor, foldExcessCategories } from '../../../../../../../core/utils/chartColors';

const MAP_WIDTH = 960;
const MAP_HEIGHT = 500;
const formatMapValue = format('.2s');

export default function CrowdSecCountriesSection({ targetCountries }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  if (!targetCountries || Object.keys(targetCountries).length === 0) return null;

  const maxValue = Math.max(1, ...Object.values(targetCountries));
  const pieData = foldExcessCategories(transformDataForPie(targetCountries), t('providers.common.other'))
    .sort((a, b) => b.value - a.value);
  const valueById = new Map(transformDataForMap(targetCountries).map((d) => [d.id, d.value]));
  const colorScale = scaleSequential(interpolateYlGnBu).domain([0, maxValue]);

  return (
    <Grid size={12}>
      <Card sx={{ mt: 2, p: 2, borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
        <Typography variant="h6" component="h3" gutterBottom>
          {t('providers.crowdsec.targetCountriesByReportCount')}
        </Typography>
        <Grid container spacing={2} alignItems="stretch">
          <Grid size={{ xs: 12, md: 5 }} sx={{ height: "400px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="label"
                  innerRadius="50%"
                  outerRadius="80%"
                  paddingAngle={1}
                  cornerRadius={3}
                  stroke={theme.palette.background.paper}
                  strokeWidth={1}
                  isAnimationActive={false}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={entry.id} fill={getCategoricalColor(theme, index)} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: theme.palette.background.paper,
                    color: theme.palette.text.primary,
                    fontSize: 12,
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: theme.shape.borderRadius,
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  wrapperStyle={{ color: theme.palette.text.secondary, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </Grid>
          <Grid size={{ xs: 12, md: 7 }} sx={{ height: "400px" }}>
            <svg width="100%" height="100%" viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} preserveAspectRatio="xMidYMid meet">
              <NaturalEarth data={worldCountries.features} fitSize={[[MAP_WIDTH, MAP_HEIGHT], worldCountries]}>
                {({ features }) =>
                  features.map(({ feature, path }) => {
                    const value = valueById.get(feature.id);
                    return (
                      <MuiTooltip
                        key={feature.id}
                        title={`${feature.properties.name}: ${value != null ? formatMapValue(value) : 0}`}
                        arrow
                      >
                        <path
                          d={path || ''}
                          fill={value != null ? colorScale(value) : theme.palette.divider}
                          stroke={theme.palette.text.primary}
                          strokeWidth={0.5}
                        />
                      </MuiTooltip>
                    );
                  })
                }
              </NaturalEarth>
            </svg>
          </Grid>
        </Grid>
      </Card>
    </Grid>
  );
}
