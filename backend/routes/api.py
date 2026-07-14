"""
API Routes Module
==============================================================================
"""

import traceback
from flask import Blueprint, request, jsonify
from datetime import datetime

from models import db, HCP, Interaction
from agent import get_agent

api_bp = Blueprint('api', __name__, url_prefix='/api')


# =============================================================================
# Chat Endpoint
# =============================================================================
@api_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        print(f"[CHAT] Received: {data}")

        if not data or 'message' not in data:
            return jsonify({"success": False, "error": "Message is required"}), 400

        message = data['message']
        chat_history = data.get('chat_history', [])
        print(f"[CHAT] Message: {message}")
        print(f"[CHAT] History length: {len(chat_history)}")

        agent = get_agent()
        if not agent:
            print("[CHAT] ERROR: Agent is None - not initialized")
            return jsonify({"success": False, "error": "AI agent not initialized"}), 500

        print("[CHAT] Running agent...")
        result = agent.run(message, chat_history)
        print(f"[CHAT] Agent result keys: {list(result.keys())}")

        return jsonify({
            "success": True,
            "response": result["response"],
            "tool_calls": result["tool_calls"],
            "tool_results": result["tool_results"]
        })

    except Exception as e:
        # Print full traceback so we see exactly which line failed
        print(f"[CHAT] EXCEPTION: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": f"{type(e).__name__}: {str(e)}"}), 500


