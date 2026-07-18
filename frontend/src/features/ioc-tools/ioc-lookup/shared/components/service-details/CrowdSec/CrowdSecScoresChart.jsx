import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import InfoIcon from '@mui/icons-material/Info';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import InfoModal from '../../../../../../../core/components/ui/InfoModal';
import { getCategoricalColor } from '../../../../../../../core/utils/chartColors';

const SCORE_KEYS = ["aggressiveness", "threat", "trust", "anomaly", "total"];

export default function CrowdSecScoresChart({ scoreData }) {
  const { t } = useTranslation('iocTools');
  const theme = useTheme();
  const [openModal, setOpenModal] = useState(false);

  return (
    <Card sx={{ p: 2, borderRadius: 2, height: '100%', border: '1px solid', borderColor: 'divider' }}>
      <InfoModal
        open={openModal}
        onClose={() => setOpenModal(false)}
        title={t('providers.crowdsec.scoreInfoTitle')}
        text={t('providers.crowdsec.scoreInfoText')}
      />
      <Box display="flex" alignItems="center" mb={1}>
        <Typography variant="h6" component="h3" gutterBottom sx={{ flexGrow: 1, mb: 0 }}>
          {t('providers.crowdsec.ctiScoresBreakdown')}
        </Typography>
        <IconButton onClick={() => setOpenModal(true)} size="small" aria-label={t('providers.crowdsec.showScoreInfo')}>
          <InfoIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ height: "380px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={scoreData} margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
            <XAxis
              dataKey="name"
              label={{ value: t('providers.crowdsec.period'), position: 'insideBottom', offset: -10, fill: theme.palette.text.primary }}
              tick={{ fontSize: 10, fill: theme.palette.text.secondary }}
              axisLine={{ stroke: theme.palette.divider }}
              tickLine={{ stroke: theme.palette.divider }}
            />
            <YAxis
              label={{ value: t('providers.crowdsec.score'), angle: -90, position: 'insideLeft', fill: theme.palette.text.primary }}
              tick={{ fontSize: 10, fill: theme.palette.text.secondary }}
              axisLine={{ stroke: theme.palette.divider }}
              tickLine={{ stroke: theme.palette.divider }}
            />
            <Tooltip
              cursor={{ fill: theme.palette.action.hover }}
              contentStyle={{
                background: theme.palette.background.paper,
                color: theme.palette.text.primary,
                fontSize: 12,
                border: `1px solid ${theme.palette.divider}`,
                borderRadius: theme.shape.borderRadius,
              }}
            />
            <Legend wrapperStyle={{ color: theme.palette.text.secondary, fontSize: 12 }} />
            {SCORE_KEYS.map((key, index) => (
              <Bar key={key} dataKey={key} stackId="scores" fill={getCategoricalColor(theme, index)} isAnimationActive={false} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </Box>
    </Card>
  );
}
