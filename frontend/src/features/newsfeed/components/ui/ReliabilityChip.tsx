import { useTranslation } from 'react-i18next';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';

import { RELIABILITY_COLORS, type Reliability } from '../../constants/reliability';

interface ReliabilityChipProps {
  grade?: Reliability | null;
}

/** Source-reliability badge for an article's feed; renders nothing for an unrated feed. */
export default function ReliabilityChip({ grade }: ReliabilityChipProps) {
  const { t } = useTranslation('newsfeed');
  if (!grade) return null;

  const title = t('reliability.sourceTooltip', {
    grade,
    description: t(`reliability.grades.${grade}`),
  });
  return (
    <Tooltip title={title} arrow>
      <Chip size="small" variant="outlined" color={RELIABILITY_COLORS[grade]} label={grade} aria-label={title} />
    </Tooltip>
  );
}
