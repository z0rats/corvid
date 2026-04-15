import React, { useState } from "react";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ScheduleIcon from '@mui/icons-material/Schedule';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid2';
import Typography from '@mui/material/Typography';
import InfoModal from "../../../shared/components/InfoModal";
import MetricSelect from "../../../shared/components/MetricSelect";
import { threatMetrics } from "../../constants/metricsConfig";

export default function ThreatScore({ metrics, onMetricChange }) {
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
          <ScheduleIcon fontSize="small" sx={{ mr: 1 }} />
          <Typography variant="subtitle2">Threat Metrics (optional)</Typography>
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
            The Threat metrics measure the current state of exploit techniques or
            code availability. These metrics are optional and can be used to
            customize the CVSS score based on the current threat landscape.
          </Typography>
        </Box>

        <Grid container spacing={2}>
          {threatMetrics.map((metric) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={metric.key}>
              <MetricSelect
                label={metric.label}
                value={metrics[metric.key] || "X"}
                options={metric.options}
                onChange={handleSelectChange(metric.key)}
                onInfoClick={() => handleOpenModal(metric.label, metric.info)}
              />
            </Grid>
          ))}
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
