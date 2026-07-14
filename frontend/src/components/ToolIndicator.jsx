/**
 * =============================================================================
 * Tool Indicator Component
 * =============================================================================
 * This component displays the tools that were called during an AI response.
 * It appears as a floating card showing which tools were used and their status.
 * 
 * The 5 tools are color-coded for easy identification:
 * - log_interaction: Blue
 * - edit_interaction: Green
 * - extract_entities: Purple
 * - summarize_interaction: Orange
 * - suggest_follow_up: Cyan
 */

import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { selectShowToolIndicator, selectCurrentToolCalls, hideToolIndicator } from '../store/chatSlice';
import { FiX, FiFileText, FiEdit2, FiSearch, FiFile, FiClock } from 'react-icons/fi';

// =============================================================================
// Tool Configuration - Icons and colors for each tool
// =============================================================================
const TOOL_CONFIG = {
    log_interaction: {
        icon: FiFileText,
        label: 'Log Interaction',
        color: 'var(--tool-log)'
    },
    edit_interaction: {
        icon: FiEdit2,
        label: 'Edit Interaction',
        color: 'var(--tool-edit)'
    },
    extract_entities: {
        icon: FiSearch,
        label: 'Extract Entities',
        color: 'var(--tool-extract)'
    },
    summarize_interaction: {
        icon: FiFile,
        label: 'Summarize',
        color: 'var(--tool-summarize)'
    },
    suggest_follow_up: {
        icon: FiClock,
        label: 'Suggest Follow-up',
        color: 'var(--tool-followup)'
    }
};

// =============================================================================
// ToolIndicator Component
// =============================================================================
const ToolIndicator = () => {
    const dispatch = useDispatch();
    const showIndicator = useSelector(selectShowToolIndicator);
    const toolCalls = useSelector(selectCurrentToolCalls);
    
    // Don't render if not showing or no tool calls
    if (!showIndicator || !toolCalls || toolCalls.length === 0) {
        return null;
    }
    
    /**
     * Handle close button click
     */
    const handleClose = () => {
        dispatch(hideToolIndicator());
    };
    
    return (
        <div className="tool-indicator">
            {/* Header with title and close button */}
            <div className="tool-indicator-header">
                <h4>🛠️ Tools Used</h4>
                <button 
                    className="tool-indicator-close" 
                    onClick={handleClose}
                    aria-label="Close tool indicator"
                >
                    <FiX size={16} />
                </button>
            </div>
            
            {/* List of tools that were called */}
            <div className="tool-indicator-list">
                {toolCalls.map((toolCall, index) => {
                    const config = TOOL_CONFIG[toolCall.name] || {
                        icon: FiFileText,
                        label: toolCall.name,
                        color: 'var(--gray-500)'
                    };
                    const IconComponent = config.icon;
                    
                    return (
                        <div 
                            key={`${toolCall.name}-${index}`}
                            className={`tool-call-item tool-${toolCall.name}`}
                        >
                            {/* Tool icon with color background */}
                            <div 
                                className="tool-call-icon"
                                style={{ backgroundColor: config.color }}
                            >
                                <IconComponent size={14} />
                            </div>
                            
                            {/* Tool name */}
                            <span className="tool-call-name">
                                {config.label}
                            </span>
                            
                            {/* Status badge */}
                            <span className="tool-call-status">
                                ✓ Done
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ToolIndicator;