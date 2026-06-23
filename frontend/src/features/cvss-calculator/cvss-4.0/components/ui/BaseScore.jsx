import React, { useState } from "react";
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
import { exploitabilityMetrics, vulnerableSystemImpactMetrics, subsequentSystemImpactMetrics } from "../../constants/metricsConfig";

export default function BaseScore({ metrics, onMetricChange, scores }) {
  const theme = useTheme();
  const chart = theme.palette.chart;
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
    onMetricChange(key, e.target.value);
  };

  const renderCard = (title, metricsList) => (
    <Grid size={6}>
      <Typography variant="h6" align="center">
        {title}
      </Typography>
      {metricsList.map((metric) => (
        <MetricSelect
          key={metric.key}
          label={metric.label}
          value={metrics[metric.key] || ""}
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
              environments. It is composed of the Exploitability metrics and the Impact
              metrics. The Exploitability metrics reflect the ease and technical means
              by which the vulnerability can be exploited. The Impact metrics reflect
              the direct consequence of a successful exploit.
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
              <Circle value={scores?.base_score || 0} />
            </Box>
            <Typography
              variant="h6"
              fontWeight={scores?.base_score >= 9.0 ? "bold" : "normal"}
              sx={{ display: "block", marginBottom: 1, color: getSeverityColor(scores?.base_score || 0, chart) }}
              align="center"
              gutterBottom
            >
              {scores?.base_severity || "None"}
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
            "Vulnerable System Impact",
            vulnerableSystemImpactMetrics
          )}
          {renderCard(
            "Subsequent System Impact", 
            subsequentSystemImpactMetrics
          )}
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
