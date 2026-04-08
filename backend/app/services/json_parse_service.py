import json
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from datetime import datetime


def detect_json(response: Any) -> bool:
    if isinstance(response, (dict, list)):
        return True
    
    if isinstance(response, str):
        try:
            json.loads(response)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    return False


def parse_json_structure(json_data: Any, path: str = "$") -> Dict[str, Any]:
    structure = {
        "path": path,
        "type": type(json_data).__name__,
        "sample": None,
        "count": 0,
        "children": []
    }
    
    if isinstance(json_data, dict):
        structure["type"] = "object"
        structure["count"] = len(json_data)
        
        if json_data:
            first_key = next(iter(json_data.keys()))
            structure["sample"] = {first_key: json_data[first_key]}
        
        for key, value in json_data.items():
            child_path = f"{path}.{key}"
            structure["children"].append(parse_json_structure(value, child_path))
    
    elif isinstance(json_data, list):
        structure["type"] = "array"
        structure["count"] = len(json_data)
        
        if json_data:
            structure["sample"] = json_data[0]
            
            item_types = Counter(type(item).__name__ for item in json_data[:100])
            structure["item_types"] = dict(item_types)
            
            if json_data and isinstance(json_data[0], dict):
                all_keys = set()
                for item in json_data[:100]:
                    if isinstance(item, dict):
                        all_keys.update(item.keys())
                
                for key in sorted(all_keys):
                    child_path = f"{path}[*].{key}"
                    sample_values = [
                        item.get(key) for item in json_data[:10]
                        if isinstance(item, dict) and key in item
                    ]
                    structure["children"].append({
                        "path": child_path,
                        "type": "array_item",
                        "sample": sample_values[0] if sample_values else None,
                        "count": len(sample_values)
                    })
    
    elif isinstance(json_data, str):
        structure["sample"] = json_data[:100]
        structure["count"] = len(json_data)
        
        if re.match(r'^\d{4}-\d{2}-\d{2}', json_data):
            structure["inferred_type"] = "date"
        elif re.match(r'^https?://', json_data):
            structure["inferred_type"] = "url"
        elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', json_data):
            structure["inferred_type"] = "email"
    
    elif isinstance(json_data, bool):
        structure["sample"] = json_data
    
    elif isinstance(json_data, (int, float)):
        structure["sample"] = json_data
        structure["count"] = 1
    
    elif json_data is None:
        structure["type"] = "null"
    
    return structure


def get_field_paths(json_data: Any, prefix: str = "$") -> List[str]:
    paths = []
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            path = f"{prefix}.{key}"
            paths.append(path)
            paths.extend(get_field_paths(value, path))
    
    elif isinstance(json_data, list):
        if json_data and isinstance(json_data[0], dict):
            all_keys = set()
            for item in json_data[:100]:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            for key in sorted(all_keys):
                path = f"{prefix}[*].{key}"
                paths.append(path)
    
    return paths


def infer_field_types(json_data: Any) -> Dict[str, str]:
    if isinstance(json_data, list):
        json_data = json_data[0] if json_data else {}
    
    if not isinstance(json_data, dict):
        return {}
    
    types = {}
    
    for key, value in json_data.items():
        if value is None:
            types[key] = "null"
        elif isinstance(value, bool):
            types[key] = "boolean"
        elif isinstance(value, int):
            types[key] = "integer"
        elif isinstance(value, float):
            types[key] = "number"
        elif isinstance(value, str):
            if re.match(r'^\d{4}-\d{2}-\d{2}', value):
                types[key] = "date"
            elif re.match(r'^https?://', value):
                types[key] = "url"
            else:
                types[key] = "string"
        elif isinstance(value, list):
            types[key] = "array"
        elif isinstance(value, dict):
            types[key] = "object"
        else:
            types[key] = "unknown"
    
    return types


def generate_json_tree(json_data: Any, depth: int = 0, max_depth: int = 5) -> List[Dict[str, Any]]:
    if depth > max_depth:
        return [{"key": "...", "value": "(truncated)", "type": "truncated"}]
    
    tree = []
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            node = {
                "key": key,
                "type": type(value).__name__,
                "depth": depth
            }
            
            if isinstance(value, (str, int, float, bool)) or value is None:
                node["value"] = str(value)[:50] if value is not None else "null"
                node["is_leaf"] = True
            else:
                node["children"] = generate_json_tree(value, depth + 1, max_depth)
                node["is_leaf"] = False
                node["count"] = len(value) if isinstance(value, (list, dict)) else 0
            
            tree.append(node)
    
    elif isinstance(json_data, list):
        for i, item in enumerate(json_data[:10]):
            node = {
                "key": f"[{i}]",
                "type": type(item).__name__,
                "depth": depth
            }
            
            if isinstance(item, (str, int, float, bool)) or item is None:
                node["value"] = str(item)[:50] if item is not None else "null"
                node["is_leaf"] = True
            else:
                node["children"] = generate_json_tree(item, depth + 1, max_depth)
                node["is_leaf"] = False
                node["count"] = len(item) if isinstance(item, (list, dict)) else 0
            
            tree.append(node)
        
        if len(json_data) > 10:
            tree.append({
                "key": "...",
                "value": f"({len(json_data) - 10} more items)",
                "type": "truncated",
                "depth": depth,
                "is_leaf": True
            })
    
    return tree


def flatten_json(json_data: Any, prefix: str = "", separator: str = "_") -> Dict[str, Any]:
    flattened = {}
    
    if isinstance(json_data, dict):
        for key, value in json_data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(flatten_json(value, new_key, separator))
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    for i, item in enumerate(value):
                        flattened.update(flatten_json(item, f"{new_key}{separator}{i}", separator))
                else:
                    flattened[new_key] = value
            else:
                flattened[new_key] = value
    
    elif isinstance(json_data, list):
        for i, item in enumerate(json_data):
            new_key = f"{prefix}{separator}{i}" if prefix else str(i)
            
            if isinstance(item, dict):
                flattened.update(flatten_json(item, new_key, separator))
            elif isinstance(item, list):
                flattened.update(flatten_json(item, new_key, separator))
            else:
                flattened[new_key] = item
    
    else:
        flattened[prefix if prefix else "value"] = json_data
    
    return flattened


def convert_key_to_title(key: str) -> str:
    key = re.sub(r'([A-Z])', r' \1', key)
    key = key.replace('_', ' ').replace('-', ' ')
    key = re.sub(r'\s+', ' ', key)
    return key.strip().title()


def generate_table_config(json_structure: Dict[str, Any]) -> Dict[str, Any]:
    columns = []
    
    def extract_columns(node: Dict[str, Any], parent_path: str = ""):
        if node.get("type") == "object" and node.get("children"):
            for child in node["children"]:
                path = child.get("path", "")
                key = path.split(".")[-1] if path else ""
                
                if child.get("type") in ["string", "integer", "number", "boolean", "date"]:
                    columns.append({
                        "field": key,
                        "title": convert_key_to_title(key),
                        "path": path,
                        "type": child.get("type"),
                        "inferred_type": child.get("inferred_type"),
                        "sortable": True,
                        "filterable": True
                    })
                elif child.get("type") == "array_item":
                    columns.append({
                        "field": key,
                        "title": convert_key_to_title(key),
                        "path": path,
                        "type": "array_item",
                        "sortable": True,
                        "filterable": True
                    })
    
    extract_columns(json_structure)
    
    return {
        "columns": columns,
        "total_columns": len(columns)
    }
