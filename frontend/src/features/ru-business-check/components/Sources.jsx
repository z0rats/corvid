import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

// Every external source considered for this feature's methodology, automated or not - kept
// as a plain hardcoded list (not settings/backend-driven) since it's informational and
// changes about as rarely as the feature's own source list does.
const STATUS_LABELS = {
  automated: 'Автоматизировано',
  manual: 'Только вручную',
  blocked: 'Заблокировано',
  unbuilt: 'Не реализовано',
  skipped: 'Решено не делать',
  not_viable: 'Не подходит',
};
const STATUS_COLORS = {
  automated: 'success',
  manual: 'warning',
  blocked: 'info',
  unbuilt: 'default',
  skipped: 'default',
  not_viable: 'error',
};

const SOURCES = [
  {
    name: 'ЕГРЮЛ/ЕГРИП',
    url: 'https://egrul.nalog.ru',
    status: 'automated',
    note: 'Официальная выписка: наименование, ОГРН/ИНН, директор, учредители, ОКВЭД, адрес, статус',
  },
  {
    name: 'Реестр дисквалифицированных лиц (РДЛ)',
    url: 'https://service.nalog.ru/disqualified.do',
    status: 'automated',
    note: 'Сверка директора по ФИО — только мягкий флаг, реестр не даёт другого идентификатора',
  },
  {
    name: 'Арбитражные дела',
    url: 'https://kad.arbitr.ru',
    status: 'automated',
    note: 'История дел по ИНН как истец/ответчик',
  },
  {
    name: 'Федресурс (банкротство)',
    url: 'https://fedresurs.ru',
    status: 'automated',
    note: 'Активное банкротство — жёсткий флаг',
  },
  {
    name: 'Прозрачный бизнес',
    url: 'https://pb.nalog.ru',
    status: 'automated',
    note: 'Массовый адрес регистрации — мягкий флаг',
  },
  {
    name: 'ФедСФМ (терроризм/ОМУ)',
    url: 'https://fedsfm.ru',
    status: 'automated',
    note: 'Сверка директора по ФИО — только мягкий флаг, как РДЛ',
  },
  {
    name: 'РНП (недобросовестные поставщики)',
    url: 'https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html',
    status: 'automated',
    note: 'Точное совпадение по ИНН — жёсткий флаг',
  },
  {
    name: 'ФССП (исполнительные производства)',
    url: 'https://fssp.gov.ru/iss/ip',
    status: 'manual',
    note: 'Капча на каждом запросе — только ручная проверка по ссылке в результатах',
  },
  {
    name: 'ГИР БО (финансовая отчётность)',
    url: 'https://bo.nalog.gov.ru',
    status: 'blocked',
    note: 'Поиск скрыт за внешним UnifiedClient — нужен захват сетевого трафика из реального браузера',
  },
  {
    name: 'Реестр уведомлений о залоге движимого имущества',
    url: 'https://www.reestr-zalogov.ru',
    status: 'unbuilt',
    note: 'Отдельный от Федресурса реестр (Федеральная нотариальная палата) — форма запроса не выяснена',
  },
  {
    name: 'Госзакупки: история контрактов',
    url: 'https://zakupki.gov.ru',
    status: 'unbuilt',
    note: 'Вторая половина госзакупок помимо РНП — низкий приоритет',
  },
  {
    name: 'rusprofile.ru',
    url: 'https://www.rusprofile.ru',
    status: 'skipped',
    note: 'Капча + вероятная защита от скрапинга — сигнал уже покрыт Прозрачным бизнесом',
  },
  {
    name: 'OpenSanctions',
    url: 'https://www.opensanctions.org/search/',
    status: 'manual',
    note: 'Не автоматизировано — лицензия CC BY-NC делает встроенную проверку рискованной (см. план). Доступно как ручная проверка по ссылке',
  },
  {
    name: 'ГАС «Правосудие»',
    url: 'https://bsr.sudrf.ru',
    status: 'not_viable',
    note: 'Нет единого API; рабочий обход требует ручного решения капчи на части судов',
  },
];

export default function Sources() {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>Источники</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Все источники, рассмотренные для методологии RU Business Check — как уже
        автоматизированные, так и нет. Возраст/анализ домена компании сюда не входит —
        эта проверка ведёт в модуль IOC-инструментов (WHOIS, DNS, Certificate Transparency),
        где для этого уже есть отдельная, более полная аналитика.
      </Typography>

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Источник</TableCell>
              <TableCell>Статус</TableCell>
              <TableCell>Комментарий</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {SOURCES.map((s) => (
              <TableRow key={s.name}>
                <TableCell>
                  <Link href={s.url} target="_blank" rel="noopener noreferrer">{s.name}</Link>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={STATUS_LABELS[s.status] || s.status} color={STATUS_COLORS[s.status] || 'default'} />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">{s.note}</Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
