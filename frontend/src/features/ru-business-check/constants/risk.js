// "incomplete": no hard flag was found, but a source that could have raised one wasn't
// checked - the absence of flags means nothing there (see flag_engine.py). Deliberately not
// a "low"-looking chip.
export const RISK_LABELS = { low: 'Низкий', medium: 'Средний', high: 'Высокий', incomplete: 'Проверка неполная' };
export const RISK_COLORS = { low: 'success', medium: 'warning', high: 'error', incomplete: 'default' };
