import { render } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router';

// Every top-level scan feature owns its own nested <Routes> (index/new/history/settings), same
// as it's mounted in the real app (routes.jsx's `path="<feature>/*"`) — mounting it bare under
// MemoryRouter without this wrapping route fails to match anything, since its own `index` route
// only matches an empty relative path once nested under a `/*` parent.
export function renderFeatureRoute(Component, path, initialEntries) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path={`${path}/*`} element={<Component />} />
      </Routes>
    </MemoryRouter>,
  );
}
