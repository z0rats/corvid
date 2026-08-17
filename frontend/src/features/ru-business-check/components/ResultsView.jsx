import { Fragment } from 'react';
import { Link as RouterLink } from 'react-router';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';

import RawResponsePanel from './RawResponsePanel';
import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';

const RISK_LABELS = { low: 'Низкий', medium: 'Средний', high: 'Высокий' };
const RISK_COLORS = { low: 'success', medium: 'warning', high: 'error' };
const SOURCE_LABELS = {
  egrul: 'ЕГРЮЛ/ЕГРИП',
  disqualified_persons: 'Реестр дисквалифицированных лиц (РДЛ)',
  arbitration: 'Арбитражные дела',
  fssp: 'Исполнительные производства (ФССП)',
  fedresurs: 'Банкротство (Федресурс)',
  pb_nalog: 'Прозрачный бизнес (ФНС)',
  fedsfm: 'Перечень терроризм/ОМУ (ФедСФМ)',
  zakupki_rnp: 'Реестр недобросовестных поставщиков (РНП)',
};
// ФССП's own API is dead and its public search demands a CAPTCHA on every query
// (confirmed live, see docs/adr/0006-*.md's addendum), so it can't be automated -
// this is a one-click manual-check affordance instead of a scraped source.
const FSSP_MANUAL_CHECK_URL = 'https://fssp.gov.ru/iss/ip';
const ARBITRATION_ROLE_LABELS = { plaintiff: 'Истец', defendant: 'Ответчик', other: 'Иная роль' };

function formatAmount(amount) {
  if (amount == null) return null;
  return `${new Intl.NumberFormat('ru-RU').format(amount)} ₽`;
}

// rusprofile.ru uses a different path per entity type - /id/<ogrn> for legal entities
// (13-digit ОГРН), /ip/<ogrnip> for individual entrepreneurs (15-digit ОГРНИП); using
// /id/ for an ИП 404s (confirmed live). Same ОГРН-length convention already used
// server-side (ru_business_check_service.py's _entity_type_from_ogrn).
function rusprofileUrl(ogrn) {
  const segment = ogrn.length === 15 ? 'ip' : 'id';
  return `https://www.rusprofile.ru/${segment}/${ogrn}`;
}

// РДЛ and ФедСФМ's own search forms are both POST/JS-driven (confirmed live - neither
// reads a query string to pre-fill or auto-run a search), so unlike РНП below there's no
// URL that reproduces the exact search - only a link to the real search page itself,
// landing the analyst one step closer than the bare homepage would.
const DISQUALIFIED_PERSONS_SEARCH_URL = 'https://service.nalog.ru/disqualified.do';
const FEDSFM_SEARCH_URL = 'https://fedsfm.ru/documents/terr-list';

// zakupki.gov.ru's РНП search *does* read its query string directly (confirmed live via a
// real browser - a fresh session with no prior cookie still resolves this URL correctly),
// so this reproduces the exact same server-side search this feature itself already ran.
function zakupkiRnpSearchUrl(inn) {
  const params = new URLSearchParams({
    searchString: inn,
    fz94: 'on',
    fz223: 'on',
    ppRf615: 'on',
    dsStatuses: '0',
    sortBy: 'UPDATE_DATE',
    pageNumber: '1',
    sortDirection: 'false',
    recordsPerPage: '_10',
  });
  return `https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html?${params}`;
}

function Field({ label, value }) {
  if (!value) return null;
  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 0.5 }}>
      <Typography variant="body2" color="text.secondary" sx={{ minWidth: 200 }}>{label}</Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

