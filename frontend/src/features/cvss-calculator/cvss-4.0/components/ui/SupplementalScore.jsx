import React, { useState } from "react";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExtensionIcon from '@mui/icons-material/Extension';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import InfoModal from "../../../shared/components/InfoModal";
import MetricSelect from "../../../shared/components/MetricSelect";
import { supplementalMetrics } from "../../constants/metricsConfig";

export default function SupplementalScore({ metrics, onMetricChange }) {
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
          <ExtensionIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Supplemental Metrics (optional)</Typography>
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
            The Supplemental metric group is intended to be used by organizations to 
            customize the CVSS score based on additional organization-specific or 
            use-case-specific considerations. These metrics do not affect the base score 
            but provide additional context for vulnerability assessment.
          </Typography>
        </Box>

        <Grid container spacing={2}>
          <Grid size={6}>
            <Typography variant="h6" align="center">
              Supplemental Metrics (Part 1)
            </Typography>
            {supplementalMetrics.slice(0, 3).map((metric) => (
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
              Supplemental Metrics (Part 2)
            </Typography>
            {supplementalMetrics.slice(3).map((metric) => (
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
