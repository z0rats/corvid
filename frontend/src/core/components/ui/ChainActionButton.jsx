import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { buildPrefillUrl } from '../../utils/crossFeatureNav';

/**
 * "Send this result to feature X" action - navigates to another feature with
 * `value` pre-filled (see usePrefillFromQuery on the receiving side).
 */
export default function ChainActionButton({ to, value, labelKey, ns, size = 'small', ...buttonProps }) {
  const { t } = useTranslation(ns);
  const navigate = useNavigate();

  const handleClick = (event) => {
    event.stopPropagation();
    navigate(buildPrefillUrl(to, value));
  };

  return (
    <Button
      size={size}
      variant="text"
      startIcon={<ArrowForwardIcon fontSize="small" />}
      onClick={handleClick}
      {...buttonProps}
    >
      {t(labelKey)}
    </Button>
  );
}
