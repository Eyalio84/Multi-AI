"""VOX Navigation Functions — browser-side functions (Phase 2).

Existing browser-side (in vox_registry.py): navigate_page, get_current_page,
get_workspace_state, switch_model, switch_theme, read_page_content
New here: 7 additional browser-side functions registered via register_browser()
"""
from services.vox_registry import vox_registry

# ── All browser-side: executed in frontend voxCore.ts, no server handler ──

vox_registry.register_browser(
    name="click_element",
    category="navigation",
    description="Click an element on the page by CSS selector",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector of element to click"},
        },
        "required": ["selector"],
    },
)

vox_registry.register_browser(
    name="scroll_to_element",
    category="navigation",
    description="Scroll the page to bring an element into view",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector of element to scroll to"},
        },
        "required": ["selector"],
    },
)

vox_registry.register_browser(
    name="highlight_element",
    category="navigation",
    description="Highlight an element with a pulsing border animation",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector of element to highlight"},
            "duration": {"type": "integer", "description": "Highlight duration in milliseconds"},
        },
        "required": ["selector"],
    },
)

vox_registry.register_browser(
    name="toggle_sidebar",
    category="navigation",
    description="Toggle the sidebar/navigation panel open or closed",
    parameters={"type": "object", "properties": {}},
)

vox_registry.register_browser(
    name="capture_screenshot",
    category="navigation",
    description="Capture a screenshot of the current page view",
    parameters={"type": "object", "properties": {}},
)

vox_registry.register_browser(
    name="fill_form_field",
    category="navigation",
    description="Fill a form field with a specified value",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector of the input field"},
            "value": {"type": "string", "description": "Value to fill in"},
        },
        "required": ["selector", "value"],
    },
)

vox_registry.register_browser(
    name="get_form_values",
    category="navigation",
    description="Read all form field values from a form element",
    parameters={
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector of the form"},
        },
        "required": ["selector"],
    },
)
