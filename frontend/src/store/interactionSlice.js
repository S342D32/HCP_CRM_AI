/**
 * =============================================================================
 * Interaction Slice - Redux State Management for Interactions
 * =============================================================================
 * This slice manages the state for HCP interactions including:
 * - List of interactions
 * - Current interaction being viewed/edited
 * - Form state for new/edit interaction
 * - Loading and error states
 * - Pagination
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { interactionAPI, hcpAPI } from '../services/api';

// =============================================================================
// Async Thunks
// =============================================================================

/**
 * Fetch all interactions with optional filters
 */
export const fetchInteractions = createAsyncThunk(
    'interactions/fetchAll',
    async (params, { rejectWithValue }) => {
        try {
            const response = await interactionAPI.getAll(params);
            return response;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

/**
 * Fetch a single interaction by ID
 */
export const fetchInteractionById = createAsyncThunk(
    'interactions/fetchById',
    async (id, { rejectWithValue }) => {
        try {
            const response = await interactionAPI.getById(id);
            return response;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

/**
 * Create a new interaction
 */
export const createInteraction = createAsyncThunk(
    'interactions/create',
    async (data, { rejectWithValue }) => {
        try {
            const response = await interactionAPI.create(data);
            return response;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

/**
 * Update an existing interaction
 */
export const updateInteraction = createAsyncThunk(
    'interactions/update',
    async ({ id, data }, { rejectWithValue }) => {
        try {
            const response = await interactionAPI.update(id, data);
            return response;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

/**
 * Delete an interaction
 */
export const deleteInteraction = createAsyncThunk(
    'interactions/delete',
    async (id, { rejectWithValue }) => {
        try {
            await interactionAPI.delete(id);
            return id;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

/**
 * Fetch all HCPs
 */
export const fetchHCPs = createAsyncThunk(
    'interactions/fetchHCPs',
    async (_, { rejectWithValue }) => {
        try {
            const response = await hcpAPI.getAll();
            return response;
        } catch (error) {
            return rejectWithValue(error.message);
        }
    }
);

// =============================================================================
// Initial Form State
// =============================================================================
const initialFormState = {
    hcp_name: '',
    specialty: '',
    hospital_name: '',
    city: '',
    interaction_type: 'visit',
    channel: 'In-person',
    date: new Date().toISOString().split('T')[0],
    duration_minutes: '',
    summary: '',
    key_discussions: '',
    products_discussed: '',
    hcp_feedback: '',
    hcp_sentiment: 'neutral',
    follow_up_required: false,
    follow_up_notes: '',
    logged_by: ''
};

// =============================================================================
// Initial State
// =============================================================================
const initialState = {
    // List of interactions
    interactions: [],
    
    // Pagination info
    pagination: {
        page: 1,
        per_page: 10,
        total: 0,
        pages: 0,
        has_next: false,
        has_prev: false
    },
    
    // Current interaction being viewed
    currentInteraction: null,
    
    // Form state
    formData: { ...initialFormState },
    
    // HCPs list for dropdown
    hcps: [],
    
    // Loading states
    isLoading: false,
    isSaving: false,
    isLoadingHCPs: false,
    
    // Error state
    error: null,
    
    // Success message
    successMessage: null,
    
    // View mode: 'list', 'form', 'chat'
    viewMode: 'chat'
};

// =============================================================================
// Interaction Slice Definition
// =============================================================================
const interactionSlice = createSlice({
    name: 'interactions',
    initialState,
    reducers: {
        /**
         * Update a single field in the form
         */
        updateFormField: (state, action) => {
            const { field, value } = action.payload;
            state.formData[field] = value;
        },
        
        /**
         * Reset form to initial state
         */
        resetForm: (state) => {
            state.formData = { ...initialFormState };
        },
        
        /**
         * Set form data from an existing interaction (for editing)
         */
        setFormData: (state, action) => {
            const interaction = action.payload;
            
            // Map interaction data to form fields
            state.formData = {
                hcp_name: interaction.hcp?.name || '',
                specialty: interaction.hcp?.specialty || '',
                hospital_name: interaction.hcp?.hospital_name || '',
                city: interaction.hcp?.city || '',
                interaction_type: interaction.interaction_type || 'visit',
                channel: interaction.channel || 'In-person',
                date: interaction.date ? interaction.date.split('T')[0] : '',
                duration_minutes: interaction.duration_minutes || '',
                summary: interaction.summary || '',
                key_discussions: interaction.key_discussions || '',
                products_discussed: interaction.products_discussed?.join(', ') || '',
                hcp_feedback: interaction.hcp_feedback || '',
                hcp_sentiment: interaction.hcp_sentiment || 'neutral',
                follow_up_required: interaction.follow_up_required || false,
                follow_up_notes: interaction.follow_up_notes || '',
                logged_by: interaction.logged_by || ''
            };
        },
        
        /**
         * Set the current interaction being viewed
         */
        setCurrentInteraction: (state, action) => {
            state.currentInteraction = action.payload;
        },
        
        /**
         * Change the view mode
         */
        setViewMode: (state, action) => {
            state.viewMode = action.payload;
        },
        
        /**
         * Clear error state
         */
        clearError: (state) => {
            state.error = null;
        },
        
        /**
         * Clear success message
         */
        clearSuccessMessage: (state) => {
            state.successMessage = null;
        },
        
        /**
         * Set pagination page
         */
        setPage: (state, action) => {
            state.pagination.page = action.payload;
        }
    },
    
    extraReducers: (builder) => {
        // ---------------------------------------------------------------------
        // fetchInteractions
        // ---------------------------------------------------------------------
        builder.addCase(fetchInteractions.pending, (state) => {
            state.isLoading = true;
            state.error = null;
        });
        builder.addCase(fetchInteractions.fulfilled, (state, action) => {
            state.isLoading = false;
            state.interactions = action.payload.data;
            state.pagination = action.payload.pagination;
        });
        builder.addCase(fetchInteractions.rejected, (state, action) => {
            state.isLoading = false;
            state.error = action.payload;
        });
        
        // ---------------------------------------------------------------------
        // fetchInteractionById
        // ---------------------------------------------------------------------
        builder.addCase(fetchInteractionById.pending, (state) => {
            state.isLoading = true;
        });
        builder.addCase(fetchInteractionById.fulfilled, (state, action) => {
            state.isLoading = false;
            state.currentInteraction = action.payload.data;
        });
        builder.addCase(fetchInteractionById.rejected, (state, action) => {
            state.isLoading = false;
            state.error = action.payload;
        });
        
        // ---------------------------------------------------------------------
        // createInteraction
        // ---------------------------------------------------------------------
        builder.addCase(createInteraction.pending, (state) => {
            state.isSaving = true;
            state.error = null;
        });
        builder.addCase(createInteraction.fulfilled, (state, action) => {
            state.isSaving = false;
            state.successMessage = 'Interaction created successfully!';
            state.formData = { ...initialFormState };
            
            // Add to the beginning of the list
            if (action.payload.data) {
                state.interactions.unshift(action.payload.data);
            }
        });
        builder.addCase(createInteraction.rejected, (state, action) => {
            state.isSaving = false;
            state.error = action.payload;
        });
        
        // ---------------------------------------------------------------------
        // updateInteraction
        // ---------------------------------------------------------------------
        builder.addCase(updateInteraction.pending, (state) => {
            state.isSaving = true;
            state.error = null;
        });
        builder.addCase(updateInteraction.fulfilled, (state, action) => {
            state.isSaving = false;
            state.successMessage = 'Interaction updated successfully!';
            state.currentInteraction = action.payload.data;
            
            // Update in the list
            const index = state.interactions.findIndex(
                i => i.id === action.payload.data.id
            );
            if (index !== -1) {
                state.interactions[index] = action.payload.data;
            }
        });
        builder.addCase(updateInteraction.rejected, (state, action) => {
            state.isSaving = false;
            state.error = action.payload;
        });
        
        // ---------------------------------------------------------------------
        // deleteInteraction
        // ---------------------------------------------------------------------
        builder.addCase(deleteInteraction.fulfilled, (state, action) => {
            // Remove from the list
            state.interactions = state.interactions.filter(
                i => i.id !== action.payload
            );
            state.successMessage = 'Interaction deleted successfully';
        });
        builder.addCase(deleteInteraction.rejected, (state, action) => {
            state.error = action.payload;
        });
        
        // ---------------------------------------------------------------------
        // fetchHCPs
        // ---------------------------------------------------------------------
        builder.addCase(fetchHCPs.pending, (state) => {
            state.isLoadingHCPs = true;
        });
        builder.addCase(fetchHCPs.fulfilled, (state, action) => {
            state.isLoadingHCPs = false;
            state.hcps = action.payload.data;
        });
        builder.addCase(fetchHCPs.rejected, (state, action) => {
            state.isLoadingHCPs = false;
            state.error = action.payload;
        });
    }
});

// =============================================================================
// Export Actions
// =============================================================================
export const {
    updateFormField,
    resetForm,
    setFormData,
    setCurrentInteraction,
    setViewMode,
    clearError,
    clearSuccessMessage,
    setPage
} = interactionSlice.actions;

// =============================================================================
// Export Selectors
// =============================================================================
export const selectInteractions = (state) => state.interactions.interactions;
export const selectPagination = (state) => state.interactions.pagination;
export const selectCurrentInteraction = (state) => state.interactions.currentInteraction;
export const selectFormData = (state) => state.interactions.formData;
export const selectHCPs = (state) => state.interactions.hcps;
export const selectIsLoading = (state) => state.interactions.isLoading;
export const selectIsSaving = (state) => state.interactions.isSaving;
export const selectInteractionError = (state) => state.interactions.error;
export const selectSuccessMessage = (state) => state.interactions.successMessage;
export const selectViewMode = (state) => state.interactions.viewMode;

// =============================================================================
// Export Reducer
// =============================================================================
export default interactionSlice.reducer;