# =============================================================================
# Interaction Endpoints
# =============================================================================
@api_bp.route('/interactions', methods=['GET'])
def get_interactions():
    """
    ===========================================================================
    List Interactions Endpoint
    ===========================================================================
    Get a paginated list of all logged interactions.
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10)
    - hcp_id: Filter by HCP ID
    - interaction_type: Filter by type
    - sentiment: Filter by sentiment
    - date_from: Filter from date (YYYY-MM-DD)
    - date_to: Filter to date (YYYY-MM-DD)
    """
    try:
        # ---------------------------------------------------------------------
        # Step 1: Get query parameters with defaults
        # ---------------------------------------------------------------------
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        hcp_id = request.args.get('hcp_id', type=int)
        interaction_type = request.args.get('interaction_type')
        sentiment = request.args.get('sentiment')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # ---------------------------------------------------------------------
        # Step 2: Build query with filters
        # ---------------------------------------------------------------------
        query = Interaction.query.join(HCP)
        
        if hcp_id:
            query = query.filter(Interaction.hcp_id == hcp_id)
        
        if interaction_type:
            query = query.filter(Interaction.interaction_type == interaction_type)
        
        if sentiment:
            query = query.filter(Interaction.hcp_sentiment == sentiment)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Interaction.date >= from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                to_date = to_date.replace(hour=23, minute=59, second=59)
                query = query.filter(Interaction.date <= to_date)
            except ValueError:
                pass
        
        # Order by most recent first
        query = query.order_by(Interaction.date.desc())
        
        # ---------------------------------------------------------------------
        # Step 3: Paginate and return results
        # ---------------------------------------------------------------------
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            "success": True,
            "data": [interaction.to_dict() for interaction in pagination.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/interactions/<int:interaction_id>', methods=['GET'])
def get_interaction(interaction_id):
    """
    ===========================================================================
    Get Single Interaction Endpoint
    ===========================================================================
    Retrieve a specific interaction by ID.
    """
    try:
        interaction = Interaction.query.get(interaction_id)
        
        if not interaction:
            return jsonify({
                "success": False,
                "error": "Interaction not found"
            }), 404
        
        return jsonify({
            "success": True,
            "data": interaction.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/interactions', methods=['POST'])
def create_interaction():
    """
    ===========================================================================
    Create Interaction Endpoint (Form Submission)
    ===========================================================================
    Directly create an interaction from form data (without AI agent).
    
    Request Body: All interaction fields
    """
    try:
        data = request.get_json()
        
        # ---------------------------------------------------------------------
        # Step 1: Validate required fields
        # ---------------------------------------------------------------------
        required_fields = ['hcp_name', 'interaction_type', 'date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # ---------------------------------------------------------------------
        # Step 2: Find or create HCP
        # ---------------------------------------------------------------------
        hcp = HCP.query.filter_by(name=data['hcp_name']).first()
        
        if not hcp:
            hcp = HCP(
                name=data['hcp_name'],
                specialty=data.get('specialty'),
                hospital_name=data.get('hospital_name'),
                city=data.get('city')
            )
            db.session.add(hcp)
            db.session.flush()
        
        # ---------------------------------------------------------------------
        # Step 3: Parse date
        # ---------------------------------------------------------------------
        try:
            interaction_date = datetime.strptime(data['date'], '%Y-%m-%d')
            interaction_date = interaction_date.replace(hour=12, minute=0)
        except ValueError:
            try:
                interaction_date = datetime.strptime(data['date'], '%Y-%m-%d %H:%M')
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid date format"
                }), 400
        
        # ---------------------------------------------------------------------
        # Step 4: Create interaction
        # ---------------------------------------------------------------------
        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=data['interaction_type'],
            channel=data.get('channel'),
            date=interaction_date,
            duration_minutes=data.get('duration_minutes'),
            summary=data.get('summary'),
            key_discussions=data.get('key_discussions'),
            products_discussed=data.get('products_discussed', []),
            hcp_feedback=data.get('hcp_feedback'),
            hcp_sentiment=data.get('hcp_sentiment', 'neutral'),
            follow_up_required=data.get('follow_up_required', False),
            follow_up_notes=data.get('follow_up_notes'),
            logged_by=data.get('logged_by', 'Manual Entry')
        )
        
        db.session.add(interaction)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Interaction created successfully",
            "data": interaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/interactions/<int:interaction_id>', methods=['PUT'])
def update_interaction(interaction_id):
    """
    ===========================================================================
    Update Interaction Endpoint
    ===========================================================================
    Update an existing interaction.
    """
    try:
        interaction = Interaction.query.get(interaction_id)
        
        if not interaction:
            return jsonify({
                "success": False,
                "error": "Interaction not found"
            }), 404
        
        data = request.get_json()
        
        # ---------------------------------------------------------------------
        # Step 1: Update each provided field
        # ---------------------------------------------------------------------
        updatable_fields = [
            'interaction_type', 'channel', 'date', 'duration_minutes',
            'summary', 'key_discussions', 'products_discussed',
            'hcp_feedback', 'hcp_sentiment', 'follow_up_required',
            'follow_up_notes', 'next_action'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'date':
                    try:
                        new_date = datetime.strptime(data['date'], '%Y-%m-%d')
                        setattr(interaction, field, new_date)
                    except ValueError:
                        pass
                else:
                    setattr(interaction, field, data[field])
        
        interaction.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Interaction updated successfully",
            "data": interaction.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/interactions/<int:interaction_id>', methods=['DELETE'])
def delete_interaction(interaction_id):
    """
    ===========================================================================
    Delete Interaction Endpoint
    ===========================================================================
    Delete an interaction by ID.
    """
    try:
        interaction = Interaction.query.get(interaction_id)
        
        if not interaction:
            return jsonify({
                "success": False,
                "error": "Interaction not found"
            }), 404
        
        db.session.delete(interaction)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Interaction deleted successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =============================================================================
# HCP Endpoints
# =============================================================================
@api_bp.route('/hcps', methods=['GET'])
def get_hcps():
    """
    ===========================================================================
    List HCPs Endpoint
    ===========================================================================
    Get a list of all Healthcare Professionals.
    """
    try:
        hcps = HCP.query.order_by(HCP.name).all()
        
        return jsonify({
            "success": True,
            "data": [hcp.to_dict() for hcp in hcps]
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_bp.route('/hcps', methods=['POST'])
def create_hcp():
    """
    ===========================================================================
    Create HCP Endpoint
    ===========================================================================
    Add a new Healthcare Professional.
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({
                "success": False,
                "error": "HCP name is required"
            }), 400
        
        hcp = HCP(
            name=data['name'],
            specialty=data.get('specialty'),
            qualification=data.get('qualification'),
            hospital_name=data.get('hospital_name'),
            city=data.get('city'),
            email=data.get('email'),
            phone=data.get('phone')
        )
        
        db.session.add(hcp)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "HCP created successfully",
            "data": hcp.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =============================================================================
# Health Check Endpoint
# =============================================================================
@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    ===========================================================================
    Health Check Endpoint
    ===========================================================================
    Simple endpoint to verify the API is running.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })