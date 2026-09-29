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

import FieldRow from './FieldRow';
import RawResponsePanel from './RawResponsePanel';
import GirBoPanel from './GirBoPanel';
import MspPanel from './MspPanel';
import DisqualifiedDumpPanel from './DisqualifiedDumpPanel';
import CbrWarningPanel from './CbrWarningPanel';
import OfacSdnPanel from './OfacSdnPanel';
import { RISK_LABELS, RISK_COLORS } from '../constants/risk';
import { buildPrefillUrl } from '../../../core/utils/crossFeatureNav';

const SOURCE_LABELS = {
  egrul: 'ЕГРЮЛ/ЕГРИП',
  disqualified_persons: 'Реестр дисквалифицированных лиц (РДЛ)',
  arbitration: 'Арбитражные дела',
  fssp: 'Исполнительные производства (ФССП)',
  fedresurs: 'Банкротство (Федресурс)',
  pb_nalog: 'Прозрачный бизнес (ФНС)',
  fedsfm: 'Перечень терроризм/ОМУ (ФедСФМ)',
  zakupki_rnp: 'Реестр недобросовестных поставщиков (РНП)',
  gir_bo: 'Бухгалтерская отчётность (ГИР БО)',
  msp: 'Реестр МСП',
  disqualified_dump: 'Реестр дисквалифицированных лиц (выгрузка ФНС)',
  cbr_warning: 'Список ЦБ: признаки нелегальной деятельности',
  ofac_sdn: 'Санкционный список OFAC SDN (США)',
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

// Sources that don't apply to this entity (e.g. the ЦБ list for an ИП) - neither checked nor
// pending; their `extra_data` entry says why.
function notApplicableSources(extra) {
  return Object.entries(extra || {}).filter(([, v]) => v?.not_applicable).map(([k]) => k);
}

export default function ResultsView({ result }) {
  if (!result) return null;

  const { egrul_data: egrul, disqualification_result: disq, arbitration_data: arb, fedresurs_data: fedresurs, pb_nalog_data: pbNalog, fedsfm_result: fedsfm, rnp_data: rnp, extra_data: extra, extra_raw: extraRaw, raw_sha256: sha, flags = [], checked_sources: checked = [], pending_sources: pending = [], candidates = [] } = result;
  const notApplicable = notApplicableSources(extra);

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
              <FieldRow label="ИНН" value={c.inn} />
              <FieldRow label="ОГРН" value={c.ogrn} />
              <FieldRow label="Адрес" value={c.address} />
              <FieldRow label="Статус" value={c.status} />
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

      {result.risk_level === 'incomplete' && (
        // Grey, like the verdict chip: it's neither a finding nor a clean result.
        <Alert
          severity="info"
          sx={{ mb: 2, bgcolor: 'action.hover', color: 'text.primary', '& .MuiAlert-icon': { color: 'text.secondary' } }}
        >
          Вердикт не выдан: не удалось проверить обязательные источники (
          {(result.missing_required_sources || []).map((s) => SOURCE_LABELS[s] || s).join(', ')}
          ). Отсутствие флагов по ним ничего не означает — повторите проверку позже или проверьте вручную.
        </Alert>
      )}

      {pending.length > 0 && candidates.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Проверены только: {checked.map((s) => SOURCE_LABELS[s] || s).join(', ')}. Не проверены (сбой источника или ещё не подключены):{' '}
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
          {notApplicable.length > 0 && (
            <> Не применимо к этому субъекту: {notApplicable.map((s) => SOURCE_LABELS[s] || s).join(', ')}.</>
          )}
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
          <FieldRow label="Полное наименование" value={egrul.full_name} />
          <FieldRow label="ОГРН" value={egrul.ogrn} />
          <FieldRow label="ИНН" value={egrul.inn} />
          <FieldRow label="КПП" value={egrul.kpp} />
          <FieldRow label="Дата регистрации" value={egrul.registration_date} />
          <FieldRow label="Адрес" value={egrul.address} />
          <FieldRow label="Статус" value={egrul.registry_status} />
          <FieldRow label="Директор" value={egrul.director_name && `${egrul.director_name}${egrul.director_position ? ` (${egrul.director_position})` : ''}`} />
          {egrul.founders?.length > 0 && (
            <FieldRow label="Учредители" value={egrul.founders.map((f) => `${f.name}${f.share ? ` — ${f.share}` : ''}`).join('; ')} />
          )}
          <FieldRow label="Основной ОКВЭД" value={egrul.okved_main} />
          {egrul.okved_additional?.length > 0 && (
            <FieldRow label="Доп. ОКВЭД" value={egrul.okved_additional.join('; ')} />
          )}
          <FieldRow label="Уставный капитал" value={egrul.capital} />

          <RawResponsePanel label="Сырые данные ЕГРЮЛ" raw={result.egrul_raw} sha256={sha?.egrul} />
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
                  <FieldRow label="ФИО" value={m.full_name} />
                  <FieldRow label="Номер записи РДЛ" value={m.record_number} />
                  <FieldRow label="Дата рождения (по реестру)" value={m.birth_date} />
                  <FieldRow label="Организация, должность" value={[m.organization, m.position].filter(Boolean).join(', ')} />
                  <FieldRow label="Статья КоАП РФ" value={m.article} />
                  <FieldRow label="Орган" value={m.issuing_authority} />
                  <FieldRow label="Сведения" value={m.details} />
                  <Divider sx={{ my: 1 }} />
                </Box>
              ))}
            </Box>
          )}

          <FieldRow
            label="Проверить вручную"
            value={
              <Link href={DISQUALIFIED_PERSONS_SEARCH_URL} target="_blank" rel="noopener noreferrer">
                {egrul?.director_name ? `Открыть service.nalog.ru и ввести «${egrul.director_name}»` : 'Открыть service.nalog.ru'}
              </Link>
            }
          />
          <RawResponsePanel label="Сырые данные РДЛ" raw={result.disqualification_raw} sha256={sha?.disqualified_persons} />
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
              <FieldRow
                label="Дело"
                value={c.case_url ? <Link href={c.case_url} target="_blank" rel="noopener noreferrer">{c.case_number}</Link> : c.case_number}
              />
              <FieldRow label="Роль" value={ARBITRATION_ROLE_LABELS[c.role] || c.role} />
              <FieldRow label="Статус" value={c.status} />
              <FieldRow label="Суд" value={c.court} />
              <FieldRow label="Дата регистрации" value={c.date_registered} />
              <FieldRow label="Сумма иска" value={formatAmount(c.claim_amount)} />
              <Divider sx={{ my: 1 }} />
            </Box>
          ))}

          <RawResponsePanel label="Сырые данные арбитража" raw={result.arbitration_raw} sha256={sha?.arbitration} />
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
          {fedresurs.found && !fedresurs.is_active_bankruptcy && fedresurs.status_recognized !== false && (
            <Typography variant="body2" color="success.main">Признаков активного банкротства не найдено</Typography>
          )}
          {fedresurs.found && fedresurs.status_recognized === false && (
            <Alert severity="warning" sx={{ mb: 1 }}>
              Статус «{fedresurs.status_text || '—'}» не входит в известные — проверьте карточку вручную
            </Alert>
          )}
          {fedresurs.found && (
            <>
              <FieldRow label="Статус" value={fedresurs.status_text} />
              {fedresurs.profile_url && (
                <FieldRow
                  label="Карточка"
                  value={<Link href={fedresurs.profile_url} target="_blank" rel="noopener noreferrer">Открыть на fedresurs.ru</Link>}
                />
              )}
            </>
          )}

          {fedresurs.publications_note && (
            <Alert severity={fedresurs.publications_checked ? 'info' : 'warning'} sx={{ my: 1 }}>
              {fedresurs.publications_note}
            </Alert>
          )}
          {fedresurs.messages?.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>Сообщения о фактах деятельности</Typography>
              {fedresurs.messages.map((m) => (
                <Typography key={m.url || `${m.date}-${m.number}`} variant="body2" color={m.signal ? 'warning.main' : 'text.secondary'}>
                  {m.date} —{' '}
                  {m.url ? <Link href={m.url} target="_blank" rel="noopener noreferrer">{m.type}</Link> : m.type}
                  {m.signal ? ' (учтено как признак)' : ''}
                </Typography>
              ))}
            </Box>
          )}

          <RawResponsePanel label="Сырые данные Федресурс" raw={result.fedresurs_raw} sha256={sha?.fedresurs} />
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
              <FieldRow label="Компаний по этому адресу" value={String(pbNalog.mass_address_count ?? 0)} />
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
                <FieldRow
                  label="Карточка"
                  value={<Link href={pbNalog.profile_url} target="_blank" rel="noopener noreferrer">Открыть на pb.nalog.ru</Link>}
                />
              )}
            </>
          )}

          <RawResponsePanel label="Сырые данные Прозрачный бизнес" raw={result.pb_nalog_raw} sha256={sha?.pb_nalog} />
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
                  <FieldRow label="ФИО" value={m.full_name} />
                  <FieldRow label="Тип" value={m.terrorist_type} />
                  <FieldRow label="Статус" value={m.status} />
                  <Divider sx={{ my: 1 }} />
                </Box>
              ))}
            </Box>
          )}

          <FieldRow
            label="Проверить вручную"
            value={
              <Link href={FEDSFM_SEARCH_URL} target="_blank" rel="noopener noreferrer">
                {egrul?.director_name ? `Открыть fedsfm.ru и ввести «${egrul.director_name}»` : 'Открыть fedsfm.ru'}
              </Link>
            }
          />
          <RawResponsePanel label="Сырые данные ФедСФМ" raw={result.fedsfm_raw} sha256={sha?.fedsfm} />
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
              <FieldRow
                label="Запись"
                value={e.detail_url ? <Link href={e.detail_url} target="_blank" rel="noopener noreferrer">№{e.registry_number}</Link> : e.registry_number}
              />
              <FieldRow label="Относится к" value={e.law} />
              <FieldRow label="Наименование" value={e.name} />
              <FieldRow label="Включено" value={e.included_date} />
              <FieldRow label="Планируемая дата исключения" value={e.planned_exclusion_date} />
              <Divider sx={{ my: 1 }} />
            </Box>
          ))}

          {result.resolved_inn && (
            <FieldRow
              label="Проверить вручную"
              value={
                <Link href={zakupkiRnpSearchUrl(result.resolved_inn)} target="_blank" rel="noopener noreferrer">
                  Повторить этот запрос на zakupki.gov.ru
                </Link>
              }
            />
          )}
          <RawResponsePanel label="Сырые данные РНП" raw={result.rnp_raw} sha256={sha?.zakupki_rnp} />
        </Paper>
      )}

      <DisqualifiedDumpPanel data={extra?.disqualified_dump} />

      <OfacSdnPanel data={extra?.ofac_sdn} />

      <CbrWarningPanel data={extra?.cbr_warning} />

      <GirBoPanel data={extra?.gir_bo} raw={extraRaw?.gir_bo} sha256={sha?.gir_bo} inn={result.resolved_inn} />

      <MspPanel data={extra?.msp} raw={extraRaw?.msp} sha256={sha?.msp} />

      {result.website && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>Домен компании</Typography>
          <FieldRow label="Сайт" value={result.website} />
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
