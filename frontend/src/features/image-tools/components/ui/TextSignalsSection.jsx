import React from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { imageUtils } from '../../utils/imageUtils';

const MAX_NAMES_SHOWN = 4;

// Names the places and languages a hint points to, capping long lists (a script or
// currency shared by a dozen countries) so one row cannot dominate the section.
function describeTargets(signal, locale, t) {
  const countries = signal.countries.map((c) => imageUtils.displayName(c, 'region', locale));
  const languages = signal.languages.map((l) => imageUtils.displayName(l, 'language', locale));
  const names = [...countries, ...languages];
  const shown = names.slice(0, MAX_NAMES_SHOWN).join(', ');
  const hidden = names.length - MAX_NAMES_SHOWN;
  return hidden > 0 ? `${shown} ${t('geolocation.textSignalsMore', { count: hidden })}` : shown;
}

export default function TextSignalsSection({ signals = [], visibleText = [] }) {
  const { t, i18n } = useTranslation('imageTools');

  if (signals.length === 0 && visibleText.length === 0) return null;

  return (
    <>
      <Typography variant="subtitle2" sx={{ mt: 2 }}>
        {t('geolocation.textSignals')}
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        {t('geolocation.textSignalsNote')}
      </Typography>

      {visibleText.length > 0 && (
        <Box
          sx={{ mb: 1.5, p: 1, borderRadius: 1, bgcolor: 'action.hover' }}
          aria-label={t('geolocation.visibleText')}
        >
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            {t('geolocation.visibleText')}
          </Typography>
          {visibleText.map((line, index) => (
            <Typography
              key={`${index}-${line}`}
              variant="body2"
              sx={{ fontFamily: 'monospace', wordBreak: 'break-word' }}
            >
              {line}
            </Typography>
          ))}
        </Box>
      )}

      {signals.map((signal) => {
        const detail = [
          t('geolocation.foundIn', { text: signal.source_text }),
          signal.note,
        ].filter(Boolean).join(' — ');
        return (
          <Box
            key={`${signal.kind}-${signal.matched}`}
            sx={{ mb: 0.75, display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap' }}
          >
            <Tooltip title={detail} arrow placement="top-start">
              <Chip
                size="small"
                variant="outlined"
                color={signal.strength === 'strong' ? 'success' : 'default'}
                label={`${t(`geolocation.signalKinds.${signal.kind}`, { defaultValue: signal.kind })}: ${signal.matched}`}
                sx={{ opacity: signal.strength === 'weak' ? 0.6 : 1 }}
              />
            </Tooltip>
            <Typography variant="body2" color="text.secondary">
              {`→ ${describeTargets(signal, i18n.language, t)}`}
            </Typography>
          </Box>
        );
      })}
    </>
  );
}
