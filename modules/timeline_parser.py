import re
from typing import List, Dict, Optional
from pathlib import Path

def parse_timeline_markdown(file_path: str) -> List[Dict]:
    """
    Parse timeline markdown file into structured event data.
    
    Args:
        file_path: Path to timeline_events.md or timeline_events_ja.md
        
    Returns:
        List of event dictionaries with keys: date, title, category, description, 
        evidence_links, impact, key_quote
    """
    events = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return []
    
    # Split by event markers (### [DATE] - [TITLE])
    event_pattern = r'###\s+(\d{4}-\d{2}-\d{2})\s+-\s+(.+?)(?=\n###|\Z)'
    matches = re.finditer(event_pattern, content, re.DOTALL)
    
    for match in matches:
        date_str = match.group(1)
        title = match.group(2).split('\n')[0].strip()
        event_content = match.group(2)
        
        # Extract fields
        # Update regex to stop at --- as well
        category_raw = extract_field(event_content, r'\*\*Category\*\*:\s*(.+?)(?=\n|$)')
        category = normalize_category(category_raw) if category_raw else 'Context'
        
        # Use more robust lookaheads that include ---
        description = extract_field(event_content, r'\*\*Description\*\*:\s*(.+?)(?=\n\*\*|\n---|$)')
        impact = extract_field(event_content, r'\*\*Impact\*\*:\s*(.+?)(?=\n\*\*|\n---|$)')
        key_quote = extract_field(event_content, r'\*\*Key Quote\*\*:\s*(.+?)(?=\n\*\*|\n---|$)')
        
        # Extract Google Drive links only
        evidence_links = extract_google_drive_links(event_content)
        
        events.append({
            'date': date_str,
            'title': title,
            'category': category,
            'description': description or '',
            'evidence_links': evidence_links,
            'impact': impact or '',
            'key_quote': key_quote or ''
        })
    
    return events

def normalize_category(category: str) -> str:
    """Normalize category to English standard keys."""
    category_map = {
        '内部告発': 'Whistleblowing',
        '報復': 'Retaliation',
        '評価': 'Recognition',
        '妨害': 'Obstruction',
        '会議': 'Meeting',
        '雇用': 'Employment',
        '背景': 'Context'
    }
    return category_map.get(category, category)

def extract_field(text: str, pattern: str, multiline: bool = True) -> Optional[str]:
    """Extract a field from markdown using regex."""
    flags = re.DOTALL if multiline else 0
    match = re.search(pattern, text, flags)
    if match:
        value = match.group(1).strip()
        
        # Aggressively remove trailing '---' and any preceding newlines/spaces
        # This handles "\n---", "\n\n---", "  ---", etc.
        value = re.split(r'\n\s*---', value)[0].strip()
        
        # Remove surrounding quotes if present (for Key Quote)
        if value.startswith('"') and value.endswith('"') and len(value) > 1:
            value = value[1:-1].strip()
            
        # Only clean up newlines if not multiline, or handle differently
        if not multiline:
            value = re.sub(r'\n+', ' ', value)
            
        return value
    return None

def extract_google_drive_links(text: str) -> List[Dict[str, str]]:
    """Extract only Google Drive links from evidence section."""
    links = []
    
    # Pattern for Google Drive links
    gdrive_pattern = r'https://drive\.google\.com/[^\s\)]+(?:id=([a-zA-Z0-9_-]+))?'
    
    matches = re.finditer(gdrive_pattern, text)
    for i, match in enumerate(matches, 1):
        url = match.group(0)
        # Try to get descriptive text before the link
        # Look for markdown link syntax [Name](url) or bullet point - Name: url
        
        # 1. Check for markdown link syntax [Name](url)
        md_link_pattern = rf'\[([^\]]+)\]\({re.escape(url)}\)'
        md_match = re.search(md_link_pattern, text)
        
        if md_match:
            name = md_match.group(1).strip()
        else:
            # 2. Check for "Name: url" pattern
            context_pattern = rf'[-*]\s*([^:\n]+):\s*{re.escape(url)}'
            context_match = re.search(context_pattern, text)
            name = context_match.group(1).strip() if context_match else f"Evidence {i}"
        
        links.append({
            'name': name,
            'url': url
        })
    
    return links

def get_category_color(category: str) -> str:
    """Return color code for category badge."""
    # Map Japanese categories to English keys if needed
    category_map = {
        '内部告発': 'Whistleblowing',
        '報復': 'Retaliation',
        '評価': 'Recognition',
        '妨害': 'Obstruction',
        '会議': 'Meeting',
        '雇用': 'Employment',
        '背景': 'Context'
    }
    
    normalized_cat = category_map.get(category, category)
    
    colors = {
        'Whistleblowing': '#4CAF50',
        'Retaliation': '#F44336',
        'Recognition': '#2196F3',
        'Obstruction': '#FF9800',
        'Meeting': '#9C27B0',
        'Employment': '#607D8B',
        'Context': '#9E9E9E'
    }
    return colors.get(normalized_cat, '#9E9E9E')

def get_category_icon(category: str) -> str:
    """Return emoji icon for category."""
    category_map = {
        '内部告発': 'Whistleblowing',
        '報復': 'Retaliation',
        '評価': 'Recognition',
        '妨害': 'Obstruction',
        '会議': 'Meeting',
        '雇用': 'Employment',
        '背景': 'Context'
    }
    
    normalized_cat = category_map.get(category, category)
    
    icons = {
        'Whistleblowing': '📢',
        'Retaliation': '⚠️',
        'Recognition': '⭐',
        'Obstruction': '🚫',
        'Meeting': '🤝',
        'Employment': '💼',
        'Context': 'ℹ️'
    }
    return icons.get(normalized_cat, 'ℹ️')
