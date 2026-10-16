import { createStore } from 'jotai';
import { apiKeysState, llmAvailableAtom, availableLlmModelsState } from './atoms';

function hasLlm({ keys = {}, local = false } = {}) {
  const store = createStore();
  store.set(apiKeysState, keys);
  store.set(availableLlmModelsState, local ? [{ id: 'ollama:llava', name: 'llava', provider: 'Ollama (local)' }] : []);
  return store.get(llmAvailableAtom);
}

describe('llmAvailableAtom', () => {
  it('is false with no provider key and no local model', () => {
    expect(hasLlm()).toBe(false);
    expect(hasLlm({ keys: { shodan: true } })).toBe(false);
  });

  it('is true with an OpenAI or Anthropic key', () => {
    expect(hasLlm({ keys: { openai: true } })).toBe(true);
    expect(hasLlm({ keys: { anthropic: true } })).toBe(true);
  });

  it('is true with only a registry model (e.g. local Ollama) and no keys at all', () => {
    expect(hasLlm({ local: true })).toBe(true);
  });
});
