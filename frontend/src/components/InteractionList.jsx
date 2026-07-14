/**
 * InteractionList.jsx - Sidebar Component
 * ============================================================================
 * Shows the history of all logged HCP interactions in the left sidebar.
 *
 * Each card shows:
 * - HCP name
 * - Interaction type badge
 * - Date (formatted as "Today", "Yesterday", "3 days ago", etc.)
 * - A colored dot showing the sentiment (green=positive, red=negative, etc.)
 *
 * Clicking a card sets it as the "current interaction" in Redux state.
 * The active card is highlighted with a blue left border.
 */

import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
    selectInteractions,
    selectIsLoading,
    selectCurrentInteraction,
    setCurrentInteraction
} from '../store/interactionSlice';
import { FiMessageCircle, FiCalendar } from 'react-icons/fi';

// =============================================================================
// Sentiment dot colors - maps sentiment value to a CSS color variable
// =============================================================================
const SENTIMENT_COLORS = {
    positive: 'var(--sentiment-positive)',   // green
    neutral: 'var(--sentiment-neutral)',     // gray
    negative: 'var(--sentiment-negative)',   // red
    mixed: 'var(--sentiment-mixed)'          // yellow/orange
};

// =============================================================================
// InteractionList Component
// =============================================================================
const InteractionList = () => {
    const dispatch = useDispatch();

    // Pull data from Redux store
    const interactions = useSelector(selectInteractions);
    const isLoading = useSelector(selectIsLoading);
    const currentInteraction = useSelector(selectCurrentInteraction);

    // =========================================================================
    // Handle clicking on an interaction card
    // =========================================================================
    const handleCardClick = (interaction) => {
        // Store the selected interaction in Redux so other components can use it
        dispatch(setCurrentInteraction(interaction));
    };

    // =========================================================================
    // Format date into a human-friendly string
    // e.g. "Today", "Yesterday", "3 days ago", "Jan 5"
    // =========================================================================
    const formatDate = (dateString) => {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;

        // For older dates, show "Jan 5" or "Jan 5, 2023" if different year
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    };

    // =========================================================================
    // Format interaction type for display
    // "phone_call" -> "phone call"
    // =========================================================================
    const formatType = (type) => {
        if (!type) return '';
        return type.replace(/_/g, ' ');
    };

    // =========================================================================
    // Empty state - shown when no interactions exist yet
    // =========================================================================
    if (!isLoading && interactions.length === 0) {
        return (
            <div className="sidebar">
                <div className="sidebar-header">
                    <h2>Interaction History</h2>
                </div>
                <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--gray-500)' }}>
                    <FiMessageCircle size={32} style={{ marginBottom: '12px', opacity: 0.5 }} />
                    <p style={{ fontSize: '0.875rem' }}>No interactions logged yet</p>
                    <p style={{ fontSize: '0.8125rem', marginTop: '4px' }}>
                        Use the chat or form to log your first interaction
                    </p>
                </div>
            </div>
        );
    }

    // =========================================================================
    // Loading state
    // =========================================================================
    if (isLoading) {
        return (
            <div className="sidebar">
                <div className="sidebar-header">
                    <h2>Interaction History</h2>
                </div>
                <div style={{ padding: '24px', textAlign: 'center' }}>
                    <div className="spinner" style={{ margin: '0 auto' }} />
                    <p style={{ fontSize: '0.875rem', color: 'var(--gray-500)', marginTop: '12px' }}>
                        Loading...
                    </p>
                </div>
            </div>
        );
    }

    // =========================================================================
    // Main render - list of interaction cards
    // =========================================================================
    return (
        <div className="sidebar">
            {/* Sidebar header */}
            <div className="sidebar-header">
                <h2>Interaction History</h2>
                <span style={{ fontSize: '0.8125rem', color: 'var(--gray-500)' }}>
                    {interactions.length} interaction{interactions.length !== 1 ? 's' : ''}
                </span>
            </div>

            {/* Scrollable list of cards */}
            <div className="sidebar-list">
                {interactions.map((interaction) => {
                    // Check if this card is the currently selected one
                    const isActive = currentInteraction?.id === interaction.id;

                    return (
                        <div
                            key={interaction.id}
                            className={`interaction-card ${isActive ? 'active' : ''}`}
                            onClick={() => handleCardClick(interaction)}
                        >
                            {/* Card top row: HCP name + type badge */}
                            <div className="card-header">
                                <span className="hcp-name">
                                    {interaction.hcp?.name || 'Unknown HCP'}
                                </span>
                                <span className="card-type">
                                    {formatType(interaction.interaction_type)}
                                </span>
                            </div>

                            {/* Card bottom row: date + sentiment dot */}
                            <div
                                className="card-date"
                                style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
                            >
                                <FiCalendar size={12} />
                                <span>{formatDate(interaction.date)}</span>

                                {/* Colored dot showing HCP sentiment */}
                                <span
                                    style={{
                                        marginLeft: 'auto',
                                        width: '8px',
                                        height: '8px',
                                        borderRadius: '50%',
                                        backgroundColor:
                                            SENTIMENT_COLORS[interaction.hcp_sentiment] ||
                                            'var(--gray-400)',
                                        flexShrink: 0
                                    }}
                                    title={`Sentiment: ${interaction.hcp_sentiment || 'unknown'}`}
                                />
                            </div>

                            {/* Optional summary preview (truncated) */}
                            {interaction.summary && (
                                <div className="card-summary">
                                    {interaction.summary}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default InteractionList;
