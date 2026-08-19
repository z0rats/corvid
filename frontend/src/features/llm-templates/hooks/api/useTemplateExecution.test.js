import { act, renderHook } from '@testing-library/react';
import { useTemplateExecution } from './useTemplateExecution';
import { templatesApi } from '../../services/api/templatesApi';

vi.mock('../../services/api/templatesApi');

describe('useTemplateExecution', () => {
  afterEach(() => vi.clearAllMocks());

  it('sends the payload, model, and temperature overrides when present on the template', async () => {
    templatesApi.executeTemplate.mockResolvedValue({ result: 'the answer' });
    const { result } = renderHook(() => useTemplateExecution());
    const template = { id: 't1', model: 'gpt-4o', temperature: 0.3 };

    await act(async () => {
      await result.current.executeTemplate(template, { logs: 'x' });
    });

    expect(templatesApi.executeTemplate).toHaveBeenCalledWith('t1', {
      template_id: 't1',
      payload_data: { logs: 'x' },
      override_model: 'gpt-4o',
      override_temperature: 0.3,
    });
  });

  it('omits the override fields when the template has no model/temperature set', async () => {
    templatesApi.executeTemplate.mockResolvedValue({ result: 'ok' });
    const { result } = renderHook(() => useTemplateExecution());

    await act(async () => {
      await result.current.executeTemplate({ id: 't1' }, {});
    });

    expect(templatesApi.executeTemplate).toHaveBeenCalledWith('t1', {
      template_id: 't1',
      payload_data: {},
    });
  });

  it('stores the LLM result and toggles executing back off', async () => {
    templatesApi.executeTemplate.mockResolvedValue({ result: 'the llm result' });
    const { result } = renderHook(() => useTemplateExecution());

    let promise;
    act(() => {
      promise = result.current.executeTemplate({ id: 't1' }, {});
    });
    expect(result.current.executing).toBe(true);

    await act(async () => {
      await promise;
    });

    expect(result.current.executing).toBe(false);
    expect(result.current.result).toBe('the llm result');
  });

  it('turns executing back off even when the API call fails, and rethrows', async () => {
    templatesApi.executeTemplate.mockRejectedValue(new Error('execution failed'));
    const { result } = renderHook(() => useTemplateExecution());

    await expect(
      act(async () => {
        await result.current.executeTemplate({ id: 't1' }, {});
      }),
    ).rejects.toThrow('execution failed');

    expect(result.current.executing).toBe(false);
  });

  it('clearResult resets the stored result', async () => {
    templatesApi.executeTemplate.mockResolvedValue({ result: 'something' });
    const { result } = renderHook(() => useTemplateExecution());

    await act(async () => {
      await result.current.executeTemplate({ id: 't1' }, {});
    });
    expect(result.current.result).toBe('something');

    act(() => result.current.clearResult());
    expect(result.current.result).toBe('');
  });
});
