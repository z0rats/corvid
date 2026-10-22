import { useTranslation } from 'react-i18next';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';
import ImageIcon from '@mui/icons-material/ImageOutlined';
import ShortcutIcon from '@mui/icons-material/Shortcut';

import { formatCompact } from '../utils/telegramFormat';

export default function PostsTable({ title, posts }) {
  const { t } = useTranslation('telegramSearch');
  if (!posts?.length) return null;

  return (
    <Paper sx={{ mb: 2 }}>
      <Typography variant="subtitle1" component="h2" sx={{ px: 2, pt: 2 }}>{title}</Typography>
      <TableContainer sx={{ maxHeight: 480 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>{t('posts.headers.post')}</TableCell>
              <TableCell>{t('posts.headers.date')}</TableCell>
              <TableCell align="right">{t('posts.headers.views')}</TableCell>
              <TableCell>{t('posts.headers.text')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {posts.map((post) => (
              <TableRow key={post.id} hover>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>
                  <Link href={post.url} target="_blank" rel="noopener noreferrer">#{post.id}</Link>
                  {post.has_media && <ImageIcon fontSize="inherit" sx={{ ml: 0.5, verticalAlign: 'middle' }} titleAccess={t('posts.media')} />}
                </TableCell>
                <TableCell sx={{ whiteSpace: 'nowrap' }}>{post.date ? new Date(post.date).toLocaleString() : '-'}</TableCell>
                <TableCell align="right">{formatCompact(post.views) ?? '-'}</TableCell>
                <TableCell sx={{ maxWidth: 480 }}>
                  {post.forwarded_from && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ShortcutIcon fontSize="inherit" />
                      {t('posts.forwardedFrom', {
                        name: post.forwarded_from.name || post.forwarded_from.username || t('network.hiddenSender'),
                      })}
                    </Typography>
                  )}
                  <Typography
                    variant="body2"
                    sx={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}
                  >
                    {post.text || '-'}
                  </Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
