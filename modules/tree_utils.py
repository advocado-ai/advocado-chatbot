import json
from typing import List, Dict, Any

def build_folder_tree(folder_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Converts a list of file paths into a nested tree structure compatible with streamlit-tree-select.
    Optimized to use dictionary lookups instead of list iteration.
    """
    # 1. Build intermediate dict structure
    # Structure: { "folder_name": { "children": { ... } } }
    root = {}
    
    for path in folder_paths:
        if not path: continue
        parts = [p for p in path.strip('/').split('/') if p]
        current_level = root
        
        for part in parts:
            if part not in current_level:
                current_level[part] = {"children": {}}
            current_level = current_level[part]["children"]
            
    # 2. Convert to list format expected by tree-select
    def convert_to_nodes(level_dict, parent_path=""):
        nodes = []
        # Sort keys for consistent display order
        for key in sorted(level_dict.keys()):
            data = level_dict[key]
            full_path = f"{parent_path}/{key}" if parent_path else key
            
            node = {
                "label": key,
                "value": full_path,
                "children": convert_to_nodes(data["children"], full_path)
            }
            nodes.append(node)
        return nodes
        
    return convert_to_nodes(root)

def load_folders_from_json(json_path: str) -> List[str]:
    """Loads the folder list from the JSON file."""
    try:
        with open(json_path, 'r') as f:
            folders = json.load(f)
        return [f for f in folders if f] # Filter empty strings
    except Exception as e:
        print(f"Error loading folders: {e}")
        return []
