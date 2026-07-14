"""
==============================================================================
LangGraph Agent Tools Definition
==============================================================================
This module defines the 5 required tools for the HCP CRM AI agent.

Tools Overview:
1. log_interaction - Captures and saves interaction data
2. edit_interaction - Modifies existing interaction logs
3. extract_entities - Extracts key information from conversation
4. summarize_interaction - Generates professional summaries
5. suggest_follow_up - Recommends follow-up actions

Each tool is decorated with @tool from LangChain and includes:
- Clear docstrings (used by LLM to understand tool purpose)
- Type hints for parameters
- Proper error handling
- Integration with the database
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from langchain_groq import ChatGroq
import json

# Import prompts
from .prompts import (
    ENTITY_EXTRACTION_PROMPT,
    SUMMARIZATION_PROMPT,
    FOLLOW_UP_PROMPT
)

# Import database models (will be injected to avoid circular imports)
db = None
Interaction = None
HCP = None
llm = None


def init_tools(database, interaction_model, hcp_model, llm_instance):
    """
    Initialize tools with database and model references.
    
    This function is called during app initialization to inject
    dependencies into the tool functions.
    
    Args:
        database: SQLAlchemy db instance
        interaction_model: Interaction model class
        hcp_model: HCP model class
        llm_instance: ChatGroq LLM instance
    """
    global db, Interaction, HCP, llm
    db = database
    Interaction = interaction_model
    HCP = hcp_model
    llm = llm_instance



# =============================================================================
# TOOL 1: Log Interaction (MANDATORY)
# =============================================================================
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    summary: Optional[str] = "",
    key_discussions: Optional[str] = "",
    products_discussed: Optional[List[str]] = None,
    hcp_sentiment: Optional[str] = None,
    specialty: Optional[str] = None,
    hospital_name: Optional[str] = None,
    city: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    hcp_feedback: Optional[str] = None,
    follow_up_required: Optional[bool] = False,
    follow_up_notes: Optional[str] = None,
    channel: Optional[str] = None,
    logged_by: Optional[str] = "AI Assistant"
) -> Dict[str, Any]:
    """
    Log a new HCP (Healthcare Professional) interaction to the CRM database.
    
    REQUIRED fields (must have values):
    - hcp_name: Full name of the Healthcare Professional
    - interaction_type: Type - 'visit', 'phone_call', 'email', 'video_call', 'conference', 'other'
    - date: Date of interaction in ISO format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'
    
    OPTIONAL fields (can be null/empty - don't ask user for these):
    - summary: Professional summary of the interaction
    - key_discussions: Main topics discussed during interaction
    - products_discussed: List of pharmaceutical products mentioned (MUST be a list, not string)
    - hcp_sentiment: HCP's attitude - 'positive', 'neutral', 'negative', 'mixed'
    - specialty: Medical specialty (e.g., Cardiology, Neurology)
    - hospital_name: Name of hospital or clinic
    - city: City where HCP practices
    - duration_minutes: Duration of interaction in minutes
    - hcp_feedback: Direct feedback or quotes from HCP
    - follow_up_required: Whether follow-up is needed
    - follow_up_notes: Notes for follow-up action
    - channel: Communication channel used
    - logged_by: User who is logging the interaction
    
    IMPORTANT: For products_discussed, ALWAYS pass an empty list [] if no products mentioned.
    NEVER pass a string like "medicine products" - it MUST be a list.
    
    Returns:
        Dictionary with success status, interaction ID, and details
    """
    
    try:
        # ---------------------------------------------------------------------
        # Step 1: Validate/normalize required fields
        # ---------------------------------------------------------------------
        if not hcp_name:
            return {
                "success": False,
                "error": "Missing required field: hcp_name"
            }

        if not interaction_type:
            interaction_type = 'other'

        if not date:
            date = datetime.utcnow().strftime('%Y-%m-%d')

        # ---------------------------------------------------------------------
        # Step 2: Handle optional fields - normalize to safe defaults
        # ---------------------------------------------------------------------
        if summary is None:
            summary = ''
        if key_discussions is None:
            key_discussions = ''
        if hcp_sentiment is None:
            hcp_sentiment = None  # Keep as None, don't default to 'neutral'
        
        # CRITICAL: Ensure products_discussed is always a list, NEVER a string
        if products_discussed is None:
            products_discussed = []
        elif isinstance(products_discussed, str):
            # If LLM mistakenly passes a string, convert to list
            # But only if it's not a generic string like "medicine products"
            if products_discussed.strip() and products_discussed.strip() not in ['medicine products', 'products', 'none', 'n/a', '']:
                products_discussed = [products_discussed.strip()]
            else:
                products_discussed = []
        elif not isinstance(products_discussed, list):
            products_discussed = []
        
        # Filter out empty strings from products list
        products_discussed = [p for p in products_discussed if p and p.strip()]
        
        # Validate interaction type
        valid_types = ['visit', 'phone_call', 'email', 'video_call', 'conference', 'other']
        if interaction_type not in valid_types:
            interaction_type = 'other'
        
        # Validate sentiment only if provided
        if hcp_sentiment is not None:
            valid_sentiments = ['positive', 'neutral', 'negative', 'mixed']
            if hcp_sentiment not in valid_sentiments:
                hcp_sentiment = None  # Set to None instead of defaulting
        
        # ---------------------------------------------------------------------
        # Step 3: Parse the date
        # ---------------------------------------------------------------------
        try:
            interaction_date = datetime.strptime(date, '%Y-%m-%d %H:%M')
        except ValueError:
            try:
                interaction_date = datetime.strptime(date, '%Y-%m-%d')
                interaction_date = interaction_date.replace(hour=12, minute=0)
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid date format. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'"
                }
        
        # ---------------------------------------------------------------------
        # Step 4: Find or create HCP record
        # ---------------------------------------------------------------------
        hcp = HCP.query.filter_by(name=hcp_name).first()
        
        if not hcp:
            hcp = HCP(
                name=hcp_name,
                specialty=specialty,
                hospital_name=hospital_name,
                city=city
            )
            db.session.add(hcp)
            db.session.flush()
        
        # ---------------------------------------------------------------------
        # Step 5: Create the interaction record
        # ---------------------------------------------------------------------
        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=interaction_type,
            channel=channel or get_default_channel(interaction_type),
            date=interaction_date,
            duration_minutes=duration_minutes,
            summary=summary if summary else None,  # Store None instead of empty string
            key_discussions=key_discussions if key_discussions else None,
            products_discussed=products_discussed if products_discussed else None,
            hcp_feedback=hcp_feedback if hcp_feedback else None,
            hcp_sentiment=hcp_sentiment,  # Can be None
            follow_up_required=follow_up_required if follow_up_required else False,
            follow_up_notes=follow_up_notes if follow_up_notes else None,
            logged_by=logged_by
        )
        
        db.session.add(interaction)
        db.session.commit()
        
        # ---------------------------------------------------------------------
        # Step 6: Return success response
        # ---------------------------------------------------------------------
        return {
            "success": True,
            "message": "Interaction logged successfully",
            "interaction_id": interaction.id,
            "hcp_id": hcp.id,
            "data": interaction.to_dict()
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "error": f"Failed to log interaction: {str(e)}"
        }

def get_default_channel(interaction_type: str) -> str:
    """Helper function to determine default channel based on interaction type"""
    channel_map = {
        'visit': 'In-person',
        'phone_call': 'Phone',
        'email': 'Email',
        'video_call': 'Virtual',
        'conference': 'In-person',
        'other': 'Other'
    }
    return channel_map.get(interaction_type, 'Other')


# =============================================================================
# TOOL 2: Edit Interaction (MANDATORY)
# =============================================================================
@tool
def edit_interaction(
    interaction_id: int,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Edit an existing HCP interaction log in the CRM database.
    
    This tool allows modification of any field in an existing interaction record.
    Only the fields specified in 'updates' will be modified; other fields remain unchanged.
    
    Args:
        interaction_id: The ID of the interaction to edit (required)
        updates: Dictionary of fields to update. Valid fields include:
            - hcp_name: Update HCP name (will find/create new HCP)
            - interaction_type: 'visit', 'phone_call', 'email', 'video_call', 'conference', 'other'
            - date: New date in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM' format
            - summary: Updated summary
            - key_discussions: Updated discussion points
            - products_discussed: Updated list of products
            - hcp_sentiment: Updated sentiment
            - duration_minutes: Updated duration
            - hcp_feedback: Updated feedback
            - follow_up_required: Updated follow-up flag
            - follow_up_notes: Updated follow-up notes
            - next_action: Updated next action
    
    Returns:
        Dictionary with success status and updated interaction data
    """
    
    try:
        # ---------------------------------------------------------------------
        # Step 1: Find the interaction
        # ---------------------------------------------------------------------
        interaction = Interaction.query.get(interaction_id)
        
        if not interaction:
            return {
                "success": False,
                "error": f"Interaction with ID {interaction_id} not found"
            }
        
        # ---------------------------------------------------------------------
        # Step 2: Process each update field
        # ---------------------------------------------------------------------
        updated_fields = []  # Track what was changed
        
        for field, value in updates.items():
            if field == 'hcp_name':
                # Special handling for HCP name - need to find/create HCP
                hcp = HCP.query.filter_by(name=value).first()
                if not hcp:
                    hcp = HCP(name=value)
                    db.session.add(hcp)
                    db.session.flush()
                interaction.hcp_id = hcp.id
                updated_fields.append('hcp_name')
                
            elif field == 'date':
                # Parse date string
                try:
                    new_date = datetime.strptime(value, '%Y-%m-%d %H:%M')
                except ValueError:
                    try:
                        new_date = datetime.strptime(value, '%Y-%m-%d')
                        new_date = new_date.replace(hour=12, minute=0)
                    except ValueError:
                        continue  # Skip invalid date
                interaction.date = new_date
                updated_fields.append('date')
                
            elif field == 'interaction_type':
                valid_types = ['visit', 'phone_call', 'email', 'video_call', 'conference', 'other']
                if value in valid_types:
                    interaction.interaction_type = value
                    interaction.channel = get_default_channel(value)
                    updated_fields.append('interaction_type')
                    
            elif field == 'hcp_sentiment':
                valid_sentiments = ['positive', 'neutral', 'negative', 'mixed']
                if value in valid_sentiments:
                    interaction.hcp_sentiment = value
                    updated_fields.append('hcp_sentiment')
                    
            elif field == 'products_discussed':
                # Ensure it's a list
                if isinstance(value, str):
                    interaction.products_discussed = [value]
                elif isinstance(value, list):
                    interaction.products_discussed = value
                updated_fields.append('products_discussed')
                
            elif hasattr(interaction, field):
                # Generic handler for other fields
                setattr(interaction, field, value)
                updated_fields.append(field)
        
        # ---------------------------------------------------------------------
        # Step 3: Save changes and return response
        # ---------------------------------------------------------------------
        if updated_fields:
            interaction.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                "success": True,
                "message": f"Interaction updated successfully. Changed fields: {', '.join(updated_fields)}",
                "updated_fields": updated_fields,
                "data": interaction.to_dict()
            }
        else:
            return {
                "success": False,
                "error": "No valid fields to update"
            }
            
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "error": f"Failed to edit interaction: {str(e)}"
        }


