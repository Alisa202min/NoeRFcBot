"""
ماژول فرمت‌کننده داده‌های کالبک
این ماژول برای ایجاد و تجزیه داده‌های کالبک به صورت یکپارچه استفاده می‌شود.
"""

import re
from typing import Optional, Tuple, Dict, Any
from configuration import (
    PRODUCT_PREFIX, SERVICE_PREFIX, EDUCATION_PREFIX, INQUIRY_PREFIX, 
    CATEGORY_PREFIX, BACK_PREFIX
)

class CallbackFormatter:
    """Class to format and parse callback data"""
    
    # Define callback patterns and their types
    CALLBACK_PATTERNS = [
        # Static callbacks
        {
            'type': 'products',
            'pattern': re.compile(r'^products$'),
            'params': {}
        },
        {
            'type': 'services',
            'pattern': re.compile(r'^services$'),
            'params': {}
        },
        {
            'type': 'contact',
            'pattern': re.compile(r'^contact$'),
            'params': {}
        },
        {
            'type': 'about',
            'pattern': re.compile(r'^about$'),
            'params': {}
        },
        {
            'type': 'educational',
            'pattern': re.compile(r'^educational$'),
            'params': {}
        },
        {
            'type': 'back_to_main',
            'pattern': re.compile(r'^back_to_main$'),
            'params': {}
        },
        {
            'type': 'confirm_inquiry',
            'pattern': re.compile(r'^confirm_inquiry$'),
            'params': {}
        },
        {
            'type': 'cancel_inquiry',
            'pattern': re.compile(r'^cancel_inquiry$'),
            'params': {}
        },
        # Dynamic callbacks with prefixes
        {
            'type': 'product_category',
            'pattern': re.compile(rf'^{PRODUCT_PREFIX}_cat_(\d+)$'),  # e.g., product_cat_2
            'params': {'category_id': int}
        },
        {
            'type': 'service_category',
            'pattern': re.compile(rf'^{SERVICE_PREFIX}_cat_(\d+)$'),  # e.g., service_cat_2
            'params': {'category_id': int}
        },
        {
            'type': 'edu_category',
            'pattern': re.compile(rf'^{EDUCATION_PREFIX}_cat_(\d+)$'),  # e.g., edu_cat_2
            'params': {'category_id': int}
        },
        {
            'type': 'edu_categories',
            'pattern': re.compile(rf'^{EDUCATION_PREFIX}categories$'),
            'params': {}
        },
        {
            'type': 'edu_content',
            'pattern': re.compile(rf'^{EDUCATION_PREFIX}:(\d+)$'),  # e.g., edu:123
            'params': {'content_id': int}
        },
        {
            'type': 'category',
            'pattern': re.compile(rf'^{CATEGORY_PREFIX}:(\d+)$'),  # e.g., category:2
            'params': {'category_id': int}
        },
        {
            'type': 'product_item',
            'pattern': re.compile(rf'^{PRODUCT_PREFIX}:(\d+)$'),  # e.g., product:123
            'params': {'product_id': int}
        },
        {
            'type': 'service_item',
            'pattern': re.compile(rf'^{SERVICE_PREFIX}:(\d+)$'),  # e.g., service:123
            'params': {'service_id': int}
        },
        {
            'type': 'inquiry',
            'pattern': re.compile(rf'^{INQUIRY_PREFIX}:(\w+):(\d+)$'),  # e.g., inquiry:product:123
            'params': {'inquiry_type': str, 'item_id': int}
        },
        {
            'type': 'back',
            'pattern': re.compile(rf'^{BACK_PREFIX}_(\w+)_(\d+)$'),  # e.g., back_product_123
            'params': {'type': str, 'id': int}
        }
    ]
    
    def __init__(self):
        """Initialize formatter with callback patterns"""
        self.pattern_map = {p['type']: p for p in self.CALLBACK_PATTERNS}
    
    def write(self, callback_type: str, **kwargs) -> str:
        """
        Format callback data for sending
        
        Args:
            callback_type: Type of callback (e.g., 'product_category', 'back_to_main')
            **kwargs: Parameters required for the callback type (e.g., category_id)
            
        Returns:
            Formatted callback data (e.g., 'product_cat_2')
            
        Raises:
            ValueError: If callback_type is invalid or required params are missing
        """
        if callback_type not in self.pattern_map:
            raise ValueError(f"Invalid callback type: {callback_type}")
        
        pattern_info = self.pattern_map[callback_type]
        params = pattern_info['params']
        
        # Validate required parameters
        for param_name, param_type in params.items():
            if param_name not in kwargs:
                raise ValueError(f"Missing required parameter: {param_name} for {callback_type}")
            if not isinstance(kwargs[param_name], param_type):
                raise ValueError(f"Invalid type for {param_name}: expected {param_type}, got {type(kwargs[param_name])}")
        
        # Generate callback data based on type
        if callback_type == 'product_category':
            return f"{PRODUCT_PREFIX}_cat_{kwargs['category_id']}"
        elif callback_type == 'service_category':
            return f"{SERVICE_PREFIX}_cat_{kwargs['category_id']}"
        elif callback_type == 'edu_category':
            return f"{EDUCATION_PREFIX}_cat_{kwargs['category_id']}"
        elif callback_type == 'edu_categories':
            return f"{EDUCATION_PREFIX}categories"
        elif callback_type == 'edu_content':
            return f"{EDUCATION_PREFIX}:{kwargs['content_id']}"
        elif callback_type == 'category':
            return f"{CATEGORY_PREFIX}:{kwargs['category_id']}"
        elif callback_type == 'product_item':
            return f"{PRODUCT_PREFIX}:{kwargs['product_id']}"
        elif callback_type == 'service_item':
            return f"{SERVICE_PREFIX}:{kwargs['service_id']}"
        elif callback_type == 'inquiry':
            return f"{INQUIRY_PREFIX}:{kwargs['inquiry_type']}:{kwargs['item_id']}"
        elif callback_type == 'back':
            return f"{BACK_PREFIX}_{kwargs['type']}_{kwargs['id']}"
        else:
            # Static callbacks
            return callback_type
    
    def read(self, callback_data: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Parse callback data and extract type and parameters
        
        Args:
            callback_data: Raw callback data (e.g., 'product_cat_2')
            
        Returns:
            Tuple of (callback_type, params_dict) if matched, else None
        """
        for pattern_info in self.CALLBACK_PATTERNS:
            match = pattern_info['pattern'].match(callback_data)
            if match:
                callback_type = pattern_info['type']
                params = {}
                param_names = list(pattern_info['params'].keys())
                for i, (param_name, param_type) in enumerate(pattern_info['params'].items(), 1):
                    if i <= len(match.groups()):
                        params[param_name] = param_type(match.group(i))
                return callback_type, params
        return None

# Singleton instance for use across the application
callback_formatter = CallbackFormatter()