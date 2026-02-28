#!/usr/bin/env python3
"""
Code Generation Agent: HTML/CSS (#38)

Generates HTML and CSS code from natural language specifications.
Supports pages, components, forms, layouts, Tailwind CSS,
responsive design, and accessibility-compliant markup.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_html_css.py --example
    python3 codegen_html_css.py --workload spec.json --output result.json

Created: February 6, 2026
"""

import sys
import os
import re
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
)

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class HTMLSpec:
    description: str
    page_type: str  # landing, dashboard, form, component, layout, card, table
    name: str
    css_framework: str = "vanilla"  # vanilla, tailwind, bootstrap
    sections: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class GeneratedHTML:
    filename: str
    html_code: str
    css_code: str
    html_lines: int = 0
    css_lines: int = 0
    elements: List[str] = field(default_factory=list)


# ============================================================================
# L2: Constants
# ============================================================================

PAGE_TYPES = {
    "landing": {"has_nav": True, "has_footer": True, "has_hero": True},
    "dashboard": {"has_nav": True, "has_footer": False, "has_hero": False},
    "form": {"has_nav": False, "has_footer": False, "has_hero": False},
    "component": {"has_nav": False, "has_footer": False, "has_hero": False},
    "layout": {"has_nav": True, "has_footer": True, "has_hero": False},
    "card": {"has_nav": False, "has_footer": False, "has_hero": False},
    "table": {"has_nav": False, "has_footer": False, "has_hero": False},
}

HTML_RULES = [
    "codegen_html_001_semantic_elements",
    "codegen_html_002_aria_labels",
    "codegen_html_003_responsive_meta",
    "codegen_html_004_alt_text_images",
    "codegen_html_005_form_labels",
    "codegen_html_006_color_contrast",
]

