import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import LocalListPanel from './LocalListPanel';

const CBR_LIST = { href: 'https://www.cbr.ru/inside/warning-list/', label: 'cbr.ru/inside/warning-list' };

/**
 * Match against a local copy of the Банк России list of companies with signs of illegal
 * activity in the financial market. The entry is the regulator's stated *sign*, not a court
 * finding; a "clone" entry means the ИНН owner is the impersonated party; and not being on
 * the list is not proof of a clean record (the same operator may be listed under another
 * name or website, which carry no ИНН). The list has no ИП ИНН - shown as not applicable.
 */
export default function CbrWarningPanel({ data }) {
  if (!data?.checked) return null;
  const records = data.records || [];

  return (
    <LocalListPanel
      title="Список Банка России: признаки нелегальной деятельности"
      caption={data.as_of ? `Локальная копия списка на ${data.as_of}; сверка по точному ИНН, ИНН в ЦБ не передаётся.` : null}
      outdated={data.outdated}
      manualLink={CBR_LIST}
    >
      {data.not_applicable && (
        <Typography variant="body2" color="text.secondary">{data.not_applicable}</Typography>
      )}
      {!data.not_applicable && records.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          Записей с этим ИНН нет. Это не значит, что компании нет в списке: часть записей (сайты, «точки присутствия») публикуется без ИНН.
        </Typography>
      )}
      {records.map((r) => (
        <Box key={r.cbr_id} sx={{ mb: 1 }}>
          {r.is_clone ? (
            <Alert severity="info" sx={{ mb: 0.5 }}>
              Запись «{r.name}» отмечена ЦБ как использующая данные легального участника рынка — вероятно, данные компании используют мошенники; против самой компании это не сигнал
            </Alert>
          ) : (
            <Alert severity="warning" sx={{ mb: 0.5 }}>
              ЦБ сообщает о признаках: {r.sign || '—'}{r.listed_at ? `, в списке с ${r.listed_at}` : ''}{r.closed ? ' (организация отмечена ликвидированной)' : ''}
            </Alert>
          )}
        </Box>
      ))}
    </LocalListPanel>
  );
}
