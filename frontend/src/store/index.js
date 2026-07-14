/**
 * =============================================================================
 * Redux Store Configuration
 * =============================================================================
 * This file configures the Redux store with all slices combined.
 * It's the central state management hub for the application.
 */

import { configureStore } from '@reduxjs/toolkit';
import chatReducer from './chatSlice';
import interactionReducer from './interactionSlice';

// =============================================================================
// Store Configuration
// =============================================================================
const store = configureStore({
    // Combine all reducers
    reducer: {
        chat: chatReducer,
        interactions: interactionReducer
    },
    
    // Middleware configuration (Redux Toolkit includes redux-thunk by default)
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            // Disable serializable check for our specific cases
            // (Tool results may contain non-serializable data)
            serializableCheck: {
                ignoredActions: [
                    'chat/sendMessage/fulfilled'
                ],
                ignoredPaths: [
                    'chat.currentToolResults',
                    'chat.messages[].tool_results'
                ]
            }
        }),
    
    // Enable Redux DevTools in development
    devTools: process.env.NODE_ENV !== 'production'
});

// =============================================================================
// Export Store
// =============================================================================
export default store;