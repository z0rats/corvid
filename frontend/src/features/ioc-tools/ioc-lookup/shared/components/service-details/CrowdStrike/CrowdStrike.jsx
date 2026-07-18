import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Chip from '@mui/material/Chip';
import Pagination from '@mui/material/Pagination';
import Paper from '@mui/material/Paper';
import Step from '@mui/material/Step';
import StepContent from '@mui/material/StepContent';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import Grid from '@mui/material/Grid';

import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SecurityIcon from '@mui/icons-material/Security';
import BugReportIcon from '@mui/icons-material/BugReport';
import CategoryIcon from '@mui/icons-material/Category';
import PersonIcon from '@mui/icons-material/Person';
import CodeIcon from '@mui/icons-material/Code';
import TimelineIcon from '@mui/icons-material/Timeline';
import DonutLargeIcon from '@mui/icons-material/DonutLarge';

import NoDetails from '../NoDetails';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getCategoricalColor, foldExcessCategories } from '../../../../../../../core/utils/chartColors';

const KILL_CHAIN_PHASE_IDS = [
  'reconnaissance',
  'weaponization',
  'delivery',
  'exploitation',
  'installation',
  'command_and_control',
  'actions_on_objectives',
];

const confidenceToScore = (level) => {
  switch (level?.toLowerCase()) {
    case "high": return 80;
    case "medium": return 50;
    case "low": return 20;
    case "unverified": return 5;
    default: return 0;
  }
};

const getConfidenceLevelColor = (level) => {
  switch (level?.toLowerCase()) {
    case "high": return "error";
    case "medium": return "warning";
    case "low": return "info";
    default: return "default";
  }
};

const mapKillChainToPhase = (chainNotation) => {
  if (!chainNotation) return '';
  const mappings = {
    'c2': 'command_and_control',
    'command and control': 'command_and_control',
    'reconnaissance': 'reconnaissance',
    'recon': 'reconnaissance',
    'delivery': 'delivery',
    'installation': 'installation',
    'exploit': 'exploitation',
    'exploitation': 'exploitation',
    'actions': 'actions_on_objectives',
    'actions on objectives': 'actions_on_objectives',
    'weaponization': 'weaponization'
  };
  const lowerChainNotation = chainNotation.toLowerCase();
  return mappings[lowerChainNotation] || lowerChainNotation;
};

