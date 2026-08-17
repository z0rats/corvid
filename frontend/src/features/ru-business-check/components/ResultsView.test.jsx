import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import ResultsView from './ResultsView';

function renderWithRouter(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe('ResultsView', () => {
  it('renders nothing when there is no result', () => {
    const { container } = render(<ResultsView result={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows which sources are pending, next to the risk level', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'disqualified_persons'],
      pending_sources: ['arbitration', 'fssp', 'fedresurs'],
      flags: [],
    }} />);

    expect(screen.getByText(/Низкий/)).toBeInTheDocument();
    expect(screen.getByText(/Ещё не подключены/)).toBeInTheDocument();
  });

  it('does not show the pending-sources notice once nothing is pending', () => {
    render(<ResultsView result={{ risk_level: 'low', checked_sources: ['egrul'], pending_sources: [], flags: [] }} />);

    expect(screen.queryByText(/Ещё не подключены/)).not.toBeInTheDocument();
  });

  it('flags a disqualification match requiring manual review as a warning, not a confirmed fact', () => {
    render(<ResultsView result={{
      risk_level: 'medium',
      checked_sources: ['egrul', 'disqualified_persons'],
      pending_sources: [],
      flags: [{ code: 'disqualified_possible_match', severity: 'soft', title: 'Возможное совпадение', detail: 'x' }],
      disqualification_result: {
        checked: true, matched: true, requires_manual_review: true,
        matches: [{ full_name: 'Иванов Иван Иванович' }],
      },
    }} />);

    expect(screen.getByText(/требуется ручная проверка/i)).toBeInTheDocument();
  });

  it('offers a manual-check link to service.nalog.ru with the director name spelled out', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'disqualified_persons'],
      pending_sources: [],
      flags: [],
      egrul_data: { director_name: 'Иванов Иван Иванович' },
      disqualification_result: { checked: true, matched: false, requires_manual_review: false, matches: [] },
    }} />);

    const link = screen.getByRole('link', { name: /Иванов Иван Иванович/ });
    expect(link).toHaveAttribute('href', 'https://service.nalog.ru/disqualified.do');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('renders ЕГРЮЛ fields and a raw-data toggle when egrul_data is present', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul'],
      pending_sources: [],
      flags: [],
      egrul_data: { full_name: 'ООО «Нитка»', inn: '7712345678' },
      egrul_raw: '{"raw": true}',
    }} />);

    expect(screen.getByText('ООО «Нитка»')).toBeInTheDocument();
    expect(screen.getByText('Сырые данные ЕГРЮЛ')).toBeInTheDocument();
  });

  it('shows "no cases found" when arbitration was checked and came back clean', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'arbitration'],
      pending_sources: [],
      flags: [],
      arbitration_data: { checked: true, cases: [] },
    }} />);

    expect(screen.getByText('Дел не найдено')).toBeInTheDocument();
  });

  it('renders arbitration case details with a link to the case, and a raw-data toggle', () => {
    render(<ResultsView result={{
      risk_level: 'medium',
      checked_sources: ['egrul', 'arbitration'],
      pending_sources: [],
      flags: [],
      arbitration_data: {
        checked: true,
        cases: [{
          case_number: 'А40-11111/2023', role: 'defendant', status: 'Рассмотрение',
          court: 'АС города Москвы', date_registered: '2023-01-15', claim_amount: 1500000,
          case_url: 'https://kad.arbitr.ru/Card/abc-123',
        }],
      },
      arbitration_raw: '{"raw": true}',
    }} />);

    const link = screen.getByRole('link', { name: 'А40-11111/2023' });
    expect(link).toHaveAttribute('href', 'https://kad.arbitr.ru/Card/abc-123');
    expect(screen.getByText('Ответчик')).toBeInTheDocument();
    expect(screen.getByText('1 500 000 ₽')).toBeInTheDocument();
    expect(screen.getByText('Сырые данные арбитража')).toBeInTheDocument();
  });

  it('does not render an arbitration section when arbitration was not checked', () => {
    render(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: ['arbitration'], flags: [],
    }} />);

    expect(screen.queryByText('Арбитражные дела')).not.toBeInTheDocument();
  });

  it('shows "not found" when fedresurs was checked and the entity is not in the register', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'fedresurs'],
      pending_sources: [],
      flags: [],
      fedresurs_data: { checked: true, found: false, status_text: null, is_active_bankruptcy: false, profile_url: null },
    }} />);

    expect(screen.getByText('Не найдено в реестре')).toBeInTheDocument();
  });

  it('flags an active bankruptcy with an error alert and a link to the fedresurs card', () => {
    render(<ResultsView result={{
      risk_level: 'high',
      checked_sources: ['egrul', 'fedresurs'],
      pending_sources: [],
      flags: [{ code: 'active_bankruptcy', severity: 'hard', title: 'Активное дело о банкротстве', detail: 'x' }],
      fedresurs_data: {
        checked: true, found: true, is_active_bankruptcy: true,
        status_text: 'Юридическое лицо признано несостоятельным (банкротом)',
        profile_url: 'https://fedresurs.ru/company/abc-123',
      },
      fedresurs_raw: '{"raw": true}',
    }} />);

    expect(screen.getByText('Найдено активное дело о банкротстве')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Открыть на fedresurs.ru' });
    expect(link).toHaveAttribute('href', 'https://fedresurs.ru/company/abc-123');
    expect(screen.getByText('Сырые данные Федресурс')).toBeInTheDocument();
  });

  it('does not render a fedresurs section when fedresurs was not checked', () => {
    render(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: ['fedresurs'], flags: [],
    }} />);

    expect(screen.queryByText('Банкротство (Федресурс)')).not.toBeInTheDocument();
  });

  it('shows "not found" when pb_nalog was checked and the entity was not found', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'pb_nalog'],
      pending_sources: [],
      flags: [],
      pb_nalog_data: { checked: true, found: false, mass_address_count: 0, mass_address_companies: [], profile_url: null },
    }} />);

    expect(screen.getByText('Не найдено на pb.nalog.ru')).toBeInTheDocument();
  });

  it('lists mass-address companies and links to the pb.nalog.ru card', () => {
    render(<ResultsView result={{
      risk_level: 'medium',
      checked_sources: ['egrul', 'pb_nalog'],
      pending_sources: [],
      flags: [{ code: 'mass_registration_address', severity: 'soft', title: 'Признаки адреса массовой регистрации', detail: 'x' }],
      pb_nalog_data: {
        checked: true, found: true, mass_address_count: 2,
        mass_address_companies: [{ inn: '111', name: 'ООО Сосед' }, { inn: '222', name: 'ООО Другой Сосед' }],
        profile_url: 'https://pb.nalog.ru/search.html#mode=search-all&queryAll=7712345678',
      },
      pb_nalog_raw: '{"raw": true}',
    }} />);

    expect(screen.getByText('ООО Сосед (ИНН 111)')).toBeInTheDocument();
    expect(screen.getByText('ООО Другой Сосед (ИНН 222)')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Открыть на pb.nalog.ru' });
    expect(link).toHaveAttribute('href', 'https://pb.nalog.ru/search.html#mode=search-all&queryAll=7712345678');
    expect(screen.getByText('Сырые данные Прозрачный бизнес')).toBeInTheDocument();
  });

  it('does not render a pb_nalog section when pb_nalog was not checked', () => {
    render(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: ['pb_nalog'], flags: [],
    }} />);

    expect(screen.queryByText('Прозрачный бизнес (ФНС)')).not.toBeInTheDocument();
  });

  it('shows "no matches" when fedsfm was checked and came back clean', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'fedsfm'],
      pending_sources: [],
      flags: [],
      fedsfm_result: { checked: true, matched: false, requires_manual_review: false, matches: [] },
    }} />);

    expect(screen.getByText('Перечень терроризм/ОМУ (ФедСФМ)')).toBeInTheDocument();
    expect(screen.getAllByText('Совпадений не найдено').length).toBeGreaterThan(0);
  });

  it('flags a fedsfm match requiring manual review as a warning, not a confirmed fact', () => {
    render(<ResultsView result={{
      risk_level: 'medium',
      checked_sources: ['egrul', 'fedsfm'],
      pending_sources: [],
      flags: [{ code: 'fedsfm_possible_match', severity: 'soft', title: 'Возможное совпадение', detail: 'x' }],
      fedsfm_result: {
        checked: true, matched: true, requires_manual_review: true,
        matches: [{ full_name: 'Иванов Иван Иванович', terrorist_type: 'Национальный', status: 'Физическое лицо' }],
      },
      fedsfm_raw: '{"raw": true}',
    }} />);

    expect(screen.getByText('Иванов Иван Иванович')).toBeInTheDocument();
    expect(screen.getByText(/требуется ручная проверка/i)).toBeInTheDocument();
    expect(screen.getByText('Сырые данные ФедСФМ')).toBeInTheDocument();
  });

  it('offers a manual-check link to fedsfm.ru with the director name spelled out', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'fedsfm'],
      pending_sources: [],
      flags: [],
      egrul_data: { director_name: 'Иванов Иван Иванович' },
      fedsfm_result: { checked: true, matched: false, requires_manual_review: false, matches: [] },
    }} />);

    const link = screen.getByRole('link', { name: /Иванов Иван Иванович/ });
    expect(link).toHaveAttribute('href', 'https://fedsfm.ru/documents/terr-list');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('does not render a fedsfm section when fedsfm was not checked', () => {
    render(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: ['fedsfm'], flags: [],
    }} />);

    expect(screen.queryByText('Перечень терроризм/ОМУ (ФедСФМ)')).not.toBeInTheDocument();
  });

  it('shows "no entries" when the RNP was checked and came back clean', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'zakupki_rnp'],
      pending_sources: [],
      flags: [],
      rnp_data: { checked: true, entries: [] },
    }} />);

    expect(screen.getByText('Действующих записей не найдено')).toBeInTheDocument();
  });

  it('flags a confirmed RNP match as a hard error, with a link to the registry entry', () => {
    render(<ResultsView result={{
      risk_level: 'high',
      checked_sources: ['egrul', 'zakupki_rnp'],
      pending_sources: [],
      flags: [{ code: 'rnp_confirmed', severity: 'hard', title: 'Запись в РНП', detail: 'x' }],
      rnp_data: {
        checked: true,
        entries: [{
          registry_number: '26008859', law: '44-ФЗ', name: 'ООО "СОКОЛСТРОЙ"',
          included_date: '13.08.2026', planned_exclusion_date: '14.08.2028',
          detail_url: 'https://zakupki.gov.ru/epz/dishonestsupplier/view/info.html?reestrNumber=26008859&law=FZ44',
        }],
      },
      rnp_raw: '{"raw": true}',
    }} />);

    expect(screen.getByText(/Найдено 1 действующ/)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: '№26008859' });
    expect(link).toHaveAttribute('href', 'https://zakupki.gov.ru/epz/dishonestsupplier/view/info.html?reestrNumber=26008859&law=FZ44');
    expect(screen.getByText('Сырые данные РНП')).toBeInTheDocument();
  });

  it('offers a repeat-this-search link to zakupki.gov.ru even when no entries were found', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'zakupki_rnp'],
      pending_sources: [],
      flags: [],
      resolved_inn: '7712345678',
      rnp_data: { checked: true, entries: [] },
    }} />);

    const link = screen.getByRole('link', { name: /Повторить этот запрос на zakupki\.gov\.ru/ });
    expect(link.getAttribute('href')).toContain('searchString=7712345678');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('does not render an RNP section when it was not checked', () => {
    render(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: ['zakupki_rnp'], flags: [],
    }} />);

    expect(screen.queryByText('Реестр недобросовестных поставщиков')).not.toBeInTheDocument();
  });

  it('renders a domain block linking to the IOC-tools domain finder when a website was supplied', () => {
    renderWithRouter(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: [], flags: [],
      website: 'example.ru',
    }} />);

    expect(screen.getByText('example.ru')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Открыть в IOC-инструментах/ });
    expect(link).toHaveAttribute('href', '/ioc-tools/domain-finder?q=example.ru');
  });

  it('does not render a domain block when no website was supplied', () => {
    renderWithRouter(<ResultsView result={{
      risk_level: 'low', checked_sources: ['egrul'], pending_sources: [], flags: [], website: null,
    }} />);

    expect(screen.queryByText('Домен компании')).not.toBeInTheDocument();
  });

  it('renders fssp as a manual-check link in the pending-sources notice, not plain text', () => {
    render(<ResultsView result={{
      risk_level: 'low',
      checked_sources: ['egrul', 'arbitration', 'fedresurs'],
      pending_sources: ['fssp'],
      flags: [],
    }} />);

    const link = screen.getByRole('link', { name: /Исполнительные производства \(ФССП\)/ });
    expect(link).toHaveAttribute('href', 'https://fssp.gov.ru/iss/ip');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('renders a disambiguation list with a re-scan link and an external link when the query was ambiguous', () => {
    renderWithRouter(<ResultsView result={{
      risk_level: null,
      checked_sources: [],
      pending_sources: ['egrul', 'disqualified_persons', 'arbitration', 'fssp', 'fedresurs'],
      flags: [],
      candidates: [
        { name: 'ООО Ромашка №1', inn: '7712345671', ogrn: '1234567890121', address: 'г. Москва', status: 'Действующее' },
        { name: 'ООО Ромашка №2', inn: '7712345672', ogrn: '1234567890122', address: 'г. Санкт-Петербург', status: 'Действующее' },
      ],
    }} />);

    expect(screen.getByText(/Найдено 2 совпадений/)).toBeInTheDocument();
    expect(screen.getByText('ООО Ромашка №1')).toBeInTheDocument();
    expect(screen.getByText('ООО Ромашка №2')).toBeInTheDocument();

    // Re-scans by ОГРН, not ИНН - an ИНН can map to more than one record (e.g. an ИП
    // that closed and later re-registered keeps the same personal ИНН across both),
    // confirmed live: the same personal ИНН search returned two distinct candidates.
    const rescanLinks = screen.getAllByRole('link', { name: 'Проверить эту запись' });
    expect(rescanLinks).toHaveLength(2);
    expect(rescanLinks[0]).toHaveAttribute('href', '/ru-business-check/new?q=1234567890121');

    const externalLinks = screen.getAllByRole('link', { name: 'Открыть на rusprofile.ru' });
    expect(externalLinks[0]).toHaveAttribute('href', 'https://www.rusprofile.ru/id/1234567890121');
    expect(externalLinks[0]).toHaveAttribute('target', '_blank');
  });

  it('falls back to ИНН for the re-scan link when a candidate has no ОГРН', () => {
    renderWithRouter(<ResultsView result={{
      risk_level: null,
      checked_sources: [],
      pending_sources: ['egrul', 'disqualified_persons', 'arbitration', 'fssp', 'fedresurs'],
      flags: [],
      candidates: [{ name: 'ООО Ромашка', inn: '7712345671', ogrn: null, address: null, status: null }],
    }} />);

    const rescanLink = screen.getByRole('link', { name: 'Проверить эту запись' });
    expect(rescanLink).toHaveAttribute('href', '/ru-business-check/new?q=7712345671');
  });

  it('links to rusprofile.ru\'s /ip/ path for an individual entrepreneur (15-digit ОГРНИП), not /id/', () => {
    // Regression: /id/<ogrnip> 404s on rusprofile.ru for an ИП - confirmed live.
    renderWithRouter(<ResultsView result={{
      risk_level: null,
      checked_sources: [],
      pending_sources: ['egrul', 'disqualified_persons', 'arbitration', 'fssp', 'fedresurs'],
      flags: [],
      candidates: [
        { name: 'ИП Иванов Иван Иванович', inn: '771234567890', ogrn: '319715400058451', address: 'г. Тула', status: null },
      ],
    }} />);

    const externalLink = screen.getByRole('link', { name: 'Открыть на rusprofile.ru' });
    expect(externalLink).toHaveAttribute('href', 'https://www.rusprofile.ru/ip/319715400058451');
  });

  it('does not show the pending-sources notice when the result is an ambiguous match', () => {
    renderWithRouter(<ResultsView result={{
      risk_level: null,
      checked_sources: [],
      pending_sources: ['egrul', 'disqualified_persons', 'arbitration', 'fssp', 'fedresurs'],
      flags: [],
      candidates: [{ name: 'ООО Ромашка', inn: '7712345678' }],
    }} />);

    expect(screen.queryByText(/Ещё не подключены/)).not.toBeInTheDocument();
  });
});
