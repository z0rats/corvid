import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

function EmailChip({ email, isNoreply }) {
  const { t } = useTranslation('gitRecon');
  return (
    <Stack direction="row" spacing={0.5} alignItems="center" component="span">
      <Typography variant="body2" component="span">{email}</Typography>
      {isNoreply && <Chip size="small" variant="outlined" color="warning" label={t('badges.noreply')} />}
    </Stack>
  );
}

function PersonRow({ person }) {
  const { t } = useTranslation('gitRecon');
  return (
    <TableRow hover>
      <TableCell>
        <Typography variant="body2" fontWeight={600}>{person.name || '?'}</Typography>
        {person.aliases.length > 0 && (
          <Stack spacing={0.25} sx={{ mt: 0.5 }}>
            {person.aliases.map((alias, i) => (
              <Typography key={i} variant="caption" color="text.secondary">
                {t('results.alsoKnownAs')} {alias.name} &lt;{alias.email}&gt;
                {alias.is_noreply && ` (${t('badges.noreply')})`}
              </Typography>
            ))}
          </Stack>
        )}
      </TableCell>
      <TableCell><EmailChip email={person.email} isNoreply={person.is_noreply} /></TableCell>
      <TableCell align="right">{person.as_author}</TableCell>
      <TableCell align="right">{person.as_committer}</TableCell>
      <TableCell>
        {person.github_login ? (
          <Link href={`https://github.com/${person.github_login}`} target="_blank" rel="noopener noreferrer">
            @{person.github_login}
          </Link>
        ) : (
          <Typography variant="body2" color="text.secondary">-</Typography>
        )}
      </TableCell>
    </TableRow>
  );
}

function PersonsTable({ persons }) {
  const { t } = useTranslation('gitRecon');
  if (persons.length === 0) return null;
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>{t('results.identities', { count: persons.length })}</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('results.headers.name')}</TableCell>
              <TableCell>{t('results.headers.email')}</TableCell>
              <TableCell align="right">{t('results.headers.asAuthor')}</TableCell>
              <TableCell align="right">{t('results.headers.asCommitter')}</TableCell>
              <TableCell>{t('results.headers.githubLogin')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {persons.map((p) => <PersonRow key={p.key} person={p} />)}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function CorrelationsSection({ sharedNameGroups, samePersonClusters }) {
  const { t } = useTranslation('gitRecon');
  if (sharedNameGroups.length === 0 && samePersonClusters.length === 0) return null;
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>{t('results.correlation')}</Typography>
      <Stack spacing={1}>
        {sharedNameGroups.map((group, i) => (
          <Alert key={`name-${i}`} severity="warning" variant="outlined">
            <Typography variant="body2" fontWeight={600}>{group.name}</Typography>
            <Typography variant="caption">{t('results.sharedEmails', { count: group.emails.length })}: {group.emails.join(', ')}</Typography>
          </Alert>
        ))}
        {samePersonClusters.map((cluster, i) => (
          <Alert key={`cluster-${i}`} severity="warning" variant="outlined">
            <Typography variant="body2" fontWeight={600}>{t('results.samePerson')}: {cluster.names.join(' ≡ ')}</Typography>
            <Typography variant="caption">{cluster.emails.join(', ')}</Typography>
          </Alert>
        ))}
      </Stack>
    </Box>
  );
}

function GpgKeysTable({ gpgKeys }) {
  const { t } = useTranslation('gitRecon');
  if (gpgKeys.length === 0) return null;
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>{t('results.pgpKeys', { count: gpgKeys.length })}</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('results.headers.email')}</TableCell>
              <TableCell>{t('results.headers.status')}</TableCell>
              <TableCell>{t('results.headers.keyId')}</TableCell>
              <TableCell>{t('results.headers.source')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {gpgKeys.map((k, i) => (
              <TableRow key={i} hover>
                <TableCell><EmailChip email={k.email} isNoreply={false} /></TableCell>
                <TableCell>
                  <Chip size="small" color={k.verified ? 'success' : 'default'} label={t(k.verified ? 'badges.verified' : 'badges.unverified')} />
                </TableCell>
                <TableCell><Typography variant="body2" fontFamily="monospace">{k.key_id || '?'}</Typography></TableCell>
                <TableCell>{k.source}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function CommitHitsTable({ commitHits }) {
  const { t } = useTranslation('gitRecon');
  if (commitHits.length === 0) return null;
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="subtitle1" sx={{ mb: 1 }}>{t('results.commitSearch', { count: commitHits.length })}</Typography>
      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>{t('results.headers.name')}</TableCell>
              <TableCell>{t('results.headers.email')}</TableCell>
              <TableCell>{t('results.headers.role')}</TableCell>
              <TableCell>{t('results.headers.repo')}</TableCell>
              <TableCell>{t('results.headers.date')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {commitHits.map((c, i) => (
              <TableRow key={i} hover>
                <TableCell>{c.name || '?'}</TableCell>
                <TableCell><EmailChip email={c.email} isNoreply={false} /></TableCell>
                <TableCell><Chip size="small" variant="outlined" label={c.role} /></TableCell>
                <TableCell>
                  {c.repo ? (
                    <Link href={`https://github.com/${c.repo}`} target="_blank" rel="noopener noreferrer">{c.repo}</Link>
                  ) : '-'}
                </TableCell>
                <TableCell>{c.date ? new Date(c.date).toLocaleDateString() : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default function ResultsView({ result }) {
  const { t } = useTranslation('gitRecon');
  if (!result) return null;

  const { stats, repos, persons, shared_name_groups: sharedNameGroups, same_person_clusters: samePersonClusters, gpg_keys: gpgKeys, commit_hits: commitHits, notes } = result;

  const hasClonedData = (repos && repos.length > 0) || (persons && persons.length > 0);
  const hasSearchData = (gpgKeys && gpgKeys.length > 0) || (commitHits && commitHits.length > 0);

  if (!hasClonedData && !hasSearchData && (!notes || notes.length === 0)) {
    return <Typography color="text.secondary">{t('results.empty')}</Typography>;
  }

  return (
    <Box>
      {notes && notes.length > 0 && (
        <Stack spacing={1} sx={{ mb: 2 }}>
          {notes.map((note, i) => <Alert key={i} severity="info">{note}</Alert>)}
        </Stack>
      )}

      {hasClonedData && (
        <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
          <Chip label={t('results.stats.repos', { count: stats.repos })} />
          <Chip label={t('results.stats.commits', { count: stats.commits })} />
          <Chip label={t('results.stats.persons', { count: stats.persons })} />
        </Stack>
      )}

      <PersonsTable persons={persons || []} />
      <CorrelationsSection sharedNameGroups={sharedNameGroups || []} samePersonClusters={samePersonClusters || []} />
      <GpgKeysTable gpgKeys={gpgKeys || []} />
      <CommitHitsTable commitHits={commitHits || []} />
    </Box>
  );
}