HTML_ANTI_PATTERNS = [
    "div_soup",
    "missing_alt_text",
    "missing_form_labels",
    "inline_styles_overuse",
    "missing_viewport_meta",
    "non_semantic_markup",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenHtmlCssAnalyzer(BaseAnalyzer):
    """HTML/CSS code generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-html-css",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "specs": [
                {
                    "description": "Landing page for an AI agent platform with hero, features grid, pricing cards, and CTA",
                    "page_type": "landing",
                    "name": "agent-platform",
                    "css_framework": "tailwind",
                    "sections": ["hero", "features", "pricing", "cta", "footer"],
                    "constraints": ["responsive", "dark mode support", "accessible"],
                },
                {
                    "description": "Data table component with sortable columns, pagination, and search filter",
                    "page_type": "table",
                    "name": "data-table",
                    "css_framework": "vanilla",
                    "sections": ["search", "table", "pagination"],
                    "inputs": ["headers", "rows", "page_size"],
                    "constraints": ["responsive on mobile", "zebra striping", "hover highlight"],
                },
                {
                    "description": "Multi-step form wizard with progress bar, validation feedback, and summary step",
                    "page_type": "form",
                    "name": "signup-wizard",
                    "css_framework": "vanilla",
                    "sections": ["progress", "step1_personal", "step2_account", "step3_confirm"],
                    "inputs": ["name", "email", "password", "plan"],
                    "constraints": ["client-side validation", "accessible error messages"],
                },
            ],
        }

    def _parse_spec(self, spec_dict: Dict) -> HTMLSpec:
        return HTMLSpec(
            description=spec_dict.get("description", ""),
            page_type=spec_dict.get("page_type", "component"),
            name=spec_dict.get("name", "untitled"),
            css_framework=spec_dict.get("css_framework", "vanilla"),
            sections=spec_dict.get("sections", []),
            inputs=spec_dict.get("inputs", []),
            constraints=spec_dict.get("constraints", []),
        )

    def _generate_html_css(self, spec: HTMLSpec) -> GeneratedHTML:
        type_info = PAGE_TYPES.get(spec.page_type, PAGE_TYPES["component"])

        if spec.page_type == "landing":
            return self._gen_landing(spec, type_info)
        elif spec.page_type == "form":
            return self._gen_form(spec, type_info)
        elif spec.page_type == "table":
            return self._gen_table(spec, type_info)
        elif spec.page_type == "dashboard":
            return self._gen_dashboard(spec, type_info)
        elif spec.page_type == "card":
            return self._gen_card(spec, type_info)
        else:
            return self._gen_component(spec, type_info)

    def _html_wrapper(self, spec: HTMLSpec, body: str, css: str) -> tuple:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        title = spec.name.replace("-", " ").title()

        tailwind_cdn = ""
        if spec.css_framework == "tailwind":
            tailwind_cdn = '\n    <script src="https://cdn.tailwindcss.com"></script>'

        html = textwrap.dedent(f"""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>{title}</title>{tailwind_cdn}
              <link rel="stylesheet" href="{kebab}.css">
            </head>
            <body>
            {body}
            </body>
            </html>
        """)
        return html, css

    def _gen_landing(self, spec: HTMLSpec, type_info: Dict) -> GeneratedHTML:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        use_tw = spec.css_framework == "tailwind"

        sections_html = []
        for section in spec.sections:
            if section == "hero":
                if use_tw:
                    sections_html.append(textwrap.dedent("""\
                      <section class="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-20 px-6">
                        <div class="max-w-4xl mx-auto text-center">
                          <h1 class="text-5xl font-bold mb-4">Build Intelligent Agents</h1>
                          <p class="text-xl mb-8 opacity-90">The platform for creating, deploying, and managing AI agents at scale.</p>
                          <a href="#pricing" class="bg-white text-blue-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition">Get Started</a>
                        </div>
                      </section>"""))
                else:
                    sections_html.append(textwrap.dedent("""\
                      <section class="hero" role="banner">
                        <h1>Build Intelligent Agents</h1>
                        <p>The platform for creating, deploying, and managing AI agents at scale.</p>
                        <a href="#pricing" class="cta-button">Get Started</a>
                      </section>"""))
            elif section == "features":
                if use_tw:
                    sections_html.append(textwrap.dedent("""\
                      <section class="py-16 px-6 bg-white" id="features">
                        <div class="max-w-6xl mx-auto">
                          <h2 class="text-3xl font-bold text-center mb-12">Features</h2>
                          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div class="p-6 rounded-xl border hover:shadow-lg transition">
                              <h3 class="text-xl font-semibold mb-2">Multi-Model</h3>
                              <p class="text-gray-600">Route tasks across Claude, Gemini, and more.</p>
                            </div>
                            <div class="p-6 rounded-xl border hover:shadow-lg transition">
                              <h3 class="text-xl font-semibold mb-2">Knowledge Graphs</h3>
                              <p class="text-gray-600">Built-in KG construction and querying.</p>
                            </div>
                            <div class="p-6 rounded-xl border hover:shadow-lg transition">
                              <h3 class="text-xl font-semibold mb-2">Cost Optimization</h3>
                              <p class="text-gray-600">Reduce API costs by up to 80%.</p>
                            </div>
                          </div>
                        </div>
                      </section>"""))
                else:
                    sections_html.append(textwrap.dedent("""\
                      <section class="features" id="features">
                        <h2>Features</h2>
                        <div class="feature-grid">
                          <article class="feature-card"><h3>Multi-Model</h3><p>Route tasks across Claude, Gemini, and more.</p></article>
                          <article class="feature-card"><h3>Knowledge Graphs</h3><p>Built-in KG construction and querying.</p></article>
                          <article class="feature-card"><h3>Cost Optimization</h3><p>Reduce API costs by up to 80%.</p></article>
                        </div>
                      </section>"""))
            elif section == "pricing":
                if use_tw:
                    sections_html.append(textwrap.dedent("""\
                      <section class="py-16 px-6 bg-gray-50" id="pricing">
                        <div class="max-w-6xl mx-auto">
                          <h2 class="text-3xl font-bold text-center mb-12">Pricing</h2>
                          <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                            <div class="bg-white p-8 rounded-xl border text-center">
                              <h3 class="text-lg font-semibold">Free</h3><p class="text-3xl font-bold my-4">$0</p><p class="text-gray-500">For individuals</p>
                            </div>
                            <div class="bg-blue-600 text-white p-8 rounded-xl text-center shadow-xl">
                              <h3 class="text-lg font-semibold">Pro</h3><p class="text-3xl font-bold my-4">$29</p><p class="opacity-90">For teams</p>
                            </div>
                            <div class="bg-white p-8 rounded-xl border text-center">
                              <h3 class="text-lg font-semibold">Enterprise</h3><p class="text-3xl font-bold my-4">Custom</p><p class="text-gray-500">Contact us</p>
                            </div>
                          </div>
                        </div>
                      </section>"""))
                else:
                    sections_html.append(textwrap.dedent("""\
                      <section class="pricing" id="pricing">
                        <h2>Pricing</h2>
                        <div class="pricing-grid">
                          <div class="price-card"><h3>Free</h3><p class="price">$0</p><p>For individuals</p></div>
                          <div class="price-card featured"><h3>Pro</h3><p class="price">$29</p><p>For teams</p></div>
                          <div class="price-card"><h3>Enterprise</h3><p class="price">Custom</p><p>Contact us</p></div>
                        </div>
                      </section>"""))
            elif section == "cta":
                sections_html.append(textwrap.dedent("""\
                  <section class="cta" id="cta">
                    <h2>Ready to get started?</h2>
                    <a href="#" class="cta-button">Sign Up Free</a>
                  </section>"""))
            elif section == "footer":
                sections_html.append(textwrap.dedent("""\
                  <footer role="contentinfo">
                    <p>&copy; 2026 Agent Platform. All rights reserved.</p>
                  </footer>"""))
            else:
                sections_html.append(f'  <section id="{section}"><h2>{section.replace("_", " ").title()}</h2></section>')

        body = "\n".join(sections_html)

        css = textwrap.dedent(f"""\
            /* {spec.description} */
            :root {{
              --primary: #2563eb;
              --primary-dark: #1d4ed8;
              --bg: #ffffff;
              --text: #1f2937;
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: system-ui, -apple-system, sans-serif; color: var(--text); }}
            .hero {{ background: linear-gradient(135deg, var(--primary), #7c3aed); color: white; padding: 5rem 2rem; text-align: center; }}
            .hero h1 {{ font-size: 3rem; margin-bottom: 1rem; }}
            .cta-button {{ display: inline-block; padding: 0.75rem 2rem; background: var(--primary); color: white; text-decoration: none; border-radius: 0.5rem; }}
            .features, .pricing {{ padding: 4rem 2rem; max-width: 1200px; margin: 0 auto; }}
            .feature-grid, .pricing-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem; margin-top: 2rem; }}
            .feature-card, .price-card {{ padding: 2rem; border: 1px solid #e5e7eb; border-radius: 1rem; }}
            .price-card.featured {{ background: var(--primary); color: white; }}
            footer {{ padding: 2rem; text-align: center; background: #f9fafb; }}
            @media (max-width: 768px) {{
              .hero h1 {{ font-size: 2rem; }}
              .feature-grid, .pricing-grid {{ grid-template-columns: 1fr; }}
            }}
        """)

        html, css = self._html_wrapper(spec, body, css)
        return GeneratedHTML(
            filename=f"{kebab}.html",
            html_code=html,
            css_code=css,
            html_lines=html.count("\n") + 1,
            css_lines=css.count("\n") + 1,
            elements=spec.sections,
        )

    def _gen_form(self, spec: HTMLSpec, type_info: Dict) -> GeneratedHTML:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')

        form_fields = ""
        for inp in spec.inputs:
            input_type = "email" if "email" in inp else "password" if "password" in inp else "text"
            label = inp.replace("_", " ").title()
            form_fields += textwrap.dedent(f"""\
                <div class="form-group">
                  <label for="{inp}">{label}</label>
                  <input type="{input_type}" id="{inp}" name="{inp}" required aria-describedby="{inp}-error">
                  <span id="{inp}-error" class="error" role="alert"></span>
                </div>
            """)

        steps_html = ""
        for i, section in enumerate(spec.sections):
            active = ' class="step active"' if i == 0 else ' class="step"'
            steps_html += f'    <div{active} data-step="{i}">\n      <h2>{section.replace("_", " ").title()}</h2>\n      {form_fields if i == 0 else "<!-- Step content -->"}\n    </div>\n'

        progress = '<div class="progress-bar"><div class="progress-fill" style="width: 33%"></div></div>'

        body = textwrap.dedent(f"""\
          <main class="form-container" role="main">
            <h1>{spec.name.replace('-', ' ').title()}</h1>
            {progress}
            <form id="{kebab}-form" novalidate>
          {steps_html}
              <div class="form-actions">
                <button type="button" class="btn-prev" disabled>Previous</button>
                <button type="button" class="btn-next">Next</button>
                <button type="submit" class="btn-submit" hidden>Submit</button>
              </div>
            </form>
          </main>
        """)

        css = textwrap.dedent(f"""\
            /* {spec.description} */
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: system-ui, sans-serif; background: #f3f4f6; min-height: 100vh; display: flex; justify-content: center; align-items: center; }}
            .form-container {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; width: 100%; }}
            .progress-bar {{ height: 4px; background: #e5e7eb; border-radius: 2px; margin: 1.5rem 0; }}
            .progress-fill {{ height: 100%; background: #2563eb; border-radius: 2px; transition: width 0.3s; }}
            .form-group {{ margin-bottom: 1rem; }}
            .form-group label {{ display: block; font-weight: 600; margin-bottom: 0.25rem; }}
            .form-group input {{ width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.375rem; }}
            .form-group input:focus {{ outline: 2px solid #2563eb; border-color: transparent; }}
            .error {{ color: #dc2626; font-size: 0.875rem; }}
            .step {{ display: none; }} .step.active {{ display: block; }}
            .form-actions {{ display: flex; justify-content: space-between; margin-top: 1.5rem; }}
            .btn-prev, .btn-next, .btn-submit {{ padding: 0.5rem 1.5rem; border-radius: 0.375rem; border: none; cursor: pointer; }}
            .btn-next, .btn-submit {{ background: #2563eb; color: white; }}
            .btn-prev {{ background: #e5e7eb; }}
        """)

        html, css = self._html_wrapper(spec, body, css)
        return GeneratedHTML(
            filename=f"{kebab}.html",
            html_code=html,
            css_code=css,
            html_lines=html.count("\n") + 1,
            css_lines=css.count("\n") + 1,
            elements=spec.sections + spec.inputs,
        )

    def _gen_table(self, spec: HTMLSpec, type_info: Dict) -> GeneratedHTML:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')

        body = textwrap.dedent("""\
          <main class="table-container" role="main">
            <div class="table-toolbar">
              <input type="search" placeholder="Search..." aria-label="Search table" class="search-input">
            </div>
            <div class="table-responsive">
              <table role="grid">
                <thead>
                  <tr>
                    <th scope="col" aria-sort="none">ID</th>
                    <th scope="col" aria-sort="none">Name</th>
                    <th scope="col" aria-sort="none">Status</th>
                    <th scope="col" aria-sort="none">Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>1</td><td>Example Item</td><td>Active</td><td>2026-02-06</td></tr>
                  <tr><td>2</td><td>Another Item</td><td>Pending</td><td>2026-02-05</td></tr>
                </tbody>
              </table>
            </div>
            <nav class="pagination" aria-label="Table pagination">
              <button disabled>&laquo; Prev</button>
              <span>Page 1 of 1</span>
              <button disabled>Next &raquo;</button>
            </nav>
          </main>
        """)

        css = textwrap.dedent(f"""\
            /* {spec.description} */
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: system-ui, sans-serif; background: #f9fafb; padding: 2rem; }}
            .table-container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
            .table-toolbar {{ padding: 1rem; border-bottom: 1px solid #e5e7eb; }}
            .search-input {{ width: 100%; padding: 0.5rem 1rem; border: 1px solid #d1d5db; border-radius: 0.375rem; }}
            .table-responsive {{ overflow-x: auto; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #f3f4f6; padding: 0.75rem 1rem; text-align: left; font-weight: 600; cursor: pointer; user-select: none; }}
            td {{ padding: 0.75rem 1rem; border-top: 1px solid #e5e7eb; }}
            tbody tr:nth-child(even) {{ background: #f9fafb; }}
            tbody tr:hover {{ background: #eff6ff; }}
            .pagination {{ display: flex; justify-content: center; align-items: center; gap: 1rem; padding: 1rem; }}
            .pagination button {{ padding: 0.375rem 0.75rem; border: 1px solid #d1d5db; border-radius: 0.25rem; background: white; cursor: pointer; }}
            .pagination button:disabled {{ opacity: 0.5; cursor: default; }}
            @media (max-width: 640px) {{ th, td {{ padding: 0.5rem; font-size: 0.875rem; }} }}
        """)

        html, css = self._html_wrapper(spec, body, css)
        return GeneratedHTML(
            filename=f"{kebab}.html",
            html_code=html,
            css_code=css,
            html_lines=html.count("\n") + 1,
            css_lines=css.count("\n") + 1,
            elements=["search", "table", "pagination"],
        )

    def _gen_dashboard(self, spec: HTMLSpec, type_info: Dict) -> GeneratedHTML:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        body = '<main class="dashboard"><h1>Dashboard</h1><div class="grid">'
        for s in spec.sections:
            body += f'\n    <section class="panel" id="{s}"><h2>{s.replace("_"," ").title()}</h2></section>'
        body += '\n  </div></main>'
        css = f"/* {spec.description} */\n.dashboard {{ padding: 2rem; }}\n.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }}\n.panel {{ background: white; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}"
        html, css = self._html_wrapper(spec, body, css)
        return GeneratedHTML(filename=f"{kebab}.html", html_code=html, css_code=css, html_lines=html.count("\n")+1, css_lines=css.count("\n")+1, elements=spec.sections)

    def _gen_card(self, spec: HTMLSpec, type_info: Dict) -> GeneratedHTML:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        body = f'<article class="card"><h2>{spec.name.replace("-"," ").title()}</h2><p>{spec.description}</p></article>'
        css = f".card {{ background: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 400px; }}"
        html, css = self._html_wrapper(spec, body, css)
        return GeneratedHTML(filename=f"{kebab}.html", html_code=html, css_code=css, html_lines=html.count("\n")+1, css_lines=css.count("\n")+1, elements=["card"])

    def _gen_component(self, spec: HTMLSpec, type_info: Dict) -> GeneratedHTML:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        body = f'<div class="{kebab}">\n'
        for s in spec.sections:
            body += f'  <div class="{s}">{s.replace("_"," ").title()}</div>\n'
        body += '</div>'
        css = f".{kebab} {{ padding: 1rem; }}"
        html, css = self._html_wrapper(spec, body, css)
        return GeneratedHTML(filename=f"{kebab}.html", html_code=html, css_code=css, html_lines=html.count("\n")+1, css_lines=css.count("\n")+1, elements=spec.sections)

    def _check_anti_patterns(self, html: str) -> List[str]:
        found = []
        if '<img' in html and 'alt=' not in html:
            found.append("missing_alt_text")
        if '<input' in html and '<label' not in html:
            found.append("missing_form_labels")
        if 'viewport' not in html:
            found.append("missing_viewport_meta")
        div_count = html.count('<div')
        semantic_count = sum(html.count(f'<{t}') for t in ['section', 'article', 'nav', 'main', 'header', 'footer', 'aside'])
        if div_count > 10 and semantic_count < div_count // 3:
            found.append("div_soup")
        return found

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        specs_raw = w.get("specs", [])

        generated = []
        all_anti_patterns = []
        total_html_lines = 0
        total_css_lines = 0
        type_counts: Dict[str, int] = {}
        fw_counts: Dict[str, int] = {}

        for spec_dict in specs_raw:
            spec = self._parse_spec(spec_dict)
            result = self._generate_html_css(spec)
            generated.append(result)
            total_html_lines += result.html_lines
            total_css_lines += result.css_lines
            type_counts[spec.page_type] = type_counts.get(spec.page_type, 0) + 1
            fw_counts[spec.css_framework] = fw_counts.get(spec.css_framework, 0) + 1
            all_anti_patterns.extend(self._check_anti_patterns(result.html_code))

        recommendations = []
        for gen in generated:
            recommendations.append({
                "technique": f"codegen_html_{gen.filename}",
                "impact": f"Generated {gen.html_lines} HTML + {gen.css_lines} CSS lines",
                "reasoning": f"File: {gen.filename}, Elements: {gen.elements}",
                "filename": gen.filename,
                "html_code": gen.html_code,
                "css_code": gen.css_code,
                "html_lines": gen.html_lines,
                "css_lines": gen.css_lines,
                "elements": gen.elements,
            })

        meta_insight = (
            f"Generated {len(generated)} HTML/CSS file pairs totaling {total_html_lines} HTML + {total_css_lines} CSS lines. "
            f"Types: {', '.join(f'{k}({v})' for k, v in type_counts.items())}. "
            f"Frameworks: {', '.join(f'{k}({v})' for k, v in fw_counts.items())}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=HTML_RULES[:len(generated) + 2],
            meta_insight=meta_insight,
            analysis_data={
                "files_generated": len(generated),
                "total_html_lines": total_html_lines,
                "total_css_lines": total_css_lines,
                "type_distribution": type_counts,
                "framework_distribution": fw_counts,
            },
            anti_patterns=list(set(all_anti_patterns)),
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenHtmlCssAnalyzer()
    run_standard_cli(
        agent_name="CodeGen HTML/CSS",
        description="Generate HTML and CSS from natural language specifications",
        analyzer=analyzer,
    )
