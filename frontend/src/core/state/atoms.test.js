import { createStore } from 'jotai';
import { apiKeysState, hasLlmKeyAtom, hasLocalLlmState } from './atoms';

function hasLlm({ keys = {}, local = false } = {}) {
  const store = createStore();
  store.set(apiKeysState, keys);
  store.set(hasLocalLlmState, local);
  return store.get(hasLlmKeyAtom);
}

describe('hasLlmKeyAtom', () => {
  it('is false with no provider key and no local model', () => {
    expect(hasLlm()).toBe(false);
    expect(hasLlm({ keys: { shodan: true } })).toBe(false);
  });

  it('is true with an OpenAI or Anthropic key', () => {
    expect(hasLlm({ keys: { openai: true } })).toBe(true);
    expect(hasLlm({ keys: { anthropic: true } })).toBe(true);
  });

  it('is true with only a local Ollama model and no keys at all', () => {
    expect(hasLlm({ local: true })).toBe(true);
  });
});
