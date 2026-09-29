import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import FieldRow from './FieldRow';
import RawResponsePanel from './RawResponsePanel';

const RMSP_URL = 'https://rmsp.nalog.ru/';

/**
 * Facts from the ФНС МСП register (rmsp.nalog.ru). Informational only - no risk flag is
 * derived from it, and not being listed is the normal state for any large company.
 */
export default function MspPanel({ data, raw, sha256 }) {
  if (!data?.checked) return null;

  return (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" gutterBottom>Реестр МСП</Typography>
      {!data.found && (
        <Typography variant="body2" color="text.secondary">Не найдено в реестре малого и среднего предпринимательства</Typography>
      )}
      {data.found && (
        <>
          <FieldRow label="Категория" value={data.category} />
          <FieldRow label="Сведения актуальны" value={data.is_active ? 'Да' : 'Нет — исключён из реестра'} />
          <FieldRow label="В реестре с" value={data.registered_at} />
          <FieldRow label="Исключён из реестра" value={data.removed_at} />
          <FieldRow label="Признак" value={data.is_new ? 'Вновь созданный' : null} />
        </>
      )}
      <Box sx={{ mt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          Проверить вручную: <Link href={RMSP_URL} target="_blank" rel="noopener noreferrer">rmsp.nalog.ru</Link>
        </Typography>
      </Box>
      <RawResponsePanel label="Сырые данные реестра МСП" raw={raw} sha256={sha256} />
    </Paper>
  );
}
