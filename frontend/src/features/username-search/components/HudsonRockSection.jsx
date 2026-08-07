import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import HudsonRockStatusChip from './HudsonRockStatusChip';

export default function HudsonRockSection({ result }) {
  const { t } = useTranslation('usernameSearch');

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>{t('form.sourceHudsonRock')}</Typography>
      <HudsonRockStatusChip result={result} />
    </Box>
  );
}
