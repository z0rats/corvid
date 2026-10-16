import { render, screen, fireEvent, within } from '@testing-library/react';
import { Provider, createStore } from 'jotai';
import { MemoryRouter } from 'react-router';
import CreateTemplateForm from './CreateTemplateForm';
import { availableLlmModelsState } from '../../../../core/state/atoms';

// The rich-text editor doesn't render in jsdom and isn't what this test is about.
vi.mock('@mdxeditor/editor', () => {
  const plugin = () => ({});
  return {
    MDXEditor: () => null,
    headingsPlugin: plugin, listsPlugin: plugin, quotePlugin: plugin, thematicBreakPlugin: plugin,
    markdownShortcutPlugin: plugin, codeBlockPlugin: plugin, codeMirrorPlugin: plugin, toolbarPlugin: plugin,
    BoldItalicUnderlineToggles: () => null, StrikeThroughSupSubToggles: () => null, ListsToggle: () => null,
    BlockTypeSelect: () => null, InsertThematicBreak: () => null, InsertCodeBlock: () => null,
  };
});
vi.mock('@mdxeditor/editor/style.css', () => ({}));
vi.mock('../../hooks/api/useCategories', () => ({ useCategories: () => ({ categories: [] }) }));

describe('CreateTemplateForm model picker', () => {
  it('lists the backend registry, including local Ollama models', () => {
    const store = createStore();
    store.set(availableLlmModelsState, [
      { id: 'gpt-5', name: 'GPT-5', provider: 'OpenAI' },
      { id: 'ollama:llava', name: 'llava', provider: 'Ollama (local)' },
    ]);
    render(
      <Provider store={store}>
        <MemoryRouter><CreateTemplateForm /></MemoryRouter>
      </Provider>,
    );

    fireEvent.mouseDown(screen.getAllByRole('combobox')[0]);
    const listbox = screen.getByRole('listbox');

    expect(within(listbox).getByRole('option', { name: 'llava' })).toBeInTheDocument();
    expect(within(listbox).getByRole('option', { name: 'GPT-5' })).toBeInTheDocument();
    expect(within(listbox).getByText('Ollama (local)')).toBeInTheDocument();
  });
});
