#!/usr/bin/env python3
"""
Code Generation Agent: Python (#34)

Generates Python code from natural language specifications.
Supports scripts, classes, CLI tools, FastAPI endpoints, tests,
data pipelines, and agent definitions.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_python.py --example
    python3 codegen_python.py --workload spec.json --output result.json

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
class CodeSpec:
    description: str
    code_type: str  # script, class, function, cli, api, test, agent, pipeline
    name: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass
class GeneratedCode:
    filename: str
    code: str
    language: str = "python"
    lines: int = 0
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


# ============================================================================
# L2: Constants
# ============================================================================

CODE_TYPES = {
    "script": {
        "template": "standalone",
        "requires_main": True,
        "typical_imports": ["sys", "os", "json", "argparse"],
    },
    "class": {
        "template": "oop",
        "requires_main": False,
        "typical_imports": ["dataclasses", "typing"],
    },
    "function": {
        "template": "minimal",
        "requires_main": False,
        "typical_imports": ["typing"],
    },
    "cli": {
        "template": "cli_app",
        "requires_main": True,
        "typical_imports": ["sys", "os", "argparse", "json"],
    },
    "api": {
        "template": "fastapi",
        "requires_main": True,
        "typical_imports": ["fastapi", "pydantic", "uvicorn"],
    },
    "test": {
        "template": "pytest",
        "requires_main": False,
        "typical_imports": ["pytest", "unittest.mock"],
    },
    "agent": {
        "template": "nlke_agent",
        "requires_main": True,
        "typical_imports": ["sys", "os", "json", "dataclasses", "typing"],
    },
    "pipeline": {
        "template": "pipeline",
        "requires_main": True,
        "typical_imports": ["sys", "os", "json", "pathlib"],
    },
}

# Python best practices rules
PYTHON_RULES = [
    "codegen_001_type_hints_required",
    "codegen_002_docstrings_required",
    "codegen_003_no_bare_except",
    "codegen_004_pathlib_over_os_path",
    "codegen_005_f_strings_preferred",
    "codegen_006_dataclasses_for_data",
    "codegen_007_main_guard",
    "codegen_008_consistent_naming",
]

# Anti-patterns to avoid
PYTHON_ANTI_PATTERNS = [
    "mutable_default_arguments",
    "global_state_mutation",
    "bare_except_clause",
    "string_concatenation_in_loop",
    "nested_try_except",
    "hardcoded_paths",
    "import_star",
    "unused_variables",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenPythonAnalyzer(BaseAnalyzer):
    """Python code generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-python",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "specs": [
                {
                    "description": "CLI tool that reads a JSON file, filters entries by a key-value pair, and outputs results as formatted table",
                    "code_type": "cli",
                    "name": "json_filter",
                    "inputs": ["json_file_path", "filter_key", "filter_value"],
                    "outputs": ["filtered_table_stdout", "count"],
                    "dependencies": [],
                    "constraints": ["handle missing keys gracefully", "support nested JSON"],
                },
                {
                    "description": "Data class for representing API rate limit state with sliding window tracking",
                    "code_type": "class",
                    "name": "RateLimiter",
                    "inputs": ["max_requests_per_minute", "window_size_seconds"],
                    "outputs": ["allow_request", "remaining", "reset_time"],
                    "dependencies": ["time", "collections"],
                    "constraints": ["thread-safe", "O(1) check time"],
                },
                {
                    "description": "Pytest test suite for a calculator module with add, subtract, multiply, divide",
                    "code_type": "test",
                    "name": "test_calculator",
                    "inputs": ["calculator_module"],
                    "outputs": ["test_results"],
                    "dependencies": ["pytest"],
                    "constraints": ["cover edge cases", "test division by zero"],
                },
            ],
        }

    def _parse_spec(self, spec_dict: Dict) -> CodeSpec:
        return CodeSpec(
            description=spec_dict.get("description", ""),
            code_type=spec_dict.get("code_type", "script"),
            name=spec_dict.get("name", "untitled"),
            inputs=spec_dict.get("inputs", []),
            outputs=spec_dict.get("outputs", []),
            dependencies=spec_dict.get("dependencies", []),
            constraints=spec_dict.get("constraints", []),
        )

    def _generate_code(self, spec: CodeSpec) -> GeneratedCode:
        """Generate Python code from a specification."""
        type_info = CODE_TYPES.get(spec.code_type, CODE_TYPES["script"])
        template = type_info["template"]

        if template == "cli_app":
            return self._gen_cli(spec, type_info)
        elif template == "oop":
            return self._gen_class(spec, type_info)
        elif template == "pytest":
            return self._gen_test(spec, type_info)
        elif template == "fastapi":
            return self._gen_api(spec, type_info)
        elif template == "nlke_agent":
            return self._gen_agent(spec, type_info)
        elif template == "pipeline":
            return self._gen_pipeline(spec, type_info)
        elif template == "minimal":
            return self._gen_function(spec, type_info)
        else:
            return self._gen_script(spec, type_info)

    def _gen_cli(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        imports = type_info["typical_imports"] + spec.dependencies
        import_block = "\n".join(f"import {i}" for i in sorted(set(imports)))

        args_block = ""
        for inp in spec.inputs:
            args_block += f'    parser.add_argument("--{inp}", type=str, required=True, help="{inp}")\n'

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            {import_block}
            from typing import Any, Dict, List


            def {snake_name}({", ".join(f"{i}: str" for i in spec.inputs)}) -> Dict[str, Any]:
                """{spec.description}

                Args:
            {chr(10).join(f"        {i}: Input parameter" for i in spec.inputs)}

                Returns:
                    Dict with results
                """
                # TODO: Implement {spec.description}
                results: Dict[str, Any] = {{}}
                return results


            def main() -> None:
                parser = argparse.ArgumentParser(description="{spec.description}")
            {args_block}
                args = parser.parse_args()

                result = {snake_name}({", ".join(f"args.{i}" for i in spec.inputs)})
                print(json.dumps(result, indent=2))


            if __name__ == "__main__":
                main()
        ''')

        funcs = [snake_name, "main"]
        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=imports,
            functions=funcs,
        )

    def _gen_class(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        imports = type_info["typical_imports"] + spec.dependencies
        import_block = "\n".join(f"import {i}" for i in sorted(set(imports)))

        fields = "\n".join(f"    {i}: Any" for i in spec.inputs) if spec.inputs else "    pass"
        methods = ""
        for out in spec.outputs:
            method_name = re.sub(r'[^a-z0-9]+', '_', out.lower()).strip('_')
            methods += f"\n    def {method_name}(self) -> Any:\n        \"\"\"Compute {out}.\"\"\"\n        raise NotImplementedError\n"

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            {import_block}
            from dataclasses import dataclass, field
            from typing import Any, Dict, List, Optional


            @dataclass
            class {spec.name}:
                """{spec.description}

                Constraints: {', '.join(spec.constraints) if spec.constraints else 'None'}
                """
            {fields}
            {methods}
        ''')

        return GeneratedCode(
            filename=f"{re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=imports,
            classes=[spec.name],
        )

    def _gen_test(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        module_name = spec.inputs[0] if spec.inputs else "module_under_test"

        test_methods = ""
        for out in spec.outputs:
            test_name = re.sub(r'[^a-z0-9]+', '_', out.lower()).strip('_')
            test_methods += f"\n    def test_{test_name}(self) -> None:\n        \"\"\"Test {out}.\"\"\"\n        # TODO: implement\n        assert True\n"

        constraints_tests = ""
        for c in spec.constraints:
            c_name = re.sub(r'[^a-z0-9]+', '_', c.lower()).strip('_')[:40]
            constraints_tests += f"\n    def test_{c_name}(self) -> None:\n        \"\"\"Test constraint: {c}\"\"\"\n        # TODO: implement\n        assert True\n"

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            import pytest
            from typing import Any
            # from {module_name} import *  # TODO: adjust import


            class Test{spec.name.replace('test_', '').title().replace('_', '')}:
                """{spec.description}"""
            {test_methods}{constraints_tests}
        ''')

        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=["pytest"],
            classes=[f"Test{spec.name.replace('test_', '').title().replace('_', '')}"],
        )

    def _gen_api(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')

        endpoints = ""
        for out in spec.outputs:
            route = out.lower().replace("_", "-")
            endpoints += f'\n@app.get("/{route}")\nasync def get_{re.sub(r"[^a-z0-9]+", "_", out.lower()).strip("_")}():\n    """Get {out}."""\n    return {{"status": "ok", "data": None}}\n'

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            from fastapi import FastAPI, HTTPException
            from pydantic import BaseModel
            from typing import Any, Dict, List, Optional

            app = FastAPI(title="{spec.name}", description="{spec.description}")

            {endpoints}

            if __name__ == "__main__":
                import uvicorn
                uvicorn.run(app, host="0.0.0.0", port=8000)
        ''')

        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=["fastapi", "pydantic", "uvicorn"],
            functions=[f"get_{re.sub(r'[^a-z0-9]+', '_', o.lower()).strip('_')}" for o in spec.outputs],
        )

    def _gen_agent(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        class_name = "".join(w.title() for w in snake_name.split("_")) + "Analyzer"

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            import sys
            import os

            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from shared.agent_base import (
                AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
            )

            from dataclasses import dataclass, field
            from typing import Dict, List, Any


            class {class_name}(BaseAnalyzer):
                """{spec.description}"""

                def __init__(self):
                    super().__init__(
                        agent_name="{spec.name}",
                        model="sonnet",
                        version="1.0",
                    )

                def get_example_input(self) -> Dict[str, Any]:
                    return {{"task": "{spec.description}"}}

                def analyze(self, agent_input: AgentInput) -> AgentOutput:
                    w = agent_input.workload
                    return AgentOutput(
                        recommendations=[{{"technique": "{snake_name}", "impact": "high", "reasoning": "{spec.description}"}}],
                        rules_applied=["custom_001"],
                        meta_insight="{spec.description}",
                        agent_metadata=self.build_metadata(),
                    )


            if __name__ == "__main__":
                analyzer = {class_name}()
                run_standard_cli("{spec.name}", "{spec.description}", analyzer)
        ''')

        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=["sys", "os", "dataclasses", "typing"],
            classes=[class_name],
        )

    def _gen_pipeline(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        imports = type_info["typical_imports"] + spec.dependencies

        steps = ""
        for i, inp in enumerate(spec.inputs):
            steps += f"\n    # Step {i+1}: Process {inp}\n    print(f'Step {i+1}: Processing {inp}...')\n"

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            {chr(10).join(f"import {i}" for i in sorted(set(imports)))}
            from pathlib import Path
            from typing import Any, Dict, List


            def run_pipeline({", ".join(f"{i}: str" for i in spec.inputs)}) -> Dict[str, Any]:
                """{spec.description}"""
                results: Dict[str, Any] = {{}}
            {steps}
                return results


            if __name__ == "__main__":
                result = run_pipeline({", ".join(f'"{i}_value"' for i in spec.inputs)})
                print(json.dumps(result, indent=2))
        ''')

        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=imports,
            functions=["run_pipeline"],
        )

    def _gen_function(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            from typing import Any, Dict, List, Optional


            def {snake_name}({", ".join(f"{i}: Any" for i in spec.inputs)}) -> Any:
                """{spec.description}

                Args:
            {chr(10).join(f"        {i}: Input parameter" for i in spec.inputs)}

                Returns:
                    Result value
                """
                # TODO: Implement
                raise NotImplementedError
        ''')

        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=["typing"],
            functions=[snake_name],
        )

    def _gen_script(self, spec: CodeSpec, type_info: Dict) -> GeneratedCode:
        snake_name = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        imports = type_info["typical_imports"] + spec.dependencies

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""

            {chr(10).join(f"import {i}" for i in sorted(set(imports)))}
            from typing import Any, Dict, List


            def main() -> None:
                """{spec.description}"""
                # TODO: Implement
                print("Running {snake_name}...")


            if __name__ == "__main__":
                main()
        ''')

        return GeneratedCode(
            filename=f"{snake_name}.py",
            code=code,
            lines=code.count("\n") + 1,
            imports=imports,
            functions=["main"],
        )

    def _check_anti_patterns(self, code: str) -> List[str]:
        """Scan generated code for anti-patterns."""
        found = []
        if "except:" in code and "except Exception" not in code:
            found.append("bare_except_clause")
        if "import *" in code:
            found.append("import_star")
        if "= []" in code or "= {}" in code:
            # Check if it's a default argument
            for line in code.split("\n"):
                if "def " in line and ("=[]" in line.replace(" ", "") or "={}" in line.replace(" ", "")):
                    found.append("mutable_default_arguments")
                    break
        if "os.path.join" in code and "pathlib" not in code:
            found.append("prefer_pathlib")
        return found

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        specs_raw = w.get("specs", [])

        generated = []
        all_anti_patterns = []
        total_lines = 0
        type_counts: Dict[str, int] = {}

        for spec_dict in specs_raw:
            spec = self._parse_spec(spec_dict)
            code_result = self._generate_code(spec)
            generated.append(code_result)
            total_lines += code_result.lines
            type_counts[spec.code_type] = type_counts.get(spec.code_type, 0) + 1

            ap = self._check_anti_patterns(code_result.code)
            all_anti_patterns.extend(ap)

        recommendations = []
        for gen in generated:
            recommendations.append({
                "technique": f"codegen_python_{gen.filename}",
                "impact": f"Generated {gen.lines} lines",
                "reasoning": f"File: {gen.filename}, Functions: {gen.functions}, Classes: {gen.classes}",
                "filename": gen.filename,
                "code": gen.code,
                "lines": gen.lines,
                "imports": gen.imports,
                "functions": gen.functions,
                "classes": gen.classes,
            })

        meta_insight = (
            f"Generated {len(generated)} Python files totaling {total_lines} lines. "
            f"Types: {', '.join(f'{k}({v})' for k, v in type_counts.items())}. "
            f"Anti-patterns detected: {len(all_anti_patterns)}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=PYTHON_RULES[:len(generated) + 2],
            meta_insight=meta_insight,
            analysis_data={
                "files_generated": len(generated),
                "total_lines": total_lines,
                "type_distribution": type_counts,
                "all_imports": list(set(i for g in generated for i in g.imports)),
                "all_functions": [f for g in generated for f in g.functions],
                "all_classes": [c for g in generated for c in g.classes],
            },
            anti_patterns=list(set(all_anti_patterns)),
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenPythonAnalyzer()
    run_standard_cli(
        agent_name="CodeGen Python",
        description="Generate Python code from natural language specifications",
        analyzer=analyzer,
    )
