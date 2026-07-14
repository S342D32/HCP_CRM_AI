"""
==============================================================================
Interaction Database Models
==============================================================================
This module defines the database schema for HCP (Healthcare Professional)
interactions. It uses SQLAlchemy ORM for database operations.

Key Entities:
- Interaction: Main table for logged interactions
- HCP: Healthcare Professional information
- Product: Products discussed during interactions
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Enum, Float, JSON, Boolean
)
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance (will be configured in app.py)
db = SQLAlchemy()


class HCP(db.Model):
    """
    ===========================================================================
    Healthcare Professional Model
    ===========================================================================
    Stores information about doctors, pharmacists, and other healthcare
    professionals that field representatives interact with.
    
    Attributes:
        id: Unique identifier
        name: Full name of the HCP
        specialty: Medical specialty (e.g., Cardiology, Neurology)
        qualification: Medical qualification (e.g., MD, MBBS)
        hospital_name: Name of the hospital/clinic
        city: City where they practice
        email: Contact email (optional)
        phone: Contact phone (optional)
        interactions: Relationship to logged interactions
    """
    
    __tablename__ = 'hcps'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    specialty = Column(String(100))
    qualification = Column(String(100))
    hospital_name = Column(String(255))
    city = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship: One HCP can have many interactions
    interactions = relationship('Interaction', back_populates='hcp', lazy='dynamic')
    
    def to_dict(self):
        """Convert HCP object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'qualification': self.qualification,
            'hospital_name': self.hospital_name,
            'city': self.city,
            'email': self.email,
            'phone': self.phone
        }


class Interaction(db.Model):
    """
    ===========================================================================
    Interaction Model
    ===========================================================================
    Core model for logging interactions between field representatives
    and Healthcare Professionals.
    
    Attributes:
        id: Unique identifier
        hcp_id: Foreign key to HCP table
        interaction_type: Type of interaction (visit, call, email, etc.)
        channel: How the interaction occurred
        date: When the interaction happened
        duration_minutes: Duration of interaction in minutes
        summary: AI-generated summary of the interaction
        key_discussions: Main topics discussed
        products_discussed: Products mentioned (JSON array)
        hcp_feedback: Feedback or responses from HCP
        hcp_sentiment: Overall sentiment (positive, neutral, negative)
        follow_up_required: Whether follow-up is needed
        follow_up_notes: Notes for follow-up
        next_action: Planned next action
        logged_by: User who logged the interaction
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last modified
        hcp: Relationship to HCP model
    """
    
    __tablename__ = 'interactions'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign key to HCP
    hcp_id = Column(Integer, ForeignKey('hcps.id'), nullable=False)
    
    # Interaction details
    interaction_type = Column(
        Enum('visit', 'phone_call', 'email', 'video_call', 'conference', 'other',
             name='interaction_type_enum'),
        default='visit',
        nullable=False
    )
    
    channel = Column(String(50))  # In-person, Virtual, Phone, etc.
    
    date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    
    # AI-enhanced fields
    summary = Column(Text)  # LLM-generated summary
    key_discussions = Column(Text)  # Main discussion points
    products_discussed = Column(JSON)  # Array of product names
    hcp_feedback = Column(Text)
    
    # Sentiment analysis result from LLM
    hcp_sentiment = Column(
        Enum('positive', 'neutral', 'negative', 'mixed',
             name='sentiment_enum'),
        default='neutral'
    )
    
    # Follow-up information
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    follow_up_date = Column(DateTime)
    next_action = Column(Text)
    
    # Metadata
    logged_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to HCP
    hcp = relationship('HCP', back_populates='interactions')
    
    def to_dict(self):
        """
        Convert Interaction object to dictionary for JSON serialization.
        Includes nested HCP information for convenience.
        """
        return {
            'id': self.id,
            'hcp_id': self.hcp_id,
            'hcp': self.hcp.to_dict() if self.hcp else None,
            'interaction_type': self.interaction_type,
            'channel': self.channel,
            'date': self.date.isoformat() if self.date else None,
            'duration_minutes': self.duration_minutes,
            'summary': self.summary,
            'key_discussions': self.key_discussions,
            'products_discussed': self.products_discussed,
            'hcp_feedback': self.hcp_feedback,
            'hcp_sentiment': self.hcp_sentiment,
            'follow_up_required': self.follow_up_required,
            'follow_up_notes': self.follow_up_notes,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'next_action': self.next_action,
            'logged_by': self.logged_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


