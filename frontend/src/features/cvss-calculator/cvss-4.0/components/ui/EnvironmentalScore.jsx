import React, { useState } from "react";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PublicIcon from '@mui/icons-material/Public';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid2';
import Typography from '@mui/material/Typography';
import InfoModal from "../../../shared/components/InfoModal";
import MetricSelect from "../../../shared/components/MetricSelect";
import { modifiedExploitabilityMetrics, modifiedVulnerableSystemImpactMetrics, modifiedSubsequentSystemImpactMetrics } from "../../constants/metricsConfig";

export default function EnvironmentalScore({ metrics, onMetricChange }) {
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

  return (
    <Accordion 
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
          <PublicIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Environmental (Modified Base Metrics) (optional)</Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1, py: 1 }}>
        <Box
          elevation={0}
          sx={{
            m: 1,
            p: 1,
            minWidth: 0,
          }}
        >
          <Typography variant="body1">
            The Environmental metric group enables the analyst to customize the CVSS 
            score depending on the importance of the affected IT asset to a user's 
            organization, measured in terms of Confidentiality, Integrity, and 
            Availability. These metrics modify the base metrics to reflect the 
            characteristics of the user's environment.
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid size={6}>
            <Typography variant="h6" align="center">
              Modified Exploitability Metrics
            </Typography>
            {modifiedExploitabilityMetrics.map((metric) => (
              <MetricSelect
                key={metric.key}
                label={metric.label}
                value={metrics[metric.key] || "X"}
                options={metric.options}
                onChange={handleSelectChange(metric.key)}
                onInfoClick={() => handleOpenModal(metric.label, metric.info)}
              />
            ))}
          </Grid>
          <Grid size={6}>
            <Typography variant="h6" align="center">
              Modified Impact Metrics
            </Typography>
            {modifiedVulnerableSystemImpactMetrics.map((metric) => (
              <MetricSelect
                key={metric.key}
                label={metric.label}
                value={metrics[metric.key] || "X"}
                options={metric.options}
                onChange={handleSelectChange(metric.key)}
                onInfoClick={() => handleOpenModal(metric.label, metric.info)}
              />
            ))}
            {modifiedSubsequentSystemImpactMetrics.map((metric) => (
              <MetricSelect
                key={metric.key}
                label={metric.label}
                value={metrics[metric.key] || "X"}
                options={metric.options}
                onChange={handleSelectChange(metric.key)}
                onInfoClick={() => handleOpenModal(metric.label, metric.info)}
              />
            ))}
          </Grid>
        </Grid>
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
