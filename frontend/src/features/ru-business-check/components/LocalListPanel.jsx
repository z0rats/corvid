import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

/**
 * Shared frame for a match against a locally cached list (ФНС disqualified register, ЦБ
 * warning list, OFAC SDN): title, which copy was used, an "outdated copy" warning, the
 * panel's own body, and the manual-check link.
 */
export default function LocalListPanel({ title, caption, outdated, manualLink, children }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" gutterBottom>{title}</Typography>
      {caption && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>{caption}</Typography>
      )}
      {outdated && (
        <Alert severity="warning" sx={{ mb: 1 }}>
          Локальная копия устарела — обновление выполняется автоматически, результат может быть неполным.
        </Alert>
      )}
      {children}
      {manualLink && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Проверить вручную:{' '}
            <Link href={manualLink.href} target="_blank" rel="noopener noreferrer">{manualLink.label}</Link>
          </Typography>
        </Box>
      )}
    </Paper>
  );
}