export default function CrowdStrikeDetails({ result }) {
  const { t } = useTranslation('iocTools');
  const notAvailable = t('providers.common.notAvailable');
  const [page, setPage] = useState(1);
  const theme = useTheme();

  const indicators = useMemo(() => result?.resources || [], [result?.resources]);
  const rowsPerPage = 5;

  const threatTypes = useMemo(() => {
    const types = {};
    indicators.forEach(indicator => {
      if (indicator.threat_types && indicator.threat_types.length > 0) {
        indicator.threat_types.forEach(type => {
          types[type] = (types[type] || 0) + 1;
        });
      }
    });
    return types;
  }, [indicators]);

  const killChains = useMemo(() => {
    const chains = {};
    indicators.forEach(indicator => {
      if (indicator.kill_chains && indicator.kill_chains.length > 0) {
        indicator.kill_chains.forEach(chain => {
          chains[chain] = (chains[chain] || 0) + 1;
        });
      }
    });
    return chains;
  }, [indicators]);

  const threatTypeData = useMemo(() => {
    const entries = Object.keys(threatTypes).map(key => ({
      id: key,
      label: key,
      value: threatTypes[key],
    }));
    return foldExcessCategories(entries, t('providers.common.other'));
  }, [threatTypes, t]);

  const activePhases = useMemo(() => {
    const phases = new Set();
    Object.keys(killChains).forEach(chain => {
      const mappedPhase = mapKillChainToPhase(chain);
      phases.add(mappedPhase);
    });
    return phases;
  }, [killChains]);

  const paginatedIndicators = useMemo(() => {
    return indicators.slice(
      (page - 1) * rowsPerPage,
      page * rowsPerPage
    );
  }, [indicators, page, rowsPerPage]);

  const summaryPaperSx = {
    p: 2,
    backgroundColor: (t) => t.palette.mode === 'dark' ? t.palette.background.default : t.palette.grey[100],
    height: '100%',
  };

  const confidenceScore = useMemo(() => {
    if (indicators.length === 0) return 0;
    const avgConfidence = indicators.reduce((acc, ind) => {
      return acc + confidenceToScore(ind.malicious_confidence);
    }, 0) / indicators.length;
    return Math.round(avgConfidence);
  }, [indicators]);

  const actorCount = useMemo(() => indicators.reduce(
    (count, ind) => count + (ind.actors ? ind.actors.length : 0), 0
  ), [indicators]);

  const malwareCount = useMemo(() => indicators.reduce(
    (count, ind) => count + (ind.malware_families ? ind.malware_families.length : 0), 0
  ), [indicators]);

  const handlePageChange = useCallback((event, newPage) => {
    setPage(newPage);
  }, []);

  if (!result || !result.resources || result.resources.length === 0) {
    return <NoDetails message={t('providers.crowdstrike.noInfoFound')} />;
  }

  return (
    <Box sx={{ margin: 1 }}>
      {/* Summary statistics cards */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Paper sx={summaryPaperSx}>
            <Box display="flex" alignItems="center">
              <SecurityIcon fontSize="large" sx={{ mr: 1, color:
                confidenceScore < 20 ? 'success.main' :
                confidenceScore < 50 ? 'warning.main' : 'error.main'
              }} />
              <Box>
                <Typography variant="h6">{t('providers.crowdstrike.confidenceLevel')}</Typography>
                <Typography variant="h4" sx={{
                  color: confidenceScore < 20 ? 'success.main' :
                  confidenceScore < 50 ? 'warning.main' : 'error.main'
                }}>
                  {confidenceScore}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Paper sx={summaryPaperSx}>
            <Box display="flex" alignItems="center">
              <PersonIcon fontSize="large" sx={{ mr: 1, color: 'error.main' }} />
              <Box>
                <Typography variant="h6">{t('providers.crowdstrike.threatActors')}</Typography>
                <Typography variant="h4">
                  {actorCount}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, sm: 4 }}>
          <Paper sx={summaryPaperSx}>
            <Box display="flex" alignItems="center">
              <CodeIcon fontSize="large" sx={{ mr: 1, color: 'warning.main' }} />
              <Box>
                <Typography variant="h6">{t('providers.crowdstrike.malwareFamilies')}</Typography>
                <Typography variant="h4">
                  {malwareCount}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Visualization charts */}
      {(Object.keys(threatTypes).length > 0 || Object.keys(killChains).length > 0) && (
        <Card sx={{ p: 2, mb: 2, borderRadius: 1, boxShadow: 0 }}>
          <Grid container spacing={3}>
            {Object.keys(threatTypes).length > 0 && (
              <Grid size={{ xs: 12, md: 6 }}>
                <Box display="flex" alignItems="center" mb={1}>
                  <DonutLargeIcon sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h3">
                    {t('providers.crowdstrike.threatTypes')}
                  </Typography>
                </Box>
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
                      <Pie
                        data={threatTypeData}
                        dataKey="value"
                        nameKey="label"
                        innerRadius="50%"
                        outerRadius="80%"
                        paddingAngle={2}
                        cornerRadius={3}
                        stroke={theme.palette.background.paper}
                        strokeWidth={1}
                        isAnimationActive={false}
                      >
                        {threatTypeData.map((entry, index) => (
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
                </Box>
              </Grid>
            )}

            {Object.keys(killChains).length > 0 && (
              <Grid size={{ xs: 12, md: Object.keys(threatTypes).length > 0 ? 6 : 12 }}>
                <Box display="flex" alignItems="center" mb={1}>
                  <TimelineIcon sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h3">
                    {t('providers.crowdstrike.killChainPhases')}
                  </Typography>
                </Box>
                <Box sx={{ p: 2 }}>
                  <Stepper orientation="vertical">
                    {KILL_CHAIN_PHASE_IDS.map((phaseId) => {
                      const isActive = activePhases.has(phaseId);
                      return (
                        <Step key={phaseId} active={isActive} completed={isActive}>
                          <StepLabel
                            StepIconProps={{
                              sx: { color: isActive ? 'error.main' : '' }
                            }}
                          >
                            <Typography fontWeight={isActive ? 'bold' : 'normal'}>
                              {t(`providers.crowdstrike.killChainPhaseLabels.${phaseId}`)}
                            </Typography>
                          </StepLabel>
                          {isActive && (
                            <StepContent>
                              <Typography color="text.secondary">
                                {Object.entries(killChains)
                                  .filter(([chain]) => mapKillChainToPhase(chain) === phaseId)
                                  .map(([chain, count]) => t('providers.crowdstrike.observedTimes', { chain, count }))
                                  .join(', ') || t('providers.crowdstrike.detailsNotAvailable')}
                              </Typography>
                            </StepContent>
                          )}
                        </Step>
                      );
                    })}
                  </Stepper>
                </Box>
              </Grid>
            )}
          </Grid>
        </Card>
      )}

      {/* Indicators accordion */}
      <Accordion defaultExpanded sx={{ borderRadius: 1, mb: 1, "&::before": { display: "none" } }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="indicators-content"
          id="indicators-header"
        >
          <Box display="flex" alignItems="center">
            <BugReportIcon sx={{ mr: 1 }} />
            <Typography variant="h6">{t('providers.crowdstrike.indicatorsCount', { count: indicators.length })}</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {paginatedIndicators.map((indicator, index) => (
            <Paper
              key={indicator.id || index}
              sx={{
                p: 2,
                mb: 2,
                backgroundColor: (t) => t.palette.mode === 'dark' ? t.palette.background.default : t.palette.grey[100],
              }}
            >
              <Typography variant="subtitle1" fontWeight="bold">
                {indicator.indicator}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('providers.crowdstrike.type')} {indicator.type}
              </Typography>

              <Box display="flex" alignItems="center" mt={1}>
                <Typography variant="body2" mr={1}>
                  {t('providers.crowdstrike.confidence')}
                </Typography>
                <Chip
                  label={indicator.malicious_confidence || t('providers.crowdstrike.unknown')}
                  size="small"
                  color={getConfidenceLevelColor(indicator.malicious_confidence)}
                />
              </Box>

              <Box mt={1}>
                <Typography variant="body2">
                  {t('providers.crowdstrike.published')} {indicator.published_date ? new Date(indicator.published_date * 1000).toLocaleDateString() : notAvailable}
                </Typography>
                <Typography variant="body2">
                  {t('providers.crowdstrike.lastUpdated')} {indicator.last_updated ? new Date(indicator.last_updated * 1000).toLocaleDateString() : notAvailable}
                </Typography>
              </Box>

              {indicator.actors && indicator.actors.length > 0 && (
                <Box mt={2}>
                  <Typography variant="body2" fontWeight="bold">
                    {t('providers.crowdstrike.threatActorsLabel')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {indicator.actors.map((actor) => (
                      <Chip
                        key={actor}
                        label={actor}
                        size="small"
                        color="error"
                        sx={{ mr: 0.5, mb: 0.5 }}
                        icon={<PersonIcon />}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {indicator.malware_families && indicator.malware_families.length > 0 && (
                <Box mt={2}>
                  <Typography variant="body2" fontWeight="bold">
                    {t('providers.crowdstrike.malwareFamiliesLabel')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {indicator.malware_families.map((malware) => (
                      <Chip
                        key={malware}
                        label={malware}
                        size="small"
                        color="warning"
                        sx={{ mr: 0.5, mb: 0.5 }}
                        icon={<CodeIcon />}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {indicator.kill_chains && indicator.kill_chains.length > 0 && (
                <Box mt={2}>
                  <Typography variant="body2" fontWeight="bold">
                    {t('providers.crowdstrike.killChainPhasesRaw')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {indicator.kill_chains.map((phase) => (
                      <Chip
                        key={phase}
                        label={phase}
                        size="small"
                        color="primary"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {indicator.threat_types && indicator.threat_types.length > 0 && (
                <Box mt={2}>
                  <Typography variant="body2" fontWeight="bold">
                    {t('providers.crowdstrike.threatTypesLabel')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {indicator.threat_types.map((type) => (
                      <Chip
                        key={type}
                        label={type}
                        size="small"
                        color="info"
                        sx={{ mr: 0.5, mb: 0.5 }}
                        icon={<CategoryIcon />}
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </Paper>
          ))}

          {indicators.length > rowsPerPage && (
            <Box display="flex" justifyContent="center" mt={2}>
              <Pagination
                count={Math.ceil(indicators.length / rowsPerPage)}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
