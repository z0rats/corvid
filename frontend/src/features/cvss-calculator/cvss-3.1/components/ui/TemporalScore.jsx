import React from "react";
import { useCvss31 } from "../../../shared/hooks/useCvss31";
import Circle from "../../../shared/components/Circle";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import TimerIcon from "@mui/icons-material/Timer";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MetricSelect from "../../../shared/components/MetricSelect";
import { getSeverityColor } from "../../../shared/utils/scoreUtils";
import { temporalMetrics } from "../../constants/metricsConfig";
import { useTranslation } from 'react-i18next';

export default function TemporalScore() {
  const theme = useTheme();
  const chart = theme.palette.chart;
  const { state, updateMetric } = useCvss31();
  const { t } = useTranslation('cvssCalculator');

  const handleSelectChange = (key) => (e) => {
    updateMetric('temporal', key, e.target.value);
  };

  const renderMetricSelect = (metrics) => {
    return metrics.map((metric) => (
      <Grid size={{ xs: 12, md: 4 }} key={metric.key}>
        <MetricSelect
          label={metric.label}
          value={state.metrics.temporal[metric.key]}
          options={metric.options}
          onChange={handleSelectChange(metric.key)}
        />
      </Grid>
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
          <TimerIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">{t('cvss31.temporal.accordionTitle')}</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
          <Box sx={{ m: 1, p: 1, flex: 1, minWidth: 0 }}>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {t('cvss31.temporal.description')}
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
              <Circle value={state.scores.temporal.temporalScore} />
            </Box>
            <Typography
              variant="h6"
              fontWeight={state.scores.temporal.temporalScore >= 9.0 ? "bold" : "normal"}
              align="center"
              gutterBottom
              sx={{ display: "block", marginBottom: 1, color: getSeverityColor(state.scores.temporal.temporalScore, chart) }}
            >
              {state.scores.temporal.temporalSeverity || t('common.severityNone')}
            </Typography>
          </Box>
        </Grid>

        <Box sx={{ p: 1, minWidth: 0 }}>
          <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
            {renderMetricSelect(temporalMetrics)}
          </Grid>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
