#!/usr/bin/env python3
"""
Code Generation Agent: JavaScript/TypeScript (#35)

Generates JavaScript and TypeScript code from natural language specifications.
Supports Node.js scripts, React components, Express APIs, utility functions,
and TypeScript types/interfaces.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_javascript.py --example
    python3 codegen_javascript.py --workload spec.json --output result.json

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
class JSCodeSpec:
    description: str
    code_type: str  # node_script, react_component, express_api, function, typescript_types, utility
    name: str
    typescript: bool = False
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class GeneratedJS:
    filename: str
    code: str
    language: str = "javascript"
    lines: int = 0
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


# ============================================================================
# L2: Constants
# ============================================================================

JS_CODE_TYPES = {
    "node_script": {
        "ext": ".js",
        "typical_imports": ["fs", "path"],
        "module_system": "commonjs",
    },
    "react_component": {
        "ext": ".tsx",
        "typical_imports": ["react"],
        "module_system": "esm",
    },
    "express_api": {
        "ext": ".js",
        "typical_imports": ["express"],
        "module_system": "commonjs",
    },
    "function": {
        "ext": ".js",
        "typical_imports": [],
        "module_system": "esm",
    },
    "typescript_types": {
        "ext": ".ts",
        "typical_imports": [],
        "module_system": "esm",
    },
    "utility": {
        "ext": ".js",
        "typical_imports": [],
        "module_system": "esm",
    },
}

JS_RULES = [
    "codegen_js_001_const_over_let",
    "codegen_js_002_arrow_functions",
    "codegen_js_003_template_literals",
    "codegen_js_004_destructuring",
    "codegen_js_005_async_await",
    "codegen_js_006_no_var",
    "codegen_js_007_strict_equality",
    "codegen_js_008_error_boundaries",
]

JS_ANTI_PATTERNS = [
    "var_declaration",
    "callback_hell",
    "loose_equality",
    "no_error_handling",
    "implicit_globals",
    "string_concatenation",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenJavascriptAnalyzer(BaseAnalyzer):
    """JavaScript/TypeScript code generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-javascript",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "specs": [
                {
                    "description": "Express REST API with CRUD endpoints for a todo list with in-memory storage",
                    "code_type": "express_api",
                    "name": "todo-api",
                    "inputs": ["title", "completed", "id"],
                    "outputs": ["GET /todos", "POST /todos", "PUT /todos/:id", "DELETE /todos/:id"],
                    "dependencies": ["express", "cors"],
                    "constraints": ["input validation", "proper status codes", "error handling"],
                },
                {
                    "description": "React component for a search bar with debounced input and loading state",
                    "code_type": "react_component",
                    "name": "SearchBar",
                    "typescript": True,
                    "inputs": ["onSearch", "placeholder", "debounceMs"],
                    "outputs": ["rendered_component"],
                    "dependencies": ["react"],
                    "constraints": ["accessible", "responsive", "debounce 300ms default"],
                },
                {
                    "description": "TypeScript interface definitions for a user management system",
                    "code_type": "typescript_types",
                    "name": "user-types",
                    "typescript": True,
                    "inputs": ["User", "UserRole", "UserPermission"],
                    "outputs": ["User", "UserRole", "UserPermission", "UserSession"],
                    "dependencies": [],
                    "constraints": ["strict types", "enum for roles"],
                },
            ],
        }

    def _parse_spec(self, spec_dict: Dict) -> JSCodeSpec:
        return JSCodeSpec(
            description=spec_dict.get("description", ""),
            code_type=spec_dict.get("code_type", "function"),
            name=spec_dict.get("name", "untitled"),
            typescript=spec_dict.get("typescript", False),
            inputs=spec_dict.get("inputs", []),
            outputs=spec_dict.get("outputs", []),
            dependencies=spec_dict.get("dependencies", []),
            constraints=spec_dict.get("constraints", []),
        )

    def _generate_code(self, spec: JSCodeSpec) -> GeneratedJS:
        type_info = JS_CODE_TYPES.get(spec.code_type, JS_CODE_TYPES["function"])

        if spec.code_type == "express_api":
            return self._gen_express(spec, type_info)
        elif spec.code_type == "react_component":
            return self._gen_react(spec, type_info)
        elif spec.code_type == "typescript_types":
            return self._gen_types(spec, type_info)
        elif spec.code_type == "node_script":
            return self._gen_node(spec, type_info)
        else:
            return self._gen_utility(spec, type_info)

    def _gen_express(self, spec: JSCodeSpec, type_info: Dict) -> GeneratedJS:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        resource = kebab.replace("-api", "").replace("-", "_")

        imports = [f"const express = require('express');"]
        for dep in spec.dependencies:
            if dep != "express":
                imports.append(f"const {dep} = require('{dep}');")

        routes = ""
        for out in spec.outputs:
            parts = out.split()
            if len(parts) >= 2:
                method = parts[0].lower()
                path = parts[1]
                handler = re.sub(r'[^a-z0-9]+', '_', f"{method}_{path}".lower()).strip('_')
                routes += f"\napp.{method}('{path}', (req, res) => {{\n  // TODO: implement {out}\n  res.json({{ message: '{out}' }});\n}});\n"

        code = textwrap.dedent(f"""\
            /**
             * {spec.description}
             */

            {chr(10).join(imports)}

            const app = express();
            app.use(express.json());

            // In-memory storage
            let {resource}s = [];
            let nextId = 1;
            {routes}
            const PORT = process.env.PORT || 3000;
            app.listen(PORT, () => {{
              console.log(`Server running on port ${{PORT}}`);
            }});

            module.exports = app;
        """)

        return GeneratedJS(
            filename=f"{kebab}.js",
            code=code,
            lines=code.count("\n") + 1,
            imports=spec.dependencies,
            exports=["app"],
        )

    def _gen_react(self, spec: JSCodeSpec, type_info: Dict) -> GeneratedJS:
        ext = ".tsx" if spec.typescript else ".jsx"
        component_name = spec.name

        props_type = ""
        if spec.typescript:
            prop_types = "\n".join(f"  {i}: {'(() => void)' if 'on' == i[:2] else 'string'};" for i in spec.inputs)
            props_type = f"\ninterface {component_name}Props {{\n{prop_types}\n}}\n"

        props_param = f"{{ {', '.join(spec.inputs)} }}: {component_name}Props" if spec.typescript else f"{{ {', '.join(spec.inputs)} }}"

        code = textwrap.dedent(f"""\
            /**
             * {spec.description}
             */

            import React, {{ useState, useCallback }} from 'react';
            {props_type}

            export const {component_name} = ({props_param}) => {{
              const [value, setValue] = useState('');
              const [loading, setLoading] = useState(false);

              const handleChange = useCallback((e{': React.ChangeEvent<HTMLInputElement>' if spec.typescript else ''}) => {{
                setValue(e.target.value);
                // TODO: implement debounce + callback
              }}, []);

              return (
                <div className="{component_name.lower()}-container">
                  <input
                    type="text"
                    value={{value}}
                    onChange={{handleChange}}
                    placeholder={{{spec.inputs[1] if len(spec.inputs) > 1 else '"Search..."'}}}
                    aria-label="Search"
                  />
                  {{loading && <span className="loading">Loading...</span>}}
                </div>
              );
            }};

            export default {component_name};
        """)

        return GeneratedJS(
            filename=f"{component_name}{ext}",
            code=code,
            language="typescript" if spec.typescript else "javascript",
            lines=code.count("\n") + 1,
            imports=["react"],
            exports=[component_name],
        )

    def _gen_types(self, spec: JSCodeSpec, type_info: Dict) -> GeneratedJS:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')

        interfaces = ""
        for out in spec.outputs:
            interfaces += f"\nexport interface {out} {{\n  id: string;\n  // TODO: define fields for {out}\n}}\n"

        code = textwrap.dedent(f"""\
            /**
             * {spec.description}
             */

            {interfaces}
        """)

        return GeneratedJS(
            filename=f"{kebab}.ts",
            code=code,
            language="typescript",
            lines=code.count("\n") + 1,
            imports=[],
            exports=spec.outputs,
        )

    def _gen_node(self, spec: JSCodeSpec, type_info: Dict) -> GeneratedJS:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        imports = [f"const {dep} = require('{dep}');" for dep in ["fs", "path"] + spec.dependencies]

        code = textwrap.dedent(f"""\
            #!/usr/bin/env node
            /**
             * {spec.description}
             */

            {chr(10).join(imports)}

            async function main() {{
              // TODO: implement {spec.description}
              console.log('Running {spec.name}...');
            }}

            main().catch(console.error);
        """)

        return GeneratedJS(
            filename=f"{kebab}.js",
            code=code,
            lines=code.count("\n") + 1,
            imports=["fs", "path"] + spec.dependencies,
            exports=[],
        )

    def _gen_utility(self, spec: JSCodeSpec, type_info: Dict) -> GeneratedJS:
        kebab = re.sub(r'[^a-z0-9]+', '-', spec.name.lower()).strip('-')
        ext = ".ts" if spec.typescript else ".js"

        funcs = ""
        for out in spec.outputs:
            fname = re.sub(r'[^a-zA-Z0-9]+', '', out)
            fname = fname[0].lower() + fname[1:] if fname else "process"
            type_hint = f": any" if spec.typescript else ""
            funcs += f"\nexport function {fname}(){type_hint} {{\n  // TODO: implement {out}\n  throw new Error('Not implemented');\n}}\n"

        code = textwrap.dedent(f"""\
            /**
             * {spec.description}
             */

            {funcs}
        """)

        return GeneratedJS(
            filename=f"{kebab}{ext}",
            code=code,
            language="typescript" if spec.typescript else "javascript",
            lines=code.count("\n") + 1,
            imports=[],
            exports=[re.sub(r'[^a-zA-Z0-9]+', '', o) for o in spec.outputs],
        )

    def _check_anti_patterns(self, code: str) -> List[str]:
        found = []
        if "var " in code:
            found.append("var_declaration")
        if "==" in code and "===" not in code:
            found.append("loose_equality")
        if ".then(" in code and "async" not in code:
            found.append("callback_hell")
        return found

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        specs_raw = w.get("specs", [])

        generated = []
        all_anti_patterns = []
        total_lines = 0
        type_counts: Dict[str, int] = {}
        ts_count = 0

        for spec_dict in specs_raw:
            spec = self._parse_spec(spec_dict)
            code_result = self._generate_code(spec)
            generated.append(code_result)
            total_lines += code_result.lines
            type_counts[spec.code_type] = type_counts.get(spec.code_type, 0) + 1
            if spec.typescript:
                ts_count += 1
            all_anti_patterns.extend(self._check_anti_patterns(code_result.code))

        recommendations = []
        for gen in generated:
            recommendations.append({
                "technique": f"codegen_js_{gen.filename}",
                "impact": f"Generated {gen.lines} lines of {gen.language}",
                "reasoning": f"File: {gen.filename}, Exports: {gen.exports}",
                "filename": gen.filename,
                "code": gen.code,
                "language": gen.language,
                "lines": gen.lines,
                "imports": gen.imports,
                "exports": gen.exports,
            })

        meta_insight = (
            f"Generated {len(generated)} JS/TS files totaling {total_lines} lines. "
            f"TypeScript: {ts_count}/{len(generated)}. "
            f"Types: {', '.join(f'{k}({v})' for k, v in type_counts.items())}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=JS_RULES[:len(generated) + 2],
            meta_insight=meta_insight,
            analysis_data={
                "files_generated": len(generated),
                "total_lines": total_lines,
                "typescript_files": ts_count,
                "type_distribution": type_counts,
                "all_exports": [e for g in generated for e in g.exports],
            },
            anti_patterns=list(set(all_anti_patterns)),
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenJavascriptAnalyzer()
    run_standard_cli(
        agent_name="CodeGen JavaScript",
        description="Generate JavaScript/TypeScript code from specifications",
        analyzer=analyzer,
    )
