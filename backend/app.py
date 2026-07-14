"""
==============================================================================
Main Flask Application
==============================================================================
This is the entry point for the HCP CRM AI backend application.

It handles:
- Flask app initialization
- Database configuration
- AI Agent initialization
- Blueprint registration
- Error handlers

Run with: python app.py
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

# Import configuration
from config import Config

# Import database models
from models import db

# Import routes
from routes import api_bp

# Import agent
from agent import init_agent, init_tools
from models import HCP, Interaction


def create_app(config_class=Config) -> Flask:
    """
    ===========================================================================
    Application Factory
    ===========================================================================
    Creates and configures the Flask application.
    
    Using the factory pattern allows for:
    - Easy testing with different configurations
    - Multiple app instances if needed
    - Clean separation of configuration from creation
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Configured Flask application instance
    """
    
    # -------------------------------------------------------------------------
    # Step 1: Create Flask app
    # -------------------------------------------------------------------------
    app = Flask(__name__)
    
    # Load configuration from config class
    app.config.from_object(config_class)
    
    # -------------------------------------------------------------------------
    # Step 2: Enable CORS for frontend access
    # -------------------------------------------------------------------------
    # Allow requests from the React development server
    # Allow all localhost ports so Vite (5173), CRA (3000), or any dev server works
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # -------------------------------------------------------------------------
    # Step 3: Initialize Database
    # -------------------------------------------------------------------------
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        print("[OK] Database tables created/verified")
    
    # -------------------------------------------------------------------------
    # Step 4: Initialize AI Agent
    # -------------------------------------------------------------------------
    try:
        # Initialize the agent with Groq API key
        agent = init_agent(
            groq_api_key=app.config['GROQ_API_KEY'],
            model_name=app.config['GROQ_MODEL_PRIMARY']
        )
        
        # Initialize tools with database and models
        init_tools(
            database=db,
            interaction_model=Interaction,
            hcp_model=HCP,
            llm_instance=agent.llm
        )
        
        print("[OK] AI Agent initialized successfully")
        print(f"   Model: {app.config['GROQ_MODEL_PRIMARY']}")
    except Exception as e:
        print(f"[WARN] AI Agent initialization failed: {str(e)}")
        print("   Chat functionality will not be available")
    
    # -------------------------------------------------------------------------
    # Step 5: Register Blueprints (Routes)
    # -------------------------------------------------------------------------
    app.register_blueprint(api_bp)
    print("[OK] API routes registered")
    
    # -------------------------------------------------------------------------
    # Step 6: Register Error Handlers
    # -------------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            "success": False,
            "error": "Resource not found"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        tb = traceback.format_exc()
        print("[500 HANDLER]:", tb)
        return jsonify({
            "success": False,
            "error": str(error),
            "traceback": tb
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return jsonify({
            "success": False,
            "error": "Bad request"
        }), 400
    
    # -------------------------------------------------------------------------
    # Step 7: Add root route for API info
    # -------------------------------------------------------------------------
    @app.route('/')
    def index():
        """Root endpoint - API information"""
        return jsonify({
            "name": "HCP CRM AI API",
            "version": "1.0.0",
            "description": "AI-First CRM for Healthcare Professional Interactions",
            "endpoints": {
                "chat": "POST /api/chat",
                "interactions": "GET/POST /api/interactions",
                "interaction_detail": "GET/PUT/DELETE /api/interactions/<id>",
                "hcps": "GET/POST /api/hcps",
                "health": "GET /api/health"
            },
            "tools_available": [
                "log_interaction",
                "edit_interaction", 
                "extract_entities",
                "summarize_interaction",
                "suggest_follow_up"
            ]
        })
    
    return app


# =============================================================================
# Run the application
# =============================================================================
if __name__ == '__main__':
    """
    Main entry point when running the script directly.
    
    Usage:
        python app.py           # Run with default config
        FLASK_ENV=production python app.py  # Run with production config
    """
    
    # Determine which configuration to use
    env = os.getenv('FLASK_ENV', 'development')
    
    print("\n" + "="*60)
    print("HCP CRM AI Backend Server")
    print("="*60)
    print(f"   Environment: {env}")
    print("="*60 + "\n")
    
    # Create and run the app
    app = create_app()
    
    # Run the development server
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,
        debug=app.config.get('DEBUG', True)
    )