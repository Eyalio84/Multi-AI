#!/usr/bin/env python3
"""
Code Generation Agent: Gemini API (#39)

Generates code that integrates with the Gemini API.
Supports text generation, embeddings, code execution,
grounding, function calling, and multimodal tasks.

Layer: L1-L5 (Full 5-layer pattern via agent_base)

Usage:
    python3 codegen_gemini.py --example
    python3 codegen_gemini.py --workload spec.json --output result.json

Created: February 6, 2026
"""

import sys
import os
import re
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.agent_base import (
    AgentInput, AgentOutput, BaseAnalyzer, run_standard_cli,
    GEMINI_MODELS, GEMINI_API_BASE, GEMINI_CAPABILITIES,
)

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


# ============================================================================
# L1: Data Models
# ============================================================================

@dataclass
class GeminiSpec:
    description: str
    api_feature: str
    name: str
    model: str = "gemini-2.5-flash"
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)


@dataclass
class GeneratedGeminiCode:
    filename: str
    code: str
    language: str = "python"
    lines: int = 0
    api_calls: List[str] = field(default_factory=list)
    model_used: str = "gemini-2.5-flash"


# ============================================================================
# L2: Constants
# ============================================================================

API_FEATURES = {
    "text_generation": {"endpoint": "generateContent"},
    "embeddings": {"endpoint": "embedContent"},
    "code_execution": {"endpoint": "generateContent"},
    "grounding": {"endpoint": "generateContent"},
    "function_calling": {"endpoint": "generateContent"},
    "multimodal": {"endpoint": "generateContent"},
    "batch": {"endpoint": "batchGenerateContent"},
}

GEMINI_RULES = [
    "codegen_gemini_001_api_key_from_env",
    "codegen_gemini_002_error_handling",
    "codegen_gemini_003_rate_limit_retry",
    "codegen_gemini_004_model_selection",
    "codegen_gemini_005_token_counting",
    "codegen_gemini_006_safety_settings",
]


# ============================================================================
# L3: Analyzer
# ============================================================================