# =============================================================================
# TOOL 3: Extract Entities
# =============================================================================
@tool
def extract_entities(interaction_description: str) -> Dict[str, Any]:
    """
    Extract key entities from an HCP interaction description.
    
    Args:
        interaction_description: Free-text description of the interaction.
    
    Returns:
        Dictionary containing extracted entities with hcp_name, interaction_date (YYYY-MM-DD),
        interaction_type, specialty, hospital_name, city, products_mentioned, etc.
    """
    
    try:
        # Get current date for context
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        extraction_prompt = f"""
        Today's date is: {today}
        
        {ENTITY_EXTRACTION_PROMPT}
        
        Interaction Description:
        {interaction_description}
        
        IMPORTANT: For interaction_date, parse any format to YYYY-MM-DD:
        - "13th july" → "2024-07-13" (use current year if not specified)
        - "july 13" → "2024-07-13"
        - "13/07" → "2024-07-13"
        - "yesterday" → calculate from today
        - "today" → {today}
        
        Respond with ONLY a valid JSON object, no other text.
        """
        
        response = llm.invoke(extraction_prompt)
        response_text = response.content
        
        # Clean up response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        entities = json.loads(response_text.strip())
        
        return {
            "success": True,
            "message": "Entities extracted successfully",
            "entities": entities
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse LLM response as JSON: {str(e)}",
            "raw_response": response_text if 'response_text' in locals() else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Entity extraction failed: {str(e)}"
        }
