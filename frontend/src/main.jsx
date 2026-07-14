/**
 * main.jsx - Application Entry Point
 *
 * This is where React mounts to the DOM.
 * We wrap everything in <Provider> so every component
 * can access the Redux store (chat state, interaction state, etc.)
 */

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import store from './store/index';
import App from './App.jsx';

// Import global styles (CSS variables, layout, components)
import './styles/global.css';

createRoot(document.getElementById('root')).render(
    <StrictMode>
        {/* Provider makes the Redux store available to the entire app */}
        <Provider store={store}>
            <App />
        </Provider>
    </StrictMode>
);
