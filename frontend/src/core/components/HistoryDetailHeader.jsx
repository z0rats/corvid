import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DownloadIcon from '@mui/icons-material/DownloadOutlined';
import { downloadCsv, downloadJson } from '../utils/exportData';
import AddToInvestigationButton from './AddToInvestigationButton';

/**
 * Shared header for "history" detail views: back button + title + chips,
 * plus optional summary/error lines. The result body below it (found sites,
 * providers, results, tabs, ...) differs too much per feature to share.
 *
 * `exportName` turns on client-side export: JSON of the whole `exportData` record, plus CSV of
 * `csvRows` (the feature's main findings table) when it has any.
 *
 * `runRef` (`{ feature, id }`, the backend's activity-feed feature name) adds "Add to
 * investigation" - only for features with a backend RunSource (app/utils/run_source_registry.py).
 */
export default function HistoryDetailHeader({
  onBack, title, chips, summary, error, exportName, exportData, csvRows, runRef,
}) {
  const { t } = useTranslation();
  const canExport = Boolean(exportName && exportData);
  const canInvestigate = runRef?.id != null;

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2, flexWrap: 'wrap' }}>
        <IconButton onClick={onBack} aria-label={t('actions.back')}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" sx={{ wordBreak: 'break-word' }}>{title}</Typography>
        {chips}
        {(canExport || canInvestigate) && (
          <Box sx={{ display: 'flex', gap: 1, ml: 'auto', flexWrap: 'wrap' }}>
            {canInvestigate && <AddToInvestigationButton feature={runRef.feature} runId={runRef.id} />}
            {canExport && (
              <Button size="small" variant="outlined" startIcon={<DownloadIcon />} onClick={() => downloadJson(exportData, exportName)}>
                JSON
              </Button>
            )}
            {canExport && csvRows?.length > 0 && (
              <Button size="small" variant="outlined" startIcon={<DownloadIcon />} onClick={() => downloadCsv(csvRows, exportName)}>
                CSV
              </Button>
            )}
          </Box>
        )}
      </Box>

      {summary && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: error ? 1 : 2 }}>
          {summary}
        </Typography>
      )}

      {error && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
    </>
  );
}
