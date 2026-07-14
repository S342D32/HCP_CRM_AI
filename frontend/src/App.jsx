/**
 * App.jsx - Root Application Component
 * ============================================================================
 * Layout:
 * ┌──────────────────────────────────────────────────────┐
 * │                     APP HEADER                        │
 * ├──────────────────────┬───────────────────────────────┤
 * │   FORM  (1 part)     │      AI CHAT  (3 parts)        │
 * │   left panel         │      right panel               │
 * └──────────────────────┴───────────────────────────────┘
 *
 * Both panels are always visible — no tabs needed.
 * The form fills 1/4 of the width, chat fills 3/4.
 */

import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { fetchInteractions } from './store/interactionSlice';
import { FiActivity } from 'react-icons/fi';

import ChatInterface from './components/ChatInterface';
import FormInterface from './components/FormInterface';

const App = () => {
    const dispatch = useDispatch();

    // Load interactions on startup so Redux has fresh data
    useEffect(() => {
        dispatch(fetchInteractions());
    }, [dispatch]);

    return (
        <div className="app-container">

            {/* ── HEADER ─────────────────────────────────────────── */}
            <header className="app-header">
                <div className="logo">
                    <FiActivity size={24} color="var(--primary-500)" />
                    <div>
                        <h1>HCP CRM AI</h1>
                        <span>Healthcare Professional Interaction Manager</span>
                    </div>
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--gray-500)' }}>
                    Powered by LangGraph + Groq
                </div>
            </header>

            {/* ── BODY: Form (left 1) + Chat (right 3) ───────────── */}
            <div className="app-body">

                {/* Left panel — manual form, takes 1 part */}
                <div className="panel-form">
                    <div className="panel-label">Log Interaction (Form)</div>
                    <FormInterface />
                </div>

                {/* Divider line between panels */}
                <div className="panel-divider" />

                {/* Right panel — AI chat, takes 3 parts */}
                <div className="panel-chat">
                    <div className="panel-label">AI Chat Assistant</div>
                    <ChatInterface />
                </div>

            </div>
        </div>
    );
};

export default App;
