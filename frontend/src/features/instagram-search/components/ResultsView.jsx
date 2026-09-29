import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import OpenInNewIcon from '@mui/icons-material/OpenInNewOutlined';
import VideocamIcon from '@mui/icons-material/VideocamOutlined';

function FollowItemsTable({ items }) {
  const { t } = useTranslation('instagramSearch');
  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('results.headers.username')}</TableCell>
            <TableCell>{t('results.headers.fullName')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.username} hover>
              <TableCell>
                <Link
                  href={`https://www.instagram.com/${item.username}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                >
                  @{item.username} <OpenInNewIcon fontSize="inherit" />
                </Link>
              </TableCell>
              <TableCell>{item.full_name || '-'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function PostItemsTable({ items }) {
  const { t } = useTranslation('instagramSearch');
  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>{t('results.headers.post')}</TableCell>
            <TableCell>{t('results.headers.date')}</TableCell>
            <TableCell align="right">{t('results.headers.likes')}</TableCell>
            <TableCell align="right">{t('results.headers.comments')}</TableCell>
            <TableCell>{t('results.headers.caption')}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.shortcode} hover>
              <TableCell>
                <Link
                  href={item.permalink}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                >
                  {item.shortcode} <OpenInNewIcon fontSize="inherit" />
                </Link>
                {item.is_video && <VideocamIcon fontSize="inherit" sx={{ ml: 0.5, verticalAlign: 'middle' }} />}
              </TableCell>
              <TableCell>{item.date_utc ? new Date(item.date_utc).toLocaleDateString() : '-'}</TableCell>
              <TableCell align="right">{item.likes ?? '-'}</TableCell>
              <TableCell align="right">{item.comments ?? '-'}</TableCell>
              <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.caption || '-'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default function ResultsView({ result }) {
  const { t } = useTranslation('instagramSearch');
  if (!result) return null;

  const items = result.items || [];

  return (
    <>
      <Chip
        size="small"
        label={t('results.summary', { count: result.item_count, total: result.total_count ?? '?' })}
        sx={{ mb: 1.5 }}
      />
      {result.truncated && (
        <Alert severity="info" sx={{ mb: 1.5 }}>{t('results.truncatedNotice')}</Alert>
      )}

      {items.length === 0 ? (
        <Typography color="text.secondary">{t('results.empty')}</Typography>
      ) : result.scan_type === 'posts' ? (
        <PostItemsTable items={items} />
      ) : (
        <FollowItemsTable items={items} />
      )}
    </>
  );
}
