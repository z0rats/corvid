import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';
import EditIcon from '@mui/icons-material/Edit';
import InfoIcon from '@mui/icons-material/Info';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';

import { SYSTEM_CATEGORY_IDS } from '../../constants/templateConstants';

import ExecutionResult from './ExecutionResult';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2.5),
  marginBottom: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 1.5,
  backgroundColor: theme.palette.background.paper,
}));

export default function TemplateDetailPanel({
  template,
  payload,
  onPayloadChange,
  executing,
  result,
  onExecute,
  onCopyResult,
  onShowExample,
  onEdit,
  onToggleFavorite,
  search,
  onClearSearch,
}) {
  const { t } = useTranslation('llmTemplates');
  const isPayloadValid = useMemo(() => {
    if (!template) return false;
    const fields = Array.isArray(template.payload_fields) ? template.payload_fields : [];
    return fields.every(field =>
      !field.required || (payload[field.name] && payload[field.name].trim())
    );
  }, [template, payload]);

  if (!template) {
    return (
      <StyledPaper elevation={0} sx={{ textAlign: 'center', py: 6 }}>
        <Typography variant="h6" color="text.secondary">
          {t('detailPanel.selectPrompt')}
        </Typography>
        {search && (
          <Button variant="text" size="small" onClick={onClearSearch} sx={{ mt: 1 }}>
            {t('detailPanel.clearSearch')}
          </Button>
        )}
      </StyledPaper>
    );
  }

  return (
    <Box>
      <StyledPaper elevation={0}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6" fontWeight={600}>{template.title}</Typography>
          <Stack direction="row" spacing={1}>
            {onToggleFavorite && (
              <Tooltip title={template.category_id === SYSTEM_CATEGORY_IDS.FAVORITES ? t('detailPanel.removeFavorite') : t('detailPanel.addFavorite')}>
                <IconButton size="small" onClick={() => onToggleFavorite(template)} aria-label={t('detailPanel.toggleFavoriteAria')}>
                  {template.category_id === SYSTEM_CATEGORY_IDS.FAVORITES
                    ? <StarIcon fontSize="small" sx={{ color: 'warning.main' }} />
                    : <StarBorderIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title={t('detailPanel.viewExampleTooltip')}>
              <IconButton size="small" onClick={() => onShowExample(template)} aria-label={t('detailPanel.viewExampleAria')}>
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={t('detailPanel.editTemplateTooltip')}>
              <IconButton size="small" onClick={() => onEdit(template)} aria-label={t('detailPanel.editTemplateAria')}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {template.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
            {template.description}
          </Typography>
        )}

        <Divider sx={{ my: 2 }} />

        <Stack spacing={2} mt={1}>
          {Array.isArray(template.payload_fields) && template.payload_fields.length > 0 ? (
            template.payload_fields.map(field => (
              <TextField
                key={field.name}
                label={field.name}
                value={payload[field.name] || ''}
                onChange={e => onPayloadChange(field.name, e.target.value)}
                required={field.required}
                multiline
                minRows={6}
                helperText={field.description}
                error={field.required && !payload[field.name]?.trim()}
                size="small"
                variant="outlined"
                slotProps={{
                  input: {
                    sx: {
                      borderRadius: 1.5,
                      fontSize: '0.9rem',
                      '& textarea': { resize: 'vertical' },
                    },
                  },
                }}
                fullWidth
              />
            ))
          ) : (
            <TextField
              label={t('detailPanel.inputLabel')}
              value={payload.input || ''}
              onChange={e => onPayloadChange('input', e.target.value)}
              multiline
              minRows={6}
              size="small"
              variant="outlined"
              slotProps={{
                input: {
                  sx: { '& textarea': { resize: 'vertical' } },
                },
              }}
              fullWidth
            />
          )}
        </Stack>

        <Box display="flex" justifyContent="flex-end" mt={3}>
          <Button
            variant="contained"
            startIcon={executing ? <CircularProgress size={18} color="inherit" /> : <PlayArrowIcon />}
            onClick={onExecute}
            disabled={!isPayloadValid || executing}
            sx={{ borderRadius: 1.5, px: 3 }}
          >
            {executing ? t('detailPanel.executingButton') : t('detailPanel.executeButton')}
          </Button>
        </Box>
      </StyledPaper>

      <ExecutionResult result={result} onCopy={onCopyResult} />
    </Box>
  );
}
