/**
 * =============================================================================
 * Form Interface Component
 * =============================================================================
 * This component provides a structured form for manually logging HCP interactions.
 * It's an alternative to the chat interface for users who prefer form-based input.
 * 
 * Features:
 * - All required fields for interaction logging
 * - Validation for required fields
 * - Products discussed as comma-separated input
 * - Date and time pickers
 * - Submit and reset functionality
 * - Success/error notifications
 */

import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
    selectFormData, 
    selectIsSaving, 
    selectSuccessMessage, 
    selectInteractionError,
    updateFormField, 
    resetForm, 
    createInteraction,
    clearSuccessMessage,
    clearError
} from '../store/interactionSlice';
import { FiSave, FiX, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';

// =============================================================================
// Form field configuration for easier rendering
// =============================================================================
const FORM_SECTIONS = [
    {
        title: 'HCP Information',
        fields: [
            { name: 'hcp_name', label: 'HCP Name', type: 'text', required: true, placeholder: 'Dr. John Smith' },
            { name: 'specialty', label: 'Specialty', type: 'text', placeholder: 'Cardiology, Neurology, etc.' },
            { name: 'hospital_name', label: 'Hospital/Clinic', type: 'text', placeholder: 'Apollo Hospital' },
            { name: 'city', label: 'City', type: 'text', placeholder: 'Mumbai' }
        ]
    },
    {
        title: 'Interaction Details',
        fields: [
            { name: 'interaction_type', label: 'Interaction Type', type: 'select', required: true, options: [
                { value: 'visit', label: 'In-Person Visit' },
                { value: 'phone_call', label: 'Phone Call' },
                { value: 'email', label: 'Email' },
                { value: 'video_call', label: 'Video Call' },
                { value: 'conference', label: 'Conference' },
                { value: 'other', label: 'Other' }
            ]},
            { name: 'date', label: 'Date', type: 'date', required: true },
            { name: 'duration_minutes', label: 'Duration (minutes)', type: 'number', placeholder: '30' }
        ]
    },
    {
        title: 'Interaction Content',
        fields: [
            { name: 'summary', label: 'Summary', type: 'textarea', required: true, placeholder: 'Brief summary of the interaction...' },
            { name: 'key_discussions', label: 'Key Discussions', type: 'textarea', placeholder: 'Main topics discussed during the interaction...' },
            { name: 'products_discussed', label: 'Products Discussed', type: 'text', placeholder: 'Product A, Product B (comma separated)' },
            { name: 'hcp_feedback', label: 'HCP Feedback', type: 'textarea', placeholder: 'Any feedback or quotes from the HCP...' }
        ]
    },
    {
        title: 'Analysis & Follow-up',
        fields: [
            { name: 'hcp_sentiment', label: 'HCP Sentiment', type: 'select', options: [
                { value: 'positive', label: '😊 Positive' },
                { value: 'neutral', label: '😐 Neutral' },
                { value: 'negative', label: '😞 Negative' },
                { value: 'mixed', label: '🤔 Mixed' }
            ]},
            { name: 'follow_up_required', label: 'Follow-up Required', type: 'checkbox' },
            { name: 'follow_up_notes', label: 'Follow-up Notes', type: 'textarea', placeholder: 'Notes for follow-up action...' }
        ]
    }
];

// =============================================================================
// FormInterface Component
// =============================================================================
const FormInterface = () => {
    const dispatch = useDispatch();
    
    // Get state from Redux
    const formData = useSelector(selectFormData);
    const isSaving = useSelector(selectIsSaving);
    const successMessage = useSelector(selectSuccessMessage);
    const error = useSelector(selectInteractionError);
    
    // Local state for validation errors
    const [validationErrors, setValidationErrors] = useState({});
    
    // =========================================================================
    // Clear notifications after timeout
    // =========================================================================
    useEffect(() => {
        if (successMessage) {
            const timer = setTimeout(() => {
                dispatch(clearSuccessMessage());
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [successMessage, dispatch]);
    
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => {
                dispatch(clearError());
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [error, dispatch]);
    
    // =========================================================================
    // Handle field change
    // =========================================================================
    const handleFieldChange = (fieldName, value) => {
        dispatch(updateFormField({ field: fieldName, value }));
        
        // Clear validation error for this field if it exists
        if (validationErrors[fieldName]) {
            setValidationErrors(prev => ({
                ...prev,
                [fieldName]: null
            }));
        }
    };
    
    // =========================================================================
    // Validate form before submission
    // =========================================================================
    const validateForm = () => {
        const errors = {};
        
        if (!formData.hcp_name.trim()) {
            errors.hcp_name = 'HCP name is required';
        }
        
        if (!formData.interaction_type) {
            errors.interaction_type = 'Interaction type is required';
        }
        
        if (!formData.date) {
            errors.date = 'Date is required';
        }
        
        if (!formData.summary.trim()) {
            errors.summary = 'Summary is required';
        }
        
        setValidationErrors(errors);
        return Object.keys(errors).length === 0;
    };
    
    // =========================================================================
    // Handle form submission
    // =========================================================================
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Validate form
        if (!validateForm()) {
            return;
        }
        
        // Parse products discussed into array
        const productsArray = formData.products_discussed
            ? formData.products_discussed.split(',').map(p => p.trim()).filter(p => p)
            : [];
        
        // Prepare data for API
        const submitData = {
            ...formData,
            products_discussed: productsArray
        };
        
        // Dispatch create action
        const result = await dispatch(createInteraction(submitData));
        
        // If successful, show success and optionally reset form
        if (!result.error) {
            // Form is already reset in the reducer
        }
    };
    
    // =========================================================================
    // Handle form reset
    // =========================================================================
    const handleReset = () => {
        dispatch(resetForm());
        setValidationErrors({});
    };
    
    // =========================================================================
    // Render a single form field based on its type
    // =========================================================================
    const renderField = (field) => {
        const hasError = validationErrors[field.name];
        
        const commonProps = {
            id: field.name,
            value: formData[field.name] || '',
            onChange: (e) => {
                const value = field.type === 'checkbox' 
                    ? e.target.checked 
                    : e.target.value;
                handleFieldChange(field.name, value);
            },
            style: {
                borderColor: hasError ? 'var(--error)' : undefined
            }
        };
        
        switch (field.type) {
            case 'select':
                return (
                    <select {...commonProps}>
                        <option value="">Select...</option>
                        {field.options.map(opt => (
                            <option key={opt.value} value={opt.value}>
                                {opt.label}
                            </option>
                        ))}
                    </select>
                );
                
            case 'textarea':
                return (
                    <textarea 
                        {...commonProps} 
                        placeholder={field.placeholder}
                        rows={3}
                    />
                );
                
            case 'checkbox':
                return (
                    <div className="checkbox-group">
                        <input 
                            type="checkbox"
                            {...commonProps}
                            checked={formData[field.name] || false}
                        />
                        <label 
                            htmlFor={field.name}
                            style={{ 
                                fontWeight: 400, 
                                cursor: 'pointer',
                                color: 'var(--gray-600)'
                            }}
                        >
                            Yes
                        </label>
                    </div>
                );
                
            case 'number':
                return (
                    <input 
                        type="number"
                        {...commonProps}
                        placeholder={field.placeholder}
                        min="0"
                    />
                );
                
            default:
                return (
                    <input 
                        type={field.type}
                        {...commonProps}
                        placeholder={field.placeholder}
                    />
                );
        }
    };
    
    // =========================================================================
    // Render notification
    // =========================================================================
    const renderNotification = () => {
        if (successMessage) {
            return (
                <div className="notification success">
                    <FiCheckCircle size={20} />
                    {successMessage}
                </div>
            );
        }
        if (error) {
            return (
                <div className="notification error">
                    <FiAlertCircle size={20} />
                    {error}
                </div>
            );
        }
        return null;
    };
    
    // =========================================================================
    // Main render
    // =========================================================================
    return (
        <div className="form-container">
            {/* Notification */}
            {renderNotification()}
            
            <div className="form-card">
                {/* Form Header */}
                <div className="form-header">
                    <h2>Log HCP Interaction</h2>
                    <p>Fill in the details below to log a new interaction with a Healthcare Professional</p>
                </div>
                
                {/* Form */}
                <form onSubmit={handleSubmit}>
                    {FORM_SECTIONS.map((section, sectionIndex) => (
                        <div key={sectionIndex} style={{ marginBottom: '32px' }}>
                            {/* Section Title */}
                            <h3 style={{
                                fontSize: '1rem',
                                fontWeight: 600,
                                color: 'var(--gray-700)',
                                marginBottom: '16px',
                                paddingBottom: '8px',
                                borderBottom: '1px solid var(--gray-200)'
                            }}>
                                {section.title}
                            </h3>
                            
                            {/* Section Fields */}
                            <div className="form-grid">
                                {section.fields.map(field => (
                                    <div 
                                        key={field.name}
                                        className={`form-group ${field.type === 'textarea' ? 'full-width' : ''}`}
                                    >
                                        <label htmlFor={field.name}>
                                            {field.label}
                                            {field.required && <span className="required">*</span>}
                                        </label>
                                        
                                        {renderField(field)}
                                        
                                        {/* Validation error message */}
                                        {validationErrors[field.name] && (
                                            <span style={{
                                                fontSize: '0.8125rem',
                                                color: 'var(--error)',
                                                marginTop: '4px'
                                            }}>
                                                {validationErrors[field.name]}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                    
                    {/* Form Actions */}
                    <div className="form-actions">
                        <button 
                            type="button" 
                            className="btn btn-secondary"
                            onClick={handleReset}
                        >
                            <FiX size={16} />
                            Reset
                        </button>
                        
                        <button 
                            type="submit" 
                            className="btn btn-primary"
                            disabled={isSaving}
                        >
                            {isSaving ? (
                                <>
                                    <div className="spinner" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <FiSave size={16} />
                                    Save Interaction
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default FormInterface;