export default function ResultsView({ result }) {
  if (!result) return null;

  const { egrul_data: egrul, disqualification_result: disq, arbitration_data: arb, fedresurs_data: fedresurs, pb_nalog_data: pbNalog, fedsfm_result: fedsfm, rnp_data: rnp, flags = [], checked_sources: checked = [], pending_sources: pending = [], candidates = [] } = result;

  return (
    <Box>
      {candidates.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Найдено {candidates.length} совпадений — уточните, какая запись нужна
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Запрос по названию вернул несколько записей ЕГРЮЛ/ЕГРИП. Нажмите «Проверить эту запись»,
            чтобы запустить полную проверку по ней — по ОГРН, а не ИНН, поскольку один ИНН может
            соответствовать нескольким записям (например, у ИП, закрывавшего и снова открывавшего
            регистрацию).
          </Typography>
          {candidates.map((c, i) => (
            <Box
              key={i}
              sx={{ mb: 1.5, pb: 1.5, borderBottom: i < candidates.length - 1 ? 1 : 0, borderColor: 'divider' }}
            >
              <Typography variant="body2" fontWeight="bold">{c.name || 'Без названия'}</Typography>
              <Field label="ИНН" value={c.inn} />
              <Field label="ОГРН" value={c.ogrn} />
              <Field label="Адрес" value={c.address} />
              <Field label="Статус" value={c.status} />
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                {(c.ogrn || c.inn) && (
                  <Button
                    size="small"
                    variant="outlined"
                    component={RouterLink}
                    to={buildPrefillUrl('/ru-business-check/new', c.ogrn || c.inn)}
                  >
                    Проверить эту запись
                  </Button>
                )}
                {c.ogrn && (
                  <Button
                    size="small"
                    variant="text"
                    href={rusprofileUrl(c.ogrn)}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Открыть на rusprofile.ru
                  </Button>
                )}
              </Box>
            </Box>
          ))}
        </Paper>
      )}

      {result.risk_level && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Typography variant="subtitle1">Уровень риска:</Typography>
          <Chip label={RISK_LABELS[result.risk_level] || result.risk_level} color={RISK_COLORS[result.risk_level] || 'default'} />
          {result.completed_at && (
            <Typography variant="caption" color="text.secondary">
              на {new Date(result.completed_at).toLocaleString()}
            </Typography>
          )}
        </Box>
      )}

      {pending.length > 0 && candidates.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Проверены только: {checked.map((s) => SOURCE_LABELS[s] || s).join(', ')}. Ещё не подключены:{' '}
          {pending.map((s, i) => {
            const separator = i > 0 ? ', ' : '';
            if (s === 'fssp') {
              return (
                <Fragment key={s}>
                  {separator}
                  <Link href={FSSP_MANUAL_CHECK_URL} target="_blank" rel="noopener noreferrer">
                    {SOURCE_LABELS[s]} (проверить вручную)
                  </Link>
                </Fragment>
              );
            }
            return `${separator}${SOURCE_LABELS[s] || s}`;
          })}
          . Уровень риска основан только на проверенных источниках — не считайте его полной оценкой.
        </Alert>
      )}

      {flags.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>🚩 Флаги</Typography>
          {flags.map((flag) => (
            <Box key={flag.code} sx={{ mb: 1 }}>
              <Chip
                size="small"
                label={flag.severity === 'hard' ? 'Жёсткий' : 'Мягкий'}
                color={flag.severity === 'hard' ? 'error' : 'warning'}
                sx={{ mr: 1 }}
              />
              <Typography variant="body2" component="span" fontWeight="bold">{flag.title}</Typography>
              <Typography variant="body2" color="text.secondary">{flag.detail}</Typography>
            </Box>
          ))}
        </Paper>
      )}

      {egrul && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>ЕГРЮЛ/ЕГРИП</Typography>
          <Field label="Полное наименование" value={egrul.full_name} />
          <Field label="ОГРН" value={egrul.ogrn} />
          <Field label="ИНН" value={egrul.inn} />
          <Field label="КПП" value={egrul.kpp} />
          <Field label="Дата регистрации" value={egrul.registration_date} />
          <Field label="Адрес" value={egrul.address} />
          <Field label="Статус" value={egrul.registry_status} />
          <Field label="Директор" value={egrul.director_name && `${egrul.director_name}${egrul.director_position ? ` (${egrul.director_position})` : ''}`} />
          {egrul.founders?.length > 0 && (
            <Field label="Учредители" value={egrul.founders.map((f) => `${f.name}${f.share ? ` — ${f.share}` : ''}`).join('; ')} />
          )}
          <Field label="Основной ОКВЭД" value={egrul.okved_main} />
          {egrul.okved_additional?.length > 0 && (
            <Field label="Доп. ОКВЭД" value={egrul.okved_additional.join('; ')} />
          )}
          <Field label="Уставный капитал" value={egrul.capital} />

          <RawResponsePanel label="Сырые данные ЕГРЮЛ" raw={result.egrul_raw} />
        </Paper>
      )}

      {disq?.checked && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Реестр дисквалифицированных лиц</Typography>
          {!disq.matched && (
            <Typography variant="body2" color="success.main">Совпадений не найдено</Typography>
          )}
          {disq.matched && (
            <Box>
              {disq.requires_manual_review && (
                <Alert severity="warning" sx={{ mb: 1 }}>
                  Найдено совпадение по ФИО — реестр не даёт дополнительного идентификатора для
                  однозначной сверки. Требуется ручная проверка, прежде чем считать это
                  подтверждённым фактом.
                </Alert>
              )}
              {disq.matches.map((m, i) => (
                <Box key={i} sx={{ mb: 1 }}>
                  <Field label="ФИО" value={m.full_name} />
                  <Field label="Номер записи РДЛ" value={m.record_number} />
                  <Field label="Организация, должность" value={[m.organization, m.position].filter(Boolean).join(', ')} />
                  <Field label="Статья КоАП РФ" value={m.article} />
                  <Field label="Орган" value={m.issuing_authority} />
                  <Field label="Сведения" value={m.details} />
                  <Divider sx={{ my: 1 }} />
                </Box>
              ))}
            </Box>
          )}

          <Field
            label="Проверить вручную"
            value={
              <Link href={DISQUALIFIED_PERSONS_SEARCH_URL} target="_blank" rel="noopener noreferrer">
                {egrul?.director_name ? `Открыть service.nalog.ru и ввести «${egrul.director_name}»` : 'Открыть service.nalog.ru'}
              </Link>
            }
          />
          <RawResponsePanel label="Сырые данные РДЛ" raw={result.disqualification_raw} />
        </Paper>
      )}

      {arb?.checked && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Арбитражные дела</Typography>
          {arb.cases.length === 0 && (
            <Typography variant="body2" color="success.main">Дел не найдено</Typography>
          )}
          {arb.cases.map((c, i) => (
            <Box key={i} sx={{ mb: 1 }}>
              <Field
                label="Дело"
                value={c.case_url ? <Link href={c.case_url} target="_blank" rel="noopener noreferrer">{c.case_number}</Link> : c.case_number}
              />
              <Field label="Роль" value={ARBITRATION_ROLE_LABELS[c.role] || c.role} />
              <Field label="Статус" value={c.status} />
              <Field label="Суд" value={c.court} />
              <Field label="Дата регистрации" value={c.date_registered} />
              <Field label="Сумма иска" value={formatAmount(c.claim_amount)} />
              <Divider sx={{ my: 1 }} />
            </Box>
          ))}

          <RawResponsePanel label="Сырые данные арбитража" raw={result.arbitration_raw} />
        </Paper>
      )}

      {fedresurs?.checked && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Банкротство (Федресурс)</Typography>
          {!fedresurs.found && (
            <Typography variant="body2" color="success.main">Не найдено в реестре</Typography>
          )}
          {fedresurs.found && fedresurs.is_active_bankruptcy && (
            <Alert severity="error" sx={{ mb: 1 }}>
              Найдено активное дело о банкротстве
            </Alert>
          )}
          {fedresurs.found && !fedresurs.is_active_bankruptcy && (
            <Typography variant="body2" color="success.main">Признаков активного банкротства не найдено</Typography>
          )}
          {fedresurs.found && (
            <>
              <Field label="Статус" value={fedresurs.status_text} />
              {fedresurs.profile_url && (
                <Field
                  label="Карточка"
                  value={<Link href={fedresurs.profile_url} target="_blank" rel="noopener noreferrer">Открыть на fedresurs.ru</Link>}
                />
              )}
            </>
          )}

          <RawResponsePanel label="Сырые данные Федресурс" raw={result.fedresurs_raw} />
        </Paper>
      )}

      {pbNalog?.checked && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Прозрачный бизнес (ФНС)</Typography>
          {!pbNalog.found && (
            <Typography variant="body2" color="success.main">Не найдено на pb.nalog.ru</Typography>
          )}
          {pbNalog.found && (
            <>
              <Field label="Компаний по этому адресу" value={String(pbNalog.mass_address_count ?? 0)} />
              {pbNalog.mass_address_companies?.length > 0 && (
                <Box sx={{ ml: 1, mb: 1 }}>
                  {pbNalog.mass_address_companies.map((c, i) => (
                    <Typography key={i} variant="body2" color="text.secondary">
                      {c.name}{c.inn ? ` (ИНН ${c.inn})` : ''}
                    </Typography>
                  ))}
                  {pbNalog.mass_address_count > pbNalog.mass_address_companies.length && (
                    <Typography variant="caption" color="text.secondary">
                      и ещё {pbNalog.mass_address_count - pbNalog.mass_address_companies.length}…
                    </Typography>
                  )}
                </Box>
              )}
              {pbNalog.profile_url && (
                <Field
                  label="Карточка"
                  value={<Link href={pbNalog.profile_url} target="_blank" rel="noopener noreferrer">Открыть на pb.nalog.ru</Link>}
                />
              )}
            </>
          )}

          <RawResponsePanel label="Сырые данные Прозрачный бизнес" raw={result.pb_nalog_raw} />
        </Paper>
      )}

      {fedsfm?.checked && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Перечень терроризм/ОМУ (ФедСФМ)</Typography>
          {!fedsfm.matched && (
            <Typography variant="body2" color="success.main">Совпадений не найдено</Typography>
          )}
          {fedsfm.matched && (
            <Box>
              {fedsfm.requires_manual_review && (
                <Alert severity="warning" sx={{ mb: 1 }}>
                  Найдено совпадение по ФИО в перечне организаций и физических лиц, причастных к
                  терроризму/финансированию распространения оружия массового уничтожения — перечень
                  не даёт дополнительного идентификатора для однозначной сверки. Требуется ручная
                  проверка, прежде чем считать это подтверждённым фактом.
                </Alert>
              )}
              {fedsfm.matches.map((m, i) => (
                <Box key={i} sx={{ mb: 1 }}>
                  <Field label="ФИО" value={m.full_name} />
                  <Field label="Тип" value={m.terrorist_type} />
                  <Field label="Статус" value={m.status} />
                  <Divider sx={{ my: 1 }} />
                </Box>
              ))}
            </Box>
          )}

          <Field
            label="Проверить вручную"
            value={
              <Link href={FEDSFM_SEARCH_URL} target="_blank" rel="noopener noreferrer">
                {egrul?.director_name ? `Открыть fedsfm.ru и ввести «${egrul.director_name}»` : 'Открыть fedsfm.ru'}
              </Link>
            }
          />
          <RawResponsePanel label="Сырые данные ФедСФМ" raw={result.fedsfm_raw} />
        </Paper>
      )}

      {rnp?.checked && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Реестр недобросовестных поставщиков</Typography>
          {rnp.entries.length === 0 && (
            <Typography variant="body2" color="success.main">Действующих записей не найдено</Typography>
          )}
          {rnp.entries.length > 0 && (
            <Alert severity="error" sx={{ mb: 1 }}>
              Найдено {rnp.entries.length} действующ(ая/их) запис(ь/и) в РНП — точное совпадение по ИНН
            </Alert>
          )}
          {rnp.entries.map((e, i) => (
            <Box key={i} sx={{ mb: 1 }}>
              <Field
                label="Запись"
                value={e.detail_url ? <Link href={e.detail_url} target="_blank" rel="noopener noreferrer">№{e.registry_number}</Link> : e.registry_number}
              />
              <Field label="Относится к" value={e.law} />
              <Field label="Наименование" value={e.name} />
              <Field label="Включено" value={e.included_date} />
              <Field label="Планируемая дата исключения" value={e.planned_exclusion_date} />
              <Divider sx={{ my: 1 }} />
            </Box>
          ))}

          {result.resolved_inn && (
            <Field
              label="Проверить вручную"
              value={
                <Link href={zakupkiRnpSearchUrl(result.resolved_inn)} target="_blank" rel="noopener noreferrer">
                  Повторить этот запрос на zakupki.gov.ru
                </Link>
              }
            />
          )}
          <RawResponsePanel label="Сырые данные РНП" raw={result.rnp_raw} />
        </Paper>
      )}

      {result.website && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Домен компании</Typography>
          <Field label="Сайт" value={result.website} />
          <Button
            size="small"
            variant="outlined"
            component={RouterLink}
            to={buildPrefillUrl('/ioc-tools/domain-finder', result.website)}
            sx={{ mt: 1 }}
          >
            Открыть в IOC-инструментах (WHOIS, DNS, Certificate Transparency)
          </Button>
        </Paper>
      )}
    </Box>
  );
}
