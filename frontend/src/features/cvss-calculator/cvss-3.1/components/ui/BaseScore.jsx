import React, { useState } from "react";
import { useCvss31 } from "../../../shared/hooks/useCvss31";
import Circle from "../../../shared/components/Circle";
import BarChartIcon from '@mui/icons-material/BarChart';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import InfoModal from "../../../shared/components/InfoModal";
import MetricSelect from "../../../shared/components/MetricSelect";
import { getSeverityColor } from "../../../shared/utils/scoreUtils";
import { exploitabilityMetrics, impactMetrics } from "../../constants/metricsConfig";

export default function BaseScore() {
  const theme = useTheme();
  const chart = theme.palette.chart;
  const { state, updateMetric } = useCvss31();
  const [openModal, setOpenModal] = useState(false);
  const [modalContent, setModalContent] = useState({ title: "", text: "" });

  const handleOpenModal = (title, text) => {
    setModalContent({ title, text });
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
  };

  const handleSelectChange = (key) => (e) => {
    updateMetric('base', key, e.target.value);
  };

  const renderCard = (title, metrics) => (
    <Grid size={6}>
      <Typography variant="h6" align="center">
        {title}
      </Typography>
      {metrics.map((metric) => (
        <MetricSelect
          key={metric.key}
          label={metric.label}
          value={state.metrics.base[metric.key]}
          options={metric.options}
          onChange={handleSelectChange(metric.key)}
          onInfoClick={() => handleOpenModal(metric.label, metric.info)}
        />
      ))}
    </Grid>
  );

  return (
    <Accordion 
      defaultExpanded
      sx={{ 
        border: 'none', 
        boxShadow: 'none'
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
          <BarChartIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Base Score Metrics (required)</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Grid container spacing={2} sx={{ alignItems: "stretch" }}>
          <Box
            sx={{
              m: 1,
              p: 1,
              flex: 1,
              minWidth: 0,
            }}
          >
            <Typography variant="body1">
              The Base metric group represents the intrinsic characteristics of a
              vulnerability that are constant over time and across user
              environments. It is composed of two sets of metrics: the
              Exploitability metrics and the Impact metrics. The Exploitability
              metrics reflect the ease and technical means by which the
              vulnerability can be exploited. That is, they represent
              characteristics of the thing that is vulnerable, which we refer to
              formally as the vulnerable component. On the other hand, the Impact
              metrics reflect the direct consequence of a successful exploit, and
              represent the consequence to the thing that suffers the impact,
              which we refer to formally as the impacted component.
            </Typography>
          </Box>
          <Box
            sx={{
              mb: 1,
              mt: 1,
              p: 1,
              minWidth: 0,
            }}
          >
            <Box
              sx={{
                width: 120,
                height: 120,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: theme.palette.background.cvssCircle,
                borderRadius: "50%",
                mx: "auto",
              }}
            >
              <Circle value={state.scores.base.baseScore} />
            </Box>
            <Typography
              variant="h6"
              fontWeight={state.scores.base.baseScore >= 9.0 ? "bold" : "normal"}
              sx={{ display: "block", marginBottom: 1, color: getSeverityColor(state.scores.base.baseScore, chart) }}
              align="center"
              gutterBottom
            >
              {state.scores.base.baseSeverity || "None"}
            </Typography>
          </Box>
        </Grid>

        <Box
          sx={{
            minWidth: 0,
          }}
        >
          <Grid container spacing={2}>
            {renderCard(
              "Exploitability Metrics",
              exploitabilityMetrics
            )}
            {renderCard(
              "Impact Metrics",
              impactMetrics
            )}
            <Box sx={{ mx: "auto", width: "40%" }}>
              <MetricSelect
                label="Scope (S)"
                value={state.metrics.base.scope}
                options={[
                  { value: "U", label: "Unchanged" },
                  { value: "C", label: "Changed" },
                ]}
                onChange={handleSelectChange("scope")}
                onInfoClick={() =>
                  handleOpenModal(
                    "Scope (S)",
                    "The Scope metric captures whether a vulnerability in one vulnerable component impacts resources in components beyond its security scope. The Base Score is greatest when a scope change occurs."
                  )
                }
              />
            </Box>
          </Grid>
        </Box>
      </AccordionDetails>
      {openModal && (
        <InfoModal
          open={openModal}
          onClose={handleCloseModal}
          title={modalContent.title}
          text={modalContent.text}
        />
      )}
    </Accordion>
  );
}
