import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';

import FieldRow from './FieldRow';
import LocalListPanel from './LocalListPanel';

const FNS_DATASET = {
  href: 'https://data.nalog.ru/opendata/7707329152-registerdisqualified',
  label: 'открытые данные ФНС',
};

function RecordBlock({ record }) {
  return (
    <Box sx={{ mb: 1 }}>
      <FieldRow label="ФИО" value={record.full_name} />
      <FieldRow label="Номер записи" value={record.record_number} />
      <FieldRow label="Организация, должность" value={[record.org_name, record.position].filter(Boolean).join(', ')} />
      <FieldRow label="Срок" value={`${record.start_date} — ${record.end_date}${record.active ? ' (действует)' : ' (истёк)'}`} />
      <FieldRow label="Организация совпала по ИНН" value={record.same_company ? 'Да' : 'Нет'} />
      <Divider sx={{ my: 1 }} />
    </Box>
  );
}

/**
 * Match against the local copy of the ФНС open-data disqualified-persons register. Unlike the
 * online name-only search, its records carry the organization's ИНН, so "same ФИО + same
 * company + in force" is a confirmed fact, while a same-name record of another company is
 * shown for manual comparison only.
 */
export default function DisqualifiedDumpPanel({ data }) {
  if (!data?.checked) return null;
  const directorRecords = data.director_records || [];
  const companyRecords = data.company_records || [];
  const otherCompanyRecords = companyRecords.filter(
    (r) => !directorRecords.some((d) => d.record_number === r.record_number),
  );
  const nothing = directorRecords.length === 0 && companyRecords.length === 0;

  return (
    <LocalListPanel
      title="Реестр дисквалифицированных лиц (выгрузка ФНС)"
      caption={`Выгрузка от ${data.dump_date}. Сверка по ФИО руководителя и по ИНН организации.`}
      outdated={data.outdated}
      manualLink={FNS_DATASET}
    >
      {data.director_confirmed && (
        <Alert severity="error" sx={{ mb: 1 }}>
          Директор дисквалифицирован: действующая запись совпала и по ФИО, и по ИНН организации
        </Alert>
      )}
      {nothing && (
        <Typography variant="body2" color="success.main">
          Записей по ФИО руководителя и по ИНН организации не найдено
        </Typography>
      )}
      {directorRecords.length > 0 && !data.director_confirmed && (
        <Alert severity="info" sx={{ mb: 1 }}>
          Найдены записи на лицо с таким же ФИО, но не для этой компании (или срок истёк) — вероятно, тёзка, сверьте вручную
        </Alert>
      )}
      {directorRecords.map((r) => <RecordBlock key={`d-${r.record_number}`} record={r} />)}
      {otherCompanyRecords.length > 0 && (
        <>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>Другие записи с ИНН этой организации</Typography>
          {otherCompanyRecords.map((r) => <RecordBlock key={`c-${r.record_number}`} record={r} />)}
        </>
      )}
    </LocalListPanel>
  );
}