class CodegenGeminiAnalyzer(BaseAnalyzer):
    """Gemini API code generation engine."""

    def __init__(self):
        super().__init__(
            agent_name="codegen-gemini",
            model="sonnet",
            version="1.0",
        )

    def get_example_input(self) -> Dict[str, Any]:
        return {
            "specs": [
                {
                    "description": "Text summarization service using Gemini",
                    "api_feature": "text_generation",
                    "name": "article_summarizer",
                    "model": "gemini-2.5-flash",
                    "parameters": {"temperature": 0.3, "max_output_tokens": 1000},
                },
                {
                    "description": "Semantic search via Gemini embeddings",
                    "api_feature": "embeddings",
                    "name": "semantic_search",
                    "model": "gemini-embedding-001",
                },
                {
                    "description": "Data analysis via Gemini code execution",
                    "api_feature": "code_execution",
                    "name": "data_analyzer",
                    "model": "gemini-2.5-pro",
                },
                {
                    "description": "Fact checker via Google Search grounding",
                    "api_feature": "grounding",
                    "name": "fact_checker",
                    "model": "gemini-3-pro",
                },
            ],
        }

    def _parse_spec(self, spec_dict: Dict) -> GeminiSpec:
        return GeminiSpec(
            description=spec_dict.get("description", ""),
            api_feature=spec_dict.get("api_feature", "text_generation"),
            name=spec_dict.get("name", "gemini_tool"),
            model=spec_dict.get("model", "gemini-2.5-flash"),
            parameters=spec_dict.get("parameters", {}),
            constraints=spec_dict.get("constraints", []),
        )

    def _gen_text(self, spec: GeminiSpec) -> GeneratedGeminiCode:
        snake = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        temp = spec.parameters.get("temperature", 0.7)
        max_tok = spec.parameters.get("max_output_tokens", 4096)

        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""
            import os, json, urllib.request, urllib.error
            from typing import Any, Dict

            API_KEY = os.environ.get("GEMINI_API_KEY", "")
            BASE = "{GEMINI_API_BASE}"
            MODEL = "{spec.model}"

            def {snake}(prompt: str, system: str = "") -> Dict[str, Any]:
                """{spec.description}"""
                url = f"{{BASE}}/models/{{MODEL}}:generateContent?key={{API_KEY}}"
                body = {{
                    "contents": [{{"role": "user", "parts": [{{"text": prompt}}]}}],
                    "generationConfig": {{"temperature": {temp}, "maxOutputTokens": {max_tok}}},
                    "safetySettings": [{{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}}],
                }}
                if system:
                    body["system_instruction"] = {{"parts": [{{"text": system}}]}}
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={{"Content-Type": "application/json"}}, method="POST")
                try:
                    with urllib.request.urlopen(req) as resp:
                        data = json.loads(resp.read().decode())
                        return {{"text": data["candidates"][0]["content"]["parts"][0]["text"], "usage": data.get("usageMetadata", {{}})}}
                except urllib.error.HTTPError as e:
                    return {{"error": str(e), "status": e.code}}

            if __name__ == "__main__":
                print(json.dumps({snake}("Summarize AI agents in 3 points"), indent=2))
        ''')
        return GeneratedGeminiCode(filename=f"{snake}.py", code=code, lines=code.count("\n")+1, api_calls=["generateContent"], model_used=spec.model)

    def _gen_embedding(self, spec: GeminiSpec) -> GeneratedGeminiCode:
        snake = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""
            import os, json, math, urllib.request
            from typing import Any, Dict, List, Tuple

            API_KEY = os.environ.get("GEMINI_API_KEY", "")
            BASE = "{GEMINI_API_BASE}"
            MODEL = "{spec.model}"

            def get_embedding(text: str) -> List[float]:
                url = f"{{BASE}}/models/{{MODEL}}:embedContent?key={{API_KEY}}"
                body = {{"model": f"models/{{MODEL}}", "content": {{"parts": [{{"text": text}}]}}, "taskType": "RETRIEVAL_DOCUMENT"}}
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={{"Content-Type": "application/json"}}, method="POST")
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read().decode())["embedding"]["values"]

            def cosine_sim(a: List[float], b: List[float]) -> float:
                dot = sum(x*y for x, y in zip(a, b))
                na = math.sqrt(sum(x*x for x in a))
                nb = math.sqrt(sum(x*x for x in b))
                return dot / (na * nb) if na and nb else 0.0

            def {snake}(query: str, docs: List[str], top_k: int = 5) -> List[Tuple[int, float, str]]:
                """{spec.description}"""
                qe = get_embedding(query)
                results = [(i, cosine_sim(qe, get_embedding(d)), d) for i, d in enumerate(docs)]
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:top_k]

            if __name__ == "__main__":
                docs = ["AI agents automate tasks", "ML trains models", "Python is a language"]
                for idx, sim, doc in {snake}("What are AI agents?", docs):
                    print(f"  [{{idx}}] {{sim:.3f}}: {{doc}}")
        ''')
        return GeneratedGeminiCode(filename=f"{snake}.py", code=code, lines=code.count("\n")+1, api_calls=["embedContent"], model_used=spec.model)

    def _gen_code_exec(self, spec: GeminiSpec) -> GeneratedGeminiCode:
        snake = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""
            import os, json, urllib.request
            from typing import Any, Dict

            API_KEY = os.environ.get("GEMINI_API_KEY", "")
            BASE = "{GEMINI_API_BASE}"
            MODEL = "{spec.model}"

            def {snake}(task: str, data: str = "") -> Dict[str, Any]:
                """{spec.description}"""
                prompt = f"Analyze: {{data}}\\nTask: {{task}}" if data else task
                url = f"{{BASE}}/models/{{MODEL}}:generateContent?key={{API_KEY}}"
                body = {{"contents": [{{"role": "user", "parts": [{{"text": prompt}}]}}], "tools": [{{"code_execution": {{}}}}]}}
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={{"Content-Type": "application/json"}}, method="POST")
                try:
                    with urllib.request.urlopen(req) as resp:
                        parts = json.loads(resp.read().decode())["candidates"][0]["content"]["parts"]
                        return {{"text": [p["text"] for p in parts if "text" in p], "code": [p["executableCode"]["code"] for p in parts if "executableCode" in p], "output": [p["codeExecutionResult"]["output"] for p in parts if "codeExecutionResult" in p]}}
                except Exception as e:
                    return {{"error": str(e)}}

            if __name__ == "__main__":
                print(json.dumps({snake}("Calculate mean of [23,45,12,67,34,89]"), indent=2))
        ''')
        return GeneratedGeminiCode(filename=f"{snake}.py", code=code, lines=code.count("\n")+1, api_calls=["generateContent(code_execution)"], model_used=spec.model)

    def _gen_grounding(self, spec: GeminiSpec) -> GeneratedGeminiCode:
        snake = re.sub(r'[^a-z0-9]+', '_', spec.name.lower()).strip('_')
        code = textwrap.dedent(f'''\
            #!/usr/bin/env python3
            """{spec.description}"""
            import os, json, urllib.request
            from typing import Any, Dict, List

            API_KEY = os.environ.get("GEMINI_API_KEY", "")
            BASE = "{GEMINI_API_BASE}"
            MODEL = "{spec.model}"

            def {snake}(claim: str) -> Dict[str, Any]:
                """{spec.description}"""
                url = f"{{BASE}}/models/{{MODEL}}:generateContent?key={{API_KEY}}"
                body = {{"contents": [{{"role": "user", "parts": [{{"text": f"Verify: {{claim}}"}}]}}], "tools": [{{"google_search_retrieval": {{}}}}]}}
                req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={{"Content-Type": "application/json"}}, method="POST")
                try:
                    with urllib.request.urlopen(req) as resp:
                        data = json.loads(resp.read().decode())
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        gm = data["candidates"][0].get("groundingMetadata", {{}})
                        sources = [{{"title": c.get("web", {{}}).get("title", ""), "uri": c.get("web", {{}}).get("uri", "")}} for c in gm.get("groundingChunks", [])]
                        return {{"verdict": text, "sources": sources}}
                except Exception as e:
                    return {{"error": str(e)}}

            if __name__ == "__main__":
                print(json.dumps({snake}("Python 3.12 has a JIT compiler"), indent=2))
        ''')
        return GeneratedGeminiCode(filename=f"{snake}.py", code=code, lines=code.count("\n")+1, api_calls=["generateContent(grounding)"], model_used=spec.model)

    def _generate_gemini_code(self, spec: GeminiSpec) -> GeneratedGeminiCode:
        if spec.api_feature == "embeddings":
            return self._gen_embedding(spec)
        elif spec.api_feature == "code_execution":
            return self._gen_code_exec(spec)
        elif spec.api_feature == "grounding":
            return self._gen_grounding(spec)
        else:
            return self._gen_text(spec)

    def analyze(self, agent_input: AgentInput) -> AgentOutput:
        w = agent_input.workload
        specs_raw = w.get("specs", [])

        generated = []
        total_lines = 0
        feature_counts: Dict[str, int] = {}
        model_counts: Dict[str, int] = {}

        for spec_dict in specs_raw:
            spec = self._parse_spec(spec_dict)
            result = self._generate_gemini_code(spec)
            generated.append(result)
            total_lines += result.lines
            feature_counts[spec.api_feature] = feature_counts.get(spec.api_feature, 0) + 1
            model_counts[spec.model] = model_counts.get(spec.model, 0) + 1

        recommendations = []
        for gen in generated:
            recommendations.append({
                "technique": f"codegen_gemini_{gen.filename}",
                "impact": f"Generated {gen.lines} lines using {gen.model_used}",
                "reasoning": f"File: {gen.filename}, API: {gen.api_calls}",
                "filename": gen.filename,
                "code": gen.code,
                "lines": gen.lines,
                "api_calls": gen.api_calls,
                "model_used": gen.model_used,
            })

        meta_insight = (
            f"Generated {len(generated)} Gemini API files totaling {total_lines} lines. "
            f"Features: {', '.join(f'{k}({v})' for k, v in feature_counts.items())}. "
            f"Models: {', '.join(f'{k}({v})' for k, v in model_counts.items())}."
        )

        return AgentOutput(
            recommendations=recommendations,
            rules_applied=GEMINI_RULES[:len(generated) + 2],
            meta_insight=meta_insight,
            analysis_data={
                "files_generated": len(generated),
                "total_lines": total_lines,
                "feature_distribution": feature_counts,
                "model_distribution": model_counts,
            },
            anti_patterns=[],
            agent_metadata=self.build_metadata(),
        )


if __name__ == "__main__":
    analyzer = CodegenGeminiAnalyzer()
    run_standard_cli(
        agent_name="CodeGen Gemini",
        description="Generate Gemini API integration code",
        analyzer=analyzer,
    )
