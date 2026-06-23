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

export default function EnvironmentalScore() {
  const theme = useTheme();
  const chart = theme.palette.chart;
  const { state, updateMetric } = useCvss31();

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
          <Typography variant="subtitle2">Environmental Score Metrics</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
          <Box sx={{ m: 1, p: 1, flex: 1, minWidth: 0 }}>
            <Typography variant="body1" paragraph>
              These metrics enable the analyst to customize the CVSS score
              depending on the importance of the affected IT asset to a user's
              organization, measured in terms of complementary/alternative
              security controls in place, Confidentiality, Integrity, and
              Availability. The metrics are the modified equivalent of base
              metrics and are assigned metrics value based on the component
              placement in organization infrastructure.
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
                Exploitability Metrics
              </Typography>
              {renderMetricSelect(environmentalExploitabilityMetrics)}
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" align="center" gutterBottom>
                Impact Metrics
              </Typography>
              {renderMetricSelect(environmentalImpactMetrics)}
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="h6" align="center" gutterBottom>
                Impact Subscore Modifiers
              </Typography>
              {renderMetricSelect(impactSubscoreModifiers)}
            </Grid>
          </Grid>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
