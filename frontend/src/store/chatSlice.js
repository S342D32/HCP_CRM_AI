/**
 * =============================================================================
 * Chat Slice - Redux State Management for Chat
 * =============================================================================
 * This slice manages the state for the AI chat interface including:
 * - Chat messages (user and assistant)
 * - Loading state while waiting for AI response
 * - Tool calls and their results
 * - Error handling
 */

import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { chatAPI } from '../services/api';
import { fetchInteractions, updateFormField } from './interactionSlice';

// =============================================================================
// Async Thunks - Async operations with Redux
// =============================================================================

/**
 * Send message to AI and get response
 * This is an async thunk that handles the API call and updates state
 */
export const sendMessage = createAsyncThunk(
    'chat/sendMessage',
    async ({ message, chatHistory }, { rejectWithValue, dispatch }) => {
        try {
            const response = await chatAPI.sendMessage(message, chatHistory);
            
            const toolNames = (response.tool_calls || []).map(tc => tc.name);

            // Fill the form with whatever fields the AI has collected so far
            const formFillTool = (response.tool_calls || []).find(
                tc => tc.name === 'log_interaction' || tc.name === 'extract_entities'
            );
            if (formFillTool) {
                let args = {};

                if (formFillTool.name === 'extract_entities') {
                    // Parse entities from tool result
                    try {
                        const raw = (response.tool_results || []).find(r => r.tool === 'extract_entities')?.result;
                        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
                        const entities = parsed?.entities || {};
                        args = {
                            hcp_name: entities.hcp_name,
                            specialty: entities.specialty,
                            hospital_name: entities.hospital_name,
                            city: entities.city,
                            date: entities.interaction_date,
                            duration_minutes: entities.duration,
                            products_discussed: entities.products_mentioned,
                        };
                    } catch { args = {}; }
                } else {
                    args = formFillTool.args;
                }

                const fieldMap = {
                    hcp_name: args.hcp_name,
                    specialty: args.specialty,
                    hospital_name: args.hospital_name,
                    city: args.city,
                    interaction_type: args.interaction_type,
                    date: args.date,
                    duration_minutes: args.duration_minutes,
                    summary: args.summary,
                    key_discussions: args.key_discussions,
                    products_discussed: Array.isArray(args.products_discussed)
                        ? args.products_discussed.join(', ')
                        : (args.products_discussed || ''),
                    hcp_feedback: args.hcp_feedback,
                    hcp_sentiment: args.hcp_sentiment,
                    follow_up_required: args.follow_up_required,
                    follow_up_notes: args.follow_up_notes,
                };

                Object.entries(fieldMap).forEach(([field, value]) => {
                    if (value !== undefined && value !== null && value !== '') {
                        dispatch(updateFormField({ field, value }));
                    }
                });
            }

            // Refresh interaction list after logging/editing
            if (toolNames.includes('log_interaction') || toolNames.includes('edit_interaction')) {
                dispatch(fetchInteractions());
            }
            
            return response;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

// =============================================================================
// Initial State
// =============================================================================
const initialState = {
    // Array of chat messages
    messages: [],
    
    // Loading state
    isLoading: false,
    
    // Error message if any
    error: null,
    
    // Tool calls from the current response
    currentToolCalls: [],
    
    // Tool results from the current response
    currentToolResults: [],
    
    // Whether to show tool indicators
    showToolIndicator: false
};

// =============================================================================
// Chat Slice Definition
// =============================================================================
const chatSlice = createSlice({
    name: 'chat',
    initialState,
    reducers: {
        /**
         * Add a user message to the chat
         */
        addUserMessage: (state, action) => {
            state.messages.push({
                id: Date.now(),
                role: 'user',
                content: action.payload,
                timestamp: new Date().toISOString()
            });
        },
        
        /**
         * Add an assistant message to the chat
         */
        addAssistantMessage: (state, action) => {
            state.messages.push({
                id: Date.now(),
                role: 'assistant',
                content: action.payload,
                timestamp: new Date().toISOString()
            });
        },
        
        /**
         * Clear all chat messages
         */
        clearChat: (state) => {
            state.messages = [];
            state.error = null;
            state.currentToolCalls = [];
            state.currentToolResults = [];
        },
        
        /**
         * Clear error state
         */
        clearError: (state) => {
            state.error = null;
        },
        
        /**
         * Hide tool indicator
         */
        hideToolIndicator: (state) => {
            state.showToolIndicator = false;
        }
    },
    
    extraReducers: (builder) => {
        // ---------------------------------------------------------------------
        // Handle sendMessage async thunk states
        // ---------------------------------------------------------------------
        
        // When the API call starts
        builder.addCase(sendMessage.pending, (state) => {
            state.isLoading = true;
            state.error = null;
            state.showToolIndicator = false;
        });
        
        // When the API call succeeds
        builder.addCase(sendMessage.fulfilled, (state, action) => {
            state.isLoading = false;
            
            const { response, tool_calls, tool_results } = action.payload;
            
            // Add assistant response to messages
            state.messages.push({
                id: Date.now(),
                role: 'assistant',
                content: response,
                timestamp: new Date().toISOString(),
                tool_calls: tool_calls,
                tool_results: tool_results
            });
            
            // Store current tool info for display
            state.currentToolCalls = tool_calls || [];
            state.currentToolResults = tool_results || [];
            
            // Show tool indicator if tools were used
            state.showToolIndicator = tool_calls && tool_calls.length > 0;
        });
        
        // When the API call fails
        builder.addCase(sendMessage.rejected, (state, action) => {
            state.isLoading = false;
            state.error = action.payload || 'Failed to send message';
            
            // Add error as assistant message
            state.messages.push({
                id: Date.now(),
                role: 'assistant',
                content: `Sorry, I encountered an error: ${state.error}`,
                timestamp: new Date().toISOString(),
                isError: true
            });
        });
    }
});

// =============================================================================
// Export Actions
// =============================================================================
export const {
    addUserMessage,
    addAssistantMessage,
    clearChat,
    clearError,
    hideToolIndicator
} = chatSlice.actions;

// =============================================================================
// Export Selectors
// =============================================================================
export const selectMessages = (state) => state.chat.messages;
export const selectIsLoading = (state) => state.chat.isLoading;
export const selectChatError = (state) => state.chat.error;
export const selectCurrentToolCalls = (state) => state.chat.currentToolCalls;
export const selectCurrentToolResults = (state) => state.chat.currentToolResults;
export const selectShowToolIndicator = (state) => state.chat.showToolIndicator;

// =============================================================================
// Export Chat History for API (formatted for backend)
// =============================================================================
// Using createSelector so the mapped array is only recomputed when messages
// actually change — prevents the "returned a different result" Redux warning
import { createSelector } from '@reduxjs/toolkit';

export const selectChatHistory = createSelector(
    (state) => state.chat.messages,
    (messages) => messages.map(msg => ({
        role: msg.role,
        content: msg.content
    }))
);

// =============================================================================
// Export Reducer
// =============================================================================
export default chatSlice.reducer;