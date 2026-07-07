import React from "react";
import Circle from "../../../shared/components/Circle";
import { useCvss31 } from "../../../shared/hooks/useCvss31";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import ForestIcon from "@mui/icons-material/Forest";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MetricSelect from "../../../shared/components/MetricSelect";
import { getSeverityColor } from "../../../shared/utils/scoreUtils";
import { environmentalExploitabilityMetrics, environmentalImpactMetrics, impactSubscoreModifiers } from "../../constants/metricsConfig";
import { useTranslation } from 'react-i18next';

export default function EnvironmentalScore() {
  const theme = useTheme();
  const chart = theme.palette.chart;
  const { state, updateMetric } = useCvss31();
  const { t } = useTranslation('cvssCalculator');

  const handleSelectChange = (key) => (e) => {
    const value = e.target.value === "X" ? null : e.target.value;
    updateMetric("environmental", key, value);
  };

  const renderMetricSelect = (metrics) => {
    return metrics.map((metric) => (
      <MetricSelect
        key={metric.key}
        label={metric.label}
        value={state.metrics.environmental[metric.key] || "X"}
        options={metric.options}
        onChange={handleSelectChange(metric.key)}
      />
    ));
  };

  return (
    <Accordion 
      sx={{ 
        border: 'none', 
        boxShadow: 'none',
        mt: 1
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          px: 1,
          py: 0.5,
          minHeight: '40px',
          '& .MuiAccordionSummary-content': {
            margin: 0,
          },
        }}
      >
        <Box display="flex" alignItems="center">
          <ForestIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">{t('cvss31.environmental.accordionTitle')}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
          <Box sx={{ m: 1, p: 1, flex: 1, minWidth: 0 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {t('cvss31.environmental.description')}
            </Typography>
          </Box>
          
          <Box sx={{ 
            display: "flex", 
            flexDirection: "column", 
            alignItems: "center", 
            justifyContent: "center",
            m: 1
          }}>
            <Box sx={{
              width: 120,
              height: 120,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: theme.palette.background.cvssCircle,
              borderRadius: "50%",
            }}>
              <Circle value={state.scores.environmental.environmentalScore} />
            </Box>
            <Typography
              variant="h6"
              fontWeight={state.scores.environmental.environmentalScore >= 9.0 ? "bold" : "normal"}
              align="center"
              gutterBottom
              sx={{ display: "block", marginBottom: 1, color: getSeverityColor(state.scores.environmental.environmentalScore, chart) }}
            >
              {state.scores.environmental.environmentalSeverity}
            </Typography>
          </Box>
        </Grid>

        <Box sx={{ p: 1, minWidth: 0 }}>
          <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" align="center" gutterBottom>
                {t('cvss31.environmental.exploitabilityMetrics')}
              </Typography>
              {renderMetricSelect(environmentalExploitabilityMetrics)}
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" align="center" gutterBottom>
                {t('cvss31.environmental.impactMetrics')}
              </Typography>
              {renderMetricSelect(environmentalImpactMetrics)}
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" align="center" gutterBottom>
                {t('cvss31.environmental.impactSubscoreModifiers')}
              </Typography>
              {renderMetricSelect(impactSubscoreModifiers)}
            </Grid>
          </Grid>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
