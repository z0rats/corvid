import { renderHook, act } from '@testing-library/react';
import { newsfeedApi } from '../../services/api/newsfeedApi';
import { useArticleActions } from './useArticleActions';

vi.mock('../../services/api/newsfeedApi', () => ({
  newsfeedApi: { analyzeArticle: vi.fn(), updateArticle: vi.fn() },
}));

function setup() {
  const updateArticle = vi.fn();
  const updateArticleField = vi.fn();
  const { result } = renderHook(() => useArticleActions(updateArticle, updateArticleField));
  return { result, updateArticle, updateArticleField };
}

afterEach(() => vi.clearAllMocks());

describe('useArticleActions.handleAnalyze', () => {
  it.each([
    ['all', {}, false],
    ['all', { mitre_attack: { t: 1 } }, true],
    ['analysis', { mitre_attack: { t: 1 } }, false],
    ['analysis', { analysis_result: { s: 1 } }, true],
    ['mitre', { analysis_result: { s: 1 } }, false],
    ['mitre', { mitre_attack: { t: 1 } }, true],
  ])('mode %s with %j asks the backend to regenerate=%s', async (mode, existing, regen) => {
    newsfeedApi.analyzeArticle.mockResolvedValue({});
    const { result } = setup();
    await act(async () => result.current.handleAnalyze({ id: 5, ...existing }, mode));
    expect(newsfeedApi.analyzeArticle).toHaveBeenCalledWith(5, regen, mode);
  });

  it('parses a JSON-string analysis and normalizes an empty MITRE result to null', async () => {
    newsfeedApi.analyzeArticle.mockResolvedValue({ analysis_result: '{"summary":"x"}', mitre_attack: '' });
    const { result, updateArticle } = setup();
    await act(async () => result.current.handleAnalyze({ id: 1, title: 'a' }));
    expect(updateArticle).toHaveBeenCalledWith({
      id: 1, title: 'a', analysis_result: { summary: 'x' }, mitre_attack: null,
    });
    expect(result.current.analyzing).toEqual({ 1: false });
  });

  it('a failed analysis clears the spinner and leaves the article alone', async () => {
    newsfeedApi.analyzeArticle.mockRejectedValue(new Error('LLM down'));
    const { result, updateArticle } = setup();
    await act(async () => result.current.handleAnalyze({ id: 1 }));
    expect(updateArticle).not.toHaveBeenCalled();
    expect(result.current.analyzing).toEqual({ 1: false });
  });
});

describe('useArticleActions — TLP and notes', () => {
  it('TLP update sends note/read along so they are not wiped', async () => {
    newsfeedApi.updateArticle.mockResolvedValue({});
    const { result, updateArticleField } = setup();
    await act(async () => result.current.handleTlpUpdate({ id: 3, note: 'keep', read: true }, 'TLP:RED'));
    expect(newsfeedApi.updateArticle).toHaveBeenCalledWith(3, { tlp: 'TLP:RED', note: 'keep', read: true });
    expect(updateArticleField).toHaveBeenCalledWith(3, 'tlp', 'TLP:RED');
    expect(result.current.updatingTlp).toEqual({ 3: false });
  });

  it('failed TLP update does not change local state', async () => {
    newsfeedApi.updateArticle.mockRejectedValue(new Error('x'));
    const { result, updateArticleField } = setup();
    await act(async () => result.current.handleTlpUpdate({ id: 3 }, 'TLP:RED'));
    expect(updateArticleField).not.toHaveBeenCalled();
  });

  it('saving a note stores it and exits edit mode; deleting clears it', async () => {
    newsfeedApi.updateArticle.mockResolvedValue({});
    const { result, updateArticleField } = setup();
    await act(async () => result.current.handleNoteSave(4, 'hello'));
    expect(updateArticleField.mock.calls).toEqual([[4, 'note', 'hello'], [4, 'editNote', false]]);

    updateArticleField.mockClear();
    await act(async () => result.current.handleNoteDelete(4));
    expect(newsfeedApi.updateArticle).toHaveBeenLastCalledWith(4, { note: '' });
    expect(updateArticleField.mock.calls).toEqual([[4, 'note', '']]);
  });

  it('note errors leave local state untouched', async () => {
    newsfeedApi.updateArticle.mockRejectedValue(new Error('x'));
    const { result, updateArticleField } = setup();
    await act(async () => result.current.handleNoteSave(4, 'n'));
    await act(async () => result.current.handleNoteDelete(4));
    expect(updateArticleField).not.toHaveBeenCalled();
  });
});
