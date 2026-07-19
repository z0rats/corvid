import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider as JotaiProvider } from 'jotai';
import { BrowserRouter } from 'react-router-dom';

import '@fontsource/archivo/400.css';
import '@fontsource/archivo/500.css';
import '@fontsource/archivo/700.css';
import '@fontsource/jetbrains-mono/400.css';
import '@fontsource/jetbrains-mono/600.css';
import './core/config/index.css';
import './core/i18n';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <JotaiProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </JotaiProvider>
  </React.StrictMode>
);
