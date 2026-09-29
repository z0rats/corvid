import { useTranslation } from 'react-i18next';
import Avatar from '@mui/material/Avatar';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

import { formatEpoch, formatLocation } from '../utils/steamFormat';

export default function CloseFriendsTable({ closeFriends }) {
  const { t } = useTranslation('steamRecon');

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Typography variant="h6" component="h2">
        {t('closeFriends.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('closeFriends.subtitle')}
      </Typography>

      {closeFriends.length === 0 ? (
        <Typography color="text.secondary">{t('closeFriends.empty')}</Typography>
      ) : (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('closeFriends.headers.friend')}</TableCell>
                <TableCell align="right">{t('closeFriends.headers.mutual')}</TableCell>
                <TableCell>{t('closeFriends.headers.friendSince')}</TableCell>
                <TableCell>{t('closeFriends.headers.location')}</TableCell>
                <TableCell>{t('closeFriends.headers.bans')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {closeFriends.map((friend) => (
                <TableRow key={friend.steamid64}>
                  <TableCell>
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                      <Avatar src={friend.avatar_url || undefined} sx={{ width: 28, height: 28 }} />
                      <Link
                        href={`https://steamcommunity.com/profiles/${friend.steamid64}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        underline="hover"
                      >
                        {friend.persona_name || friend.steamid64}
                      </Link>
                    </Stack>
                  </TableCell>
                  <TableCell align="right">{friend.mutual_count}</TableCell>
                  <TableCell>{formatEpoch(friend.friend_since) || '-'}</TableCell>
                  <TableCell>{formatLocation(friend.location) || '-'}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5}>
                      {friend.vac_banned && (
                        <Chip size="small" color="error" label={t('closeFriends.vacBan')} />
                      )}
                      {friend.game_banned && (
                        <Chip size="small" color="error" label={t('closeFriends.gameBan')} />
                      )}
                      {friend.friends_private && (
                        <Chip size="small" variant="outlined" label={t('closeFriends.friendsPrivate')} />
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
}
