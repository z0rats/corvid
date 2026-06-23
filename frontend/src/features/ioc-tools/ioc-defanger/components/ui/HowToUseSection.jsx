import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import GppMaybeIcon from '@mui/icons-material/GppMaybe';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';

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
        <Typography variant="body2" paragraph>
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
  return (
    <>
      <Typography variant="h6" sx={{ mb: 2, mt: 3 }}>
        How to Use
      </Typography>

      <Grid container spacing={3}>
        <ExampleCard
          icon={<HealthAndSafetyIcon sx={{ color: 'text.primary' }} />}
          title="Defanging IOCs"
          subtitle="Make IOCs safe for sharing"
          description="Defanging replaces dangerous characters in IOCs to prevent accidental execution:"
          examples={DEFANG_EXAMPLES}
        />
        <ExampleCard
          icon={<GppMaybeIcon sx={{ color: 'text.primary' }} />}
          title="Fanging IOCs"
          subtitle="Restore original IOCs for analysis"
          description="Fanging restores defanged IOCs to their original form for analysis:"
          examples={FANG_EXAMPLES}
        />
      </Grid>
    </>
  );
}
