/**
 * =============================================================================
 * Chat Interface Component
 * =============================================================================
 * This is the main chat interface for interacting with the AI agent.
 * Users can type messages and the AI will respond, potentially calling
 * tools to log interactions, extract entities, etc.
 * 
 * Features:
 * - Real-time message display
 * - Typing indicator while AI is processing
 * - Tool call indicators showing which tools were used
 * - Auto-scroll to latest message
 * - Message history maintained in Redux
 */

import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
    selectMessages, 
    selectIsLoading, 
    selectChatHistory,
    addUserMessage, 
    sendMessage,
    clearChat
} from '../store/chatSlice';
import { FiSend, FiTrash2, FiMessageSquare, FiCpu, FiUser } from 'react-icons/fi';
import ToolIndicator from './ToolIndicator';

// =============================================================================
// ChatInterface Component
// =============================================================================
const ChatInterface = () => {
    const dispatch = useDispatch();
    
    // Get state from Redux
    const messages = useSelector(selectMessages);
    const isLoading = useSelector(selectIsLoading);
    const chatHistory = useSelector(selectChatHistory);
    
    // Local state for input
    const [inputValue, setInputValue] = useState('');
    
    // Ref for auto-scrolling and input focus
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    
    // =========================================================================
    // Auto-scroll to bottom when new messages arrive
    // =========================================================================
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
    
    // =========================================================================
    // Focus input on mount
    // =========================================================================
    useEffect(() => {
        inputRef.current?.focus();
    }, []);
    
    // =========================================================================
    // Handle form submission
    // =========================================================================
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Don't send empty messages
        const trimmedValue = inputValue.trim();
        if (!trimmedValue || isLoading) return;
        
        // Add user message to state
        dispatch(addUserMessage(trimmedValue));
        
        // Clear input
        setInputValue('');
        
        // Send message to AI agent
        dispatch(sendMessage({ 
            message: trimmedValue, 
            chatHistory: chatHistory.slice(0, -1) // Exclude the message we just added
        }));
    };
    
    // =========================================================================
    // Handle keyboard shortcut (Enter to send, Shift+Enter for new line)
    // =========================================================================
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };
    
    // =========================================================================
    // Handle clear chat
    // =========================================================================
    const handleClearChat = () => {
        if (window.confirm('Are you sure you want to clear the chat history?')) {
            dispatch(clearChat());
        }
    };
    
    // =========================================================================
    // Get avatar content based on message role
    // =========================================================================
    const getAvatarContent = (role) => {
        if (role === 'user') {
            return <FiUser size={18} />;
        }
        return <FiCpu size={18} />;
    };
    
    // =========================================================================
    // Render welcome message if no messages
    // =========================================================================
    const renderWelcomeMessage = () => (
        <div className="empty-state">
            <div className="empty-state-icon">
                <FiMessageSquare size={36} />
            </div>
            <h3>Welcome to HCP CRM AI Assistant</h3>
            <p>
                I can help you log interactions with Healthcare Professionals.
                Just describe your visit or conversation, and I'll extract the
                key information and create a proper interaction log.
            </p>
            <div style={{ marginTop: '24px', textAlign: 'left' }}>
                <p style={{ fontWeight: 500, marginBottom: '8px', color: 'var(--gray-700)' }}>
                    Try saying:
                </p>
                <ul style={{ 
                    listStyle: 'none', 
                    display: 'flex', 
                    flexDirection: 'column', 
                    gap: '8px' 
                }}>
                    {[
                        "I visited Dr. Sharma at Apollo Hospital today to discuss Cardioneo",
                        "Had a phone call with Dr. Patel about the new diabetes drug",
                        "Show me how to log an interaction with Dr. Gupta"
                    ].map((example, index) => (
                        <li 
                            key={index}
                            style={{
                                padding: '8px 16px',
                                background: 'var(--gray-100)',
                                borderRadius: 'var(--radius-md)',
                                fontSize: '0.875rem',
                                color: 'var(--gray-600)',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease'
                            }}
                            onClick={() => {
                                setInputValue(example);
                                inputRef.current?.focus();
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.background = 'var(--gray-200)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.background = 'var(--gray-100)';
                            }}
                        >
                            "{example}"
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
    
    // =========================================================================
    // Render a single message
    // =========================================================================
    const renderMessage = (message, index) => (
        <div 
            key={message.id || index} 
            className={`message ${message.role} ${message.isError ? 'error' : ''}`}
        >
            {/* Avatar */}
            <div className="message-avatar">
                {getAvatarContent(message.role)}
            </div>
            
            {/* Message bubble with optional tool calls */}
            <div className="message-bubble">
                {/* Main message content */}
                <div style={{ whiteSpace: 'pre-wrap' }}>
                    {message.content}
                </div>
                
                {/* Tool calls indicator (if any) */}
                {message.tool_calls && message.tool_calls.length > 0 && (
                    <div className="tool-calls-container">
                        <h4>Tools Used</h4>
                        {message.tool_calls.map((toolCall, tcIndex) => (
                            <div 
                                key={tcIndex}
                                className={`tool-call-item tool-${toolCall.name}`}
                            >
                                <span className="tool-call-name">
                                    ✓ {toolCall.name.replace(/_/g, ' ')}
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
    
    // =========================================================================
    // Render typing indicator
    // =========================================================================
    const renderTypingIndicator = () => (
        <div className="message assistant">
            <div className="message-avatar">
                <FiCpu size={18} />
            </div>
            <div className="message-bubble">
                <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    );
    
    // =========================================================================
    // Main render
    // =========================================================================
    return (
        <div className="chat-container">
            {/* Messages area */}
            <div className="chat-messages">
                {messages.length === 0 ? (
                    renderWelcomeMessage()
                ) : (
                    messages.map((message, index) => renderMessage(message, index))
                )}
                
                {/* Show typing indicator while loading */}
                {isLoading && renderTypingIndicator()}
                
                {/* Scroll anchor */}
                <div ref={messagesEndRef} />
            </div>
            
            {/* Input area */}
            <div className="chat-input-container">
                <form className="chat-input-wrapper" onSubmit={handleSubmit}>
                    <textarea
                        ref={inputRef}
                        className="chat-input"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Describe your HCP interaction..."
                        disabled={isLoading}
                        rows={1}
                    />
                    
                    <button 
                        type="submit" 
                        className="send-button"
                        disabled={!inputValue.trim() || isLoading}
                        aria-label="Send message"
                    >
                        {isLoading ? (
                            <div className="spinner" />
                        ) : (
                            <FiSend size={20} />
                        )}
                    </button>
                    
                    {/* Clear chat button */}
                    {messages.length > 0 && (
                        <button 
                            type="button"
                            onClick={handleClearChat}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'var(--gray-400)',
                                cursor: 'pointer',
                                padding: '8px',
                                borderRadius: 'var(--radius-md)',
                                transition: 'all 0.2s ease'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.color = 'var(--error)';
                                e.target.style.background = 'var(--error-light)';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.color = 'var(--gray-400)';
                                e.target.style.background = 'none';
                            }}
                            aria-label="Clear chat"
                            title="Clear chat history"
                        >
                            <FiTrash2 size={18} />
                        </button>
                    )}
                </form>
            </div>
            
            {/* Floating tool indicator */}
            <ToolIndicator />
        </div>
    );
};

export default ChatInterface;