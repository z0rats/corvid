import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import GppMaybeIcon from '@mui/icons-material/GppMaybe';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import { useTranslation } from 'react-i18next';

const DEFANG_EXAMPLES = [
  'https://example.com → hxxps[://]example[.]com',
  '192.168.1.1 → 192[.]168[.]1[.]1',
  'user@domain.com → user[@]domain[.]com',
];

const FANG_EXAMPLES = [
  'hxxps[://]example[.]com → https://example.com',
  '192[.]168[.]1[.]1 → 192.168.1.1',
  'user[@]domain[.]com → user@domain.com',
];

const ExampleCard = ({ icon, title, subtitle, description, examples }) => (
  <Grid size={{ xs: 12, md: 6 }}>
    <Card variant="outlined">
      <CardHeader avatar={icon} title={title} subheader={subtitle} />
      <CardContent>
        <Typography variant="body2" sx={{ mb: 2 }}>
          {description}
        </Typography>
        <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem', p: 1, borderRadius: 1 }}>
          {examples.map((example, index) => (
            <span key={index}>
              {example}
              {index < examples.length - 1 && <br />}
            </span>
          ))}
        </Box>
      </CardContent>
    </Card>
  </Grid>
);

export default function HowToUseSection() {
  const { t } = useTranslation('iocTools');

  return (
    <>
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>
        {t('iocDefanger.howToUse.title')}
      </Typography>

      <Grid container spacing={3}>
        <ExampleCard
          icon={<HealthAndSafetyIcon sx={{ color: 'text.primary' }} />}
          title={t('iocDefanger.howToUse.defang.title')}
          subtitle={t('iocDefanger.howToUse.defang.subtitle')}
          description={t('iocDefanger.howToUse.defang.description')}
          examples={DEFANG_EXAMPLES}
        />
        <ExampleCard
          icon={<GppMaybeIcon sx={{ color: 'text.primary' }} />}
          title={t('iocDefanger.howToUse.fang.title')}
          subtitle={t('iocDefanger.howToUse.fang.subtitle')}
          description={t('iocDefanger.howToUse.fang.description')}
          examples={FANG_EXAMPLES}
        />
      </Grid>
    </>
  );
}
