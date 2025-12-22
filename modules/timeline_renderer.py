from typing import List, Dict

def render_timeline_html(events: List[Dict]) -> str:
    """
    Generate HTML for a vertical timeline visualization.
    
    Args:
        events: List of event dictionaries (from timeline_parser)
        
    Returns:
        HTML string to be rendered with st.markdown(unsafe_allow_html=True)
    """
    
    # CSS Styles
    # Use dedent or manual formatting to avoid leading spaces which Markdown interprets as code blocks
    css = """
<style>
    /* Timeline Container */
    .timeline-container {
        position: relative;
        max-width: 800px;
        margin: 0 auto;
        padding: 40px 0;
        font-family: "Source Sans Pro", sans-serif;
    }

    /* Vertical Line */
    .timeline-container::after {
        content: '';
        position: absolute;
        width: 6px;
        background-color: #b0bec5; /* Darker gray-blue for better visibility */
        top: 0;
        bottom: 0;
        left: 20px; /* Position of the line */
        margin-left: -3px;
        z-index: 0;
    }

    /* Event Item */
    .timeline-item {
        position: relative;
        margin-bottom: 60px; /* Increased spacing */
        padding-left: 70px; /* Space for line and marker */
        z-index: 1;
    }

    /* Event Marker (Circle) */
    .timeline-marker {
        position: absolute;
        left: 20px;
        top: 0;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: white;
        border: 4px solid #2196F3; /* Default color */
        transform: translateX(-50%);
        z-index: 2; /* Above line */
    }

    /* Content Bubble */
    .timeline-content {
        background-color: #f9f9f9;
        border-radius: 8px;
        padding: 15px 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border: 1px solid #eee;
        position: relative;
    }

    /* Arrow pointing to marker */
    .timeline-content::before {
        content: " ";
        position: absolute;
        top: 10px;
        right: 100%; /* To the left of the content */
        height: 0;
        width: 0;
        border: 10px solid transparent;
        border-right-color: #f9f9f9; /* Match background */
        pointer-events: none;
    }
    
    /* Header Section */
    .timeline-header {
        display: flex;
        justify_content: space-between;
        align-items: flex-start;
        margin-bottom: 10px;
        flex-wrap: wrap;
        gap: 10px;
    }

    .timeline-date {
        font-weight: 700;
        color: #555;
        font-size: 1.1em;
        background: #e3f2fd;
        padding: 2px 8px;
        border-radius: 4px;
    }

    .timeline-title {
        font-size: 1.2em;
        font-weight: 600;
        color: #333;
        margin: 0;
        flex-grow: 1;
    }

    /* Category Badge */
    .timeline-category {
        font-size: 0.8em;
        padding: 2px 8px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        white-space: nowrap;
    }

    /* Description Body */
    .timeline-body {
        color: #444;
        line-height: 1.6;
        margin-bottom: 15px;
        white-space: pre-wrap; /* Preserve newlines */
    }

    /* Impact Section */
    .timeline-impact {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 8px 12px;
        margin-bottom: 15px;
        font-size: 0.95em;
        color: #5d4037;
    }

    /* Quote Section */
    .timeline-quote {
        font-style: italic;
        color: #666;
        border-left: 3px solid #9e9e9e;
        padding-left: 10px;
        margin: 10px 0;
    }

    /* Evidence Links */
    .timeline-evidence {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
        border-top: 1px solid #eee;
        padding-top: 10px;
    }

    .evidence-btn {
        display: inline-flex;
        align-items: center;
        background-color: #fff;
        border: 1px solid #ddd;
        padding: 4px 10px;
        border-radius: 4px;
        text-decoration: none !important;
        color: #333 !important;
        font-size: 0.85em;
        transition: background-color 0.2s;
        white-space: nowrap; /* Prevent icon/text wrapping */
    }

    .evidence-btn:hover {
        background-color: #f5f5f5;
        border-color: #bbb;
    }

    .evidence-icon {
        margin-right: 5px;
    }
    
    /* Dark Mode Adjustments (Basic) */
    @media (prefers-color-scheme: dark) {
        .timeline-content {
            background-color: #262730;
            border-color: #444;
            color: #eee;
        }
        .timeline-content::before {
            border-right-color: #262730;
        }
        .timeline-title { color: #fff; }
        .timeline-body { color: #ddd; }
        .timeline-date { background: #1e3a5f; color: #90caf9; }
        .evidence-btn { 
            background-color: #333; 
            border-color: #555; 
            color: #eee !important; 
        }
        .evidence-btn:hover { background-color: #444; }
        .timeline-impact {
            background-color: #3e2723;
            color: #ffcc80;
        }
        /* Ensure marker background is dark in dark mode so line doesn't show through if transparent */
        .timeline-marker {
            background-color: #262730;
        }
    }
</style>
"""
    
    html_content = ['<div class="timeline-container">']
    
    from modules.timeline_parser import get_category_color, get_category_icon
    
    for event in events:
        color = get_category_color(event['category'])
        icon = get_category_icon(event['category'])
        
        # Build Evidence HTML
        evidence_html = ""
        if event['evidence_links']:
            links_html = []
            for link in event['evidence_links']:
                links_html.append(
                    f'<a href="{link["url"]}" target="_blank" class="evidence-btn">'
                    f'<span class="evidence-icon">📂</span>{link["name"]}</a>'
                )
            evidence_html = f'<div class="timeline-evidence">{"".join(links_html)}</div>'
            
        # Build Impact HTML
        impact_html = ""
        if event['impact']:
            impact_html = f'<div class="timeline-impact"><strong>Impact:</strong> {event["impact"]}</div>'
            
        # Build Quote HTML
        quote_html = ""
        if event['key_quote']:
            quote_html = f'<div class="timeline-quote">"{event["key_quote"]}"</div>'

        # Build Item HTML
        # Use compact HTML to avoid markdown interference
        item_html = f"""<div class="timeline-item">
<div class="timeline-marker" style="border-color: {color};"></div>
<div class="timeline-content">
<div class="timeline-header">
<span class="timeline-date">{event['date']}</span>
<span class="timeline-category" style="background-color: {color};">{icon} {event['category']}</span>
</div>
<h3 class="timeline-title">{event['title']}</h3>
<div class="timeline-body">{event['description']}</div>
{quote_html}
{impact_html}
{evidence_html}
</div>
</div>"""
        html_content.append(item_html)
        
    html_content.append('</div>')
    
    return css + "".join(html_content)