# =============================================================================
# TOOL 4: Summarize Interaction
# =============================================================================
@tool
def summarize_interaction(
    interaction_details: str,
    key_points: Optional[str] = None,
    products: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a professional summary of an HCP interaction.
    
    This tool uses the LLM to create a concise, professional summary
    suitable for CRM documentation.
    
    Args:
        interaction_details: Description of what happened during the interaction
        key_points: Optional comma-separated string of key discussion points
        products: Optional comma-separated string of products discussed
    
    Returns:
        Dictionary containing:
            - summary: Professional summary text (3-5 sentences)
            - key_discussions: Structured key discussion points
            - word_count: Number of words in summary
    """
    
    try:
        # ---------------------------------------------------------------------
        # Step 1: Build the summarization prompt
        # ---------------------------------------------------------------------
        additional_context = ""
        
        if key_points:
            additional_context += f"\nKey Points to Include: {key_points}"
        
        if products:
            additional_context += f"\nProducts Discussed: {products}"
        
        summary_prompt = f"""
        {SUMMARIZATION_PROMPT}
        
        Interaction Details:
        {interaction_details}
        {additional_context}
        
        Provide your response as a JSON object with:
        - "summary": The professional summary (3-5 sentences)
        - "key_discussions": A comma-separated string of key discussion points
        
        Respond with ONLY valid JSON, no other text.
        """
        
        # ---------------------------------------------------------------------
        # Step 2: Call LLM for summarization
        # ---------------------------------------------------------------------
        response = llm.invoke(summary_prompt)
        response_text = response.content
        
        # Clean up response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        # ---------------------------------------------------------------------
        # Step 3: Parse and return the summary
        # ---------------------------------------------------------------------
        result = json.loads(response_text.strip())
        
        return {
            "success": True,
            "message": "Summary generated successfully",
            "summary": result.get("summary", ""),
            "key_discussions": result.get("key_discussions", ""),
            "word_count": len(result.get("summary", "").split())
        }
        
    except json.JSONDecodeError as e:
        # If JSON parsing fails, return the raw text as summary
        return {
            "success": True,
            "message": "Summary generated (raw format)",
            "summary": response_text if 'response_text' in locals() else "Unable to generate summary",
            "key_discussions": "",
            "word_count": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Summarization failed: {str(e)}"
        }


# =============================================================================
# TOOL 5: Suggest Follow-up
# =============================================================================
@tool
def suggest_follow_up(
    interaction_summary: str,
    hcp_sentiment: str,
    products_discussed: Optional[str] = None,
    previous_interactions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest follow-up actions based on an HCP interaction.
    
    This tool analyzes the interaction context and recommends
    appropriate next steps for the field representative.
    
    Args:
        interaction_summary: Summary of the interaction
        hcp_sentiment: HCP's sentiment - 'positive', 'neutral', 'negative', 'mixed'
        products_discussed: Optional comma-separated string of products discussed
        previous_interactions: Optional context about past interactions
    
    Returns:
        Dictionary containing:
            - recommendations: List of follow-up recommendations
            - priority: Overall priority level
            - suggested_timeline: When to follow up
            - materials_needed: List of materials to prepare
    """
    
    try:
        # ---------------------------------------------------------------------
        # Step 1: Build the follow-up prompt
        # ---------------------------------------------------------------------
        products_context = ""
        if products_discussed:
            products_context = f"\nProducts Discussed: {products_discussed}"
        
        previous_context = ""
        if previous_interactions:
            previous_context = f"\nPrevious Interactions Context: {previous_interactions}"
        
        follow_up_prompt = f"""
        {FOLLOW_UP_PROMPT}
        
        Interaction Summary:
        {interaction_summary}
        
        HCP Sentiment: {hcp_sentiment}
        {products_context}
        {previous_context}
        
        Provide your response as a JSON object with:
        - "recommendations": Array of objects with "action", "timeline", "priority", "reasoning"
        - "overall_priority": "high", "medium", or "low"
        - "suggested_timeline": When the next follow-up should be
        - "materials_needed": Array of materials to prepare
        
        Respond with ONLY valid JSON, no other text.
        """
        
        # ---------------------------------------------------------------------
        # Step 2: Call LLM for recommendations
        # ---------------------------------------------------------------------
        response = llm.invoke(follow_up_prompt)
        response_text = response.content
        
        # Clean up response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        # ---------------------------------------------------------------------
        # Step 3: Parse and return recommendations
        # ---------------------------------------------------------------------
        recommendations = json.loads(response_text.strip())
        
        return {
            "success": True,
            "message": "Follow-up recommendations generated",
            "recommendations": recommendations.get("recommendations", []),
            "overall_priority": recommendations.get("overall_priority", "medium"),
            "suggested_timeline": recommendations.get("suggested_timeline", "1 week"),
            "materials_needed": recommendations.get("materials_needed", [])
        }
        
    except json.JSONDecodeError as e:
        # Fallback recommendations if parsing fails
        return {
            "success": True,
            "message": "Default recommendations generated",
            "recommendations": [
                {
                    "action": "Schedule follow-up call",
                    "timeline": "1 week",
                    "priority": "medium",
                    "reasoning": "Standard follow-up based on interaction"
                }
            ],
            "overall_priority": "medium",
            "suggested_timeline": "1 week",
            "materials_needed": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Follow-up suggestion failed: {str(e)}"
        }


# =============================================================================
# Export all tools for use in the agent
# =============================================================================
ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    extract_entities,
    summarize_interaction,
    suggest_follow_up
]