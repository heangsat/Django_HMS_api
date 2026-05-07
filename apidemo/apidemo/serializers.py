"""
Serializer module for converting model instances to dictionaries.
Handles foreign key relationships and date/time formatting.
"""
from decimal import Decimal
from datetime import date, datetime


def serialize_model_instance(instance):
    """Convert a single model instance to a dictionary."""
    data = {}
    for field in instance._meta.fields:
        key = field.name
        value = getattr(instance, key, None)
        
        # Handle foreign key fields
        if field.is_relation:
            # Use the primary key value for ForeignKey/OneToOneField
            data[key] = getattr(instance, field.attname, None)
        # Handle date and datetime fields
        elif isinstance(value, (date, datetime)):
            data[key] = value.isoformat() if value else None
        # Handle Decimal fields
        elif isinstance(value, Decimal):
            data[key] = float(value) if value else None
        else:
            data[key] = value
    
    return data


def serialize_model_queryset(queryset):
    """Convert a queryset to a list of dictionaries."""
    return [serialize_model_instance(obj) for obj in queryset]


def serialize_model_with_relations(instance, related_models=None):
    """
    Serialize instance with option to include related models.
    
    Args:
        instance: Model instance to serialize
        related_models: Dict mapping field names to model classes to include
        
    Example:
        serialize_model_with_relations(doctor, {'deptid': 'department'})
    """
    data = serialize_model_instance(instance)
    
    if related_models:
        for field_name, model_class in related_models.items():
            if hasattr(instance, field_name):
                related_obj = getattr(instance, field_name)
                if related_obj:
                    data[f"{field_name}_details"] = serialize_model_instance(related_obj)
    
    return data
