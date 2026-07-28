import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

/**
 * Shared header for "history" detail views: back button + title + chips,
 * plus optional summary/error lines. The result body below it (found sites,
 * providers, results, tabs, ...) differs too much per feature to share.
 */
export default function HistoryDetailHeader({ onBack, title, chips, summary, error }) {
  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <IconButton onClick={onBack}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5" sx={{ wordBreak: 'break-word' }}>{title}</Typography>
        {chips}
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
