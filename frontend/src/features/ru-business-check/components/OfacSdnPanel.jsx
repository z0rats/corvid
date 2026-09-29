import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';

import LocalListPanel from './LocalListPanel';

const OFAC_SEARCH = { href: 'https://sanctionssearch.ofac.treas.gov/', label: 'sanctionssearch.ofac.treas.gov' };

/**
 * Match against a local copy of the US Treasury OFAC SDN list by exact ИНН. A hit is exact;
 * a miss is not proof of anything - the list carries an ИНН for only part of its Russian
 * entries (a large bank, for one, is listed without it), so the panel always says so.
 */
export default function OfacSdnPanel({ data }) {
  if (!data?.checked) return null;
  const records = data.records || [];

  return (
    <LocalListPanel
      title="Санкционный список OFAC SDN (США)"
      caption={`Локальная копия списка на ${data.as_of}; сверка по точному ИНН, ИНН никуда не передаётся.`}
      outdated={data.outdated}
      manualLink={OFAC_SEARCH}
    >
      {records.length === 0 && (
        <Typography variant="body2" color="text.secondary">Совпадений по ИНН нет.</Typography>
      )}
      {records.map((r) => (
        <Alert key={`${r.ent_num}`} severity="error" sx={{ mb: 1 }}>
          В списке OFAC SDN: {r.name} ({r.kind === 'individual' ? 'физлицо' : 'организация'}){r.programs ? `, программы: ${r.programs}` : ''}. Это статус в американском перечне, не запрет по российскому праву.
        </Alert>
      ))}
      <Typography variant="body2" color="text.secondary">
        Нет совпадения — не значит «нет санкций»: у части российских записей OFAC не указывает ИНН (например, у некоторых крупных банков), а под ограничения могут попадать и организации, контролируемые лицами из списка. Список ЕС не проверяется.
      </Typography>
    </LocalListPanel>
  );
}
