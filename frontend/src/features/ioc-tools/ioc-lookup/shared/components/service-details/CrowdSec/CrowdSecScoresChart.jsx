import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import InfoIcon from '@mui/icons-material/Info';
import { ResponsiveBar } from '@nivo/bar';
import InfoModal from '../../../../../../../core/components/ui/InfoModal';

const SCORE_INFO_TITLE = "CTI Score Information";
const SCORE_INFO_TEXT = "The scores indicate malevolence for an IP over time (Overall, Last Day, Week, Month).\n\n- Aggressiveness: Intensity of attacks (number reported).\n- Threat Level: Seriousness of reported attack types (e.g., crawl vs. exploit).\n- Trust: Confidence in reporting actors (reputation, diversity).\n- Anomaly: Red flags from IP's static description.\n- Total: Aggregation of these components (0=low to 5=high malevolence).";

export default function CrowdSecScoresChart({ scoreData }) {
  const theme = useTheme();
  const [openModal, setOpenModal] = useState(false);

  return (
    <Card sx={{ p: 2, borderRadius: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
      <InfoModal
        open={openModal}
        onClose={() => setOpenModal(false)}
        title={SCORE_INFO_TITLE}
        text={SCORE_INFO_TEXT}
      />
      <Box display="flex" alignItems="center" mb={1}>
        <Typography variant="h6" component="h3" gutterBottom sx={{ flexGrow: 1, mb: 0 }}>
          CTI Scores Breakdown
        </Typography>
        <IconButton onClick={() => setOpenModal(true)} size="small" aria-label="Show score info">
          <InfoIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ height: "380px" }}>
        <ResponsiveBar
          data={scoreData}
          keys={["aggressiveness", "threat", "trust", "anomaly", "total"]}
          indexBy="name"
          margin={{ top: 20, right: 20, bottom: 60, left: 40 }}
          padding={0.2}
          innerPadding={2}
          groupMode="stacked"
          valueScale={{ type: 'linear', min: 0, max: 'auto' }}
          colors={{ scheme: "spectral" }}
          borderColor={{ from: "color", modifiers: [["darker", 0.6]] }}
          borderWidth={1}
          borderRadius={2}
          axisTop={null}
          axisRight={null}
          axisBottom={{ tickSize: 5, tickPadding: 5, tickRotation: 0, legend: "Period", legendPosition: "middle", legendOffset: 40 }}
          axisLeft={{ tickSize: 5, tickPadding: 5, tickRotation: 0, legend: "Score", legendPosition: "middle", legendOffset: -30 }}
          enableLabel={false}
          legends={[]}
          animate={true}
          motionStiffness={90}
          motionDamping={15}
          theme={{
            axis: {
              ticks: { text: { fontSize: 10, fill: theme.palette.text.secondary } },
              legend: { text: { fontSize: 12, fill: theme.palette.text.primary } },
            },
            tooltip: {
              container: {
                background: theme.palette.background.paper,
                color: theme.palette.text.primary,
                fontSize: "12px",
              },
            },
          }}
        />
      </Box>
    </Card>
  );
}
