from typing import Dict, Any, List, Optional
from datetime import datetime
import re


def translate_value(value: Any, mapping: Dict[str, str]) -> str:
    if value is None:
        return ""
    
    str_value = str(value)
    return mapping.get(str_value, str_value)


def format_date(value: Any, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    if value is None:
        return ""
    
    if isinstance(value, datetime):
        return value.strftime(format_str)
    
    if isinstance(value, str):
        try:
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.strftime(format_str)
                except ValueError:
                    continue
        except Exception:
            pass
    
    return str(value)


def format_number(value: Any, decimal_places: int = 2, thousands_separator: str = ",") -> str:
    if value is None:
        return ""
    
    try:
        num = float(value)
        
        if decimal_places > 0:
            formatted = f"{num:,.{decimal_places}f}"
        else:
            formatted = f"{int(num):,}"
        
        if thousands_separator != ",":
            formatted = formatted.replace(",", thousands_separator)
        
        return formatted
    except (ValueError, TypeError):
        return str(value)


def format_boolean(value: Any, true_text: str = "是", false_text: str = "否") -> str:
    if value is None:
        return ""
    
    if isinstance(value, bool):
        return true_text if value else false_text
    
    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ["true", "1", "yes", "on"]:
            return true_text
        elif lower_value in ["false", "0", "no", "off"]:
            return false_text
    
    if isinstance(value, (int, float)):
        return true_text if value else false_text
    
    return str(value)


def format_url(value: Any, as_link: bool = True) -> str:
    if value is None:
        return ""
    
    str_value = str(value)
    
    if re.match(r'^https?://', str_value):
        if as_link:
            return f'<a href="{str_value}" target="_blank">{str_value}</a>'
        return str_value
    
    return str_value


def format_file_size(value: Any) -> str:
    if value is None:
        return ""
    
    try:
        size = int(value)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}" if unit != 'B' else f"{size} {unit}"
            size /= 1024
        
        return f"{size:.2f} PB"
    except (ValueError, TypeError):
        return str(value)


def format_duration(value: Any) -> str:
    if value is None:
        return ""
    
    try:
        seconds = float(value)
        
        if seconds < 1:
            return f"{seconds * 1000:.0f} ms"
        elif seconds < 60:
            return f"{seconds:.2f} s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} min"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} h"
    except (ValueError, TypeError):
        return str(value)


def apply_format(value: Any, format_type: str, options: Optional[Dict[str, Any]] = None) -> str:
    options = options or {}
    
    formatters = {
        "date": lambda v: format_date(v, options.get("format", "%Y-%m-%d %H:%M:%S")),
        "number": lambda v: format_number(v, options.get("decimal_places", 2), options.get("thousands_separator", ",")),
        "boolean": lambda v: format_boolean(v, options.get("true_text", "是"), options.get("false_text", "否")),
        "url": lambda v: format_url(v, options.get("as_link", True)),
        "file_size": format_file_size,
        "duration": format_duration,
        "translate": lambda v: translate_value(v, options.get("mapping", {})),
    }
    
    formatter = formatters.get(format_type)
    if formatter:
        return formatter(value)
    
    return str(value) if value is not None else ""


def format_row(row: Dict[str, Any], column_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    formatted_row = {}
    
    for key, value in row.items():
        config = column_configs.get(key, {})
        format_type = config.get("format_type")
        options = config.get("options", {})
        
        if format_type:
            formatted_row[key] = apply_format(value, format_type, options)
        else:
            formatted_row[key] = str(value) if value is not None else ""
    
    return formatted_row


def format_table_data(data: List[Dict[str, Any]], column_configs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [format_row(row, column_configs) for row in data]
