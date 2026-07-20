"""
Universal Prompt Runner - Integration Validation Script v3
===========================================================
Verifies the complete universal adapter against the SYSTEM ROLE specification.

  Output format (exact spec):
  {
    "module": "<target_module>",
    "intent": "<detected_intent>",
    "data": {
      "topic": "<main_topic>",
      "parameters": {},
      "original_prompt": "<user_input>"
    },
    "tasks": [],
    "output_format": "<expected_result_format>",
    "context": {
      "source": "prompt_runner"
    }
  }

Coverage:
  - File existence (all required files + general plugin)
  - Plugin loading (6 domains including general)
  - Contract schema (spec-compliant fields)
  - Run schema (spec-compliant output shape)
  - Domain routing: architecture, legal, finance, healthcare, software
  - Spec-style structured input with explicit topic field
  - Topic extraction from natural language prompts
  - tasks array populated per domain intent
  - output_format present per domain intent
  - data.parameters contains extracted data
  - context has ONLY source field
  - Universal prompt handling (general domain fallback)
  - Determinism across all 5 domains
  - Error handling
  - Complete instruction fields check
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from platform_adapter import (
    PlatformAdapter,
    PluginLoader,
    PLUGINS_DIR,
)


class ValidationResult:
    def __init__(self):
        self.passed: List[str] = []
        self.failed: List[Tuple[str, str]] = []
        self.warnings: List[str] = []

    def ok(self, name: str):
        self.passed.append(name)

    def fail(self, name: str, reason: str):
        self.failed.append((name, reason))

    def warn(self, msg: str):
        self.warnings.append(msg)

    @property
    def all_passed(self) -> bool:
        return len(self.failed) == 0

    def summary(self) -> str:
        lines = [
            "=" * 65,
            "UNIVERSAL PROMPT RUNNER — VALIDATION SUMMARY",
            "=" * 65,
            f"  Passed  : {len(self.passed)}",
            f"  Failed  : {len(self.failed)}",
            f"  Warnings: {len(self.warnings)}",
            "=" * 65,
        ]
        if self.passed:
            lines.append("\nPASSED:")
            for t in self.passed:
                lines.append(f"  ✓  {t}")
        if self.failed:
            lines.append("\nFAILED:")
            for t, r in self.failed:
                lines.append(f"  ✗  {t}")
                lines.append(f"       → {r}")
        if self.warnings:
            lines.append("\nWARNINGS:")
            for w in self.warnings:
                lines.append(f"  ⚠  {w}")
        lines += [
            "\n" + "=" * 65,
            "RESULT: " + ("ALL VALIDATIONS PASSED ✓" if self.all_passed else "VALIDATION FAILED ✗"),
            "=" * 65,
        ]
        return "\n".join(lines)


class IntegrationValidator:
    def __init__(self):
        self.base = Path(__file__).parent
        self.r = ValidationResult()

    def run_all(self) -> ValidationResult:
        print("Running Universal Prompt Runner Integration Validation...\n")
        self._check_required_files()
        self._check_plugin_files()
        self._check_registry_files()
        self._validate_contract_schema()
        self._validate_run_schema()
        self._test_plugin_loading()
        self._test_health_check()
        self._test_adapter_init()
        self._test_architecture_domain()
        self._test_legal_domain()
        self._test_finance_domain()
        self._test_healthcare_domain()
        self._test_software_domain()
        self._test_structured_request()
        self._test_topic_field_in_structured()
        self._test_context_shape()
        self._test_tasks_and_output_format()
        self._test_universal_prompt()
        self._test_determinism_all_domains()
        self._test_unknown_prompt()
        self._test_error_handling()
        self._test_instruction_fields_complete()
        return self.r

    # ------------------------------------------------------------------
    # File existence
    # ------------------------------------------------------------------

    def _check_required_files(self):
        files = [
            "platform_adapter.py",
            "contract.json",
            "run_schema.json",
            "demo_run.json",
            "validate_integration.py",
            "domain_registry.json",
            "module_registry.json",
            "DEMO_MODE_AUTHORITY.md",
            "FINAL_HANDOVER_NOTE.md",
            "CONFIRMATION_NOTE.md",
        ]
        for f in files:
            if (self.base / f).exists():
                self.r.ok(f"File exists: {f}")
            else:
                self.r.fail(f"File exists: {f}", "File not found")

    def _check_plugin_files(self):
        domains = ["architecture", "legal", "finance", "healthcare", "software", "general"]
        for d in domains:
            path = self.base / "plugins" / d / "plugin.json"
            if path.exists():
                self.r.ok(f"Plugin file exists: plugins/{d}/plugin.json")
            else:
                self.r.fail(f"Plugin file exists: plugins/{d}/plugin.json", "File not found")

    def _check_registry_files(self):
        for fname in ["domain_registry.json", "module_registry.json"]:
            path = self.base / fname
            if not path.exists():
                self.r.fail(f"Registry: {fname} exists", "Not found")
                return
            with open(path) as f:
                data = json.load(f)
            if "version" in data:
                self.r.ok(f"Registry {fname} has version field")
            else:
                self.r.fail(f"Registry {fname} version", "Missing")

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def _validate_contract_schema(self):
        try:
            with open(self.base / "contract.json") as f:
                c = json.load(f)
            for section in ["definitions", "input", "output", "routing_model"]:
                if section in c:
                    self.r.ok(f"Contract has '{section}'")
                else:
                    self.r.fail(f"Contract '{section}'", "Missing section")
            inst = c.get("definitions", {}).get("instruction", {}).get("properties", {})
            for field in ["module", "intent", "data", "tasks", "output_format", "context"]:
                if field in inst:
                    self.r.ok(f"Contract instruction has '{field}'")
                else:
                    self.r.fail(f"Contract instruction '{field}'", "Missing")
            data_props = inst.get("data", {}).get("properties", {})
            for field in ["topic", "parameters", "original_prompt"]:
                if field in data_props:
                    self.r.ok(f"Contract data has '{field}'")
                else:
                    self.r.fail(f"Contract data '{field}'", "Missing")
            ctx = inst.get("context", {}).get("properties", {})
            if "source" in ctx:
                self.r.ok("Contract context has 'source'")
            else:
                self.r.fail("Contract context 'source'", "Missing")
            extra_ctx = [k for k in ctx if k != "source"]
            if not extra_ctx:
                self.r.ok("Contract context has no extra fields (spec-compliant)")
            else:
                self.r.fail("Contract context extra fields", f"Found: {extra_ctx}")
            for removed_field in ["task", "domain"]:
                if removed_field not in inst:
                    self.r.ok(f"Contract instruction correctly omits '{removed_field}'")
                else:
                    self.r.fail(f"Contract instruction '{removed_field}'", "Should not be present (spec)")
            si = c.get("definitions", {}).get("structuredInput", {}).get("properties", {})
            if "topic" in si:
                self.r.ok("Contract structuredInput has 'topic' field")
            else:
                self.r.fail("Contract structuredInput 'topic'", "Missing")
        except Exception as e:
            self.r.fail("Contract schema validation", str(e))

    def _validate_run_schema(self):
        try:
            with open(self.base / "run_schema.json") as f:
                s = json.load(f)
            for prop in ["run_id", "timestamp", "input", "output", "status", "metadata", "pipeline"]:
                if prop in s.get("properties", {}):
                    self.r.ok(f"Run schema has '{prop}'")
                else:
                    self.r.fail(f"Run schema '{prop}'", "Missing")
            pipeline_stages = s.get("properties", {}).get("pipeline", {}).get("properties", {})
            for stage in ["stage_1_domain_detection", "stage_2_intent_detection",
                          "stage_3_entity_extraction", "stage_4_constraint_extraction",
                          "stage_5_instruction_build"]:
                if stage in pipeline_stages:
                    self.r.ok(f"Run schema pipeline has '{stage}'")
                else:
                    self.r.fail(f"Run schema pipeline '{stage}'", "Missing")
            out_instr = (s.get("properties", {})
                          .get("output", {})
                          .get("properties", {})
                          .get("instruction", {})
                          .get("properties", {}))
            for field in ["module", "intent", "data", "tasks", "output_format", "context"]:
                if field in out_instr:
                    self.r.ok(f"Run schema output.instruction has '{field}'")
                else:
                    self.r.fail(f"Run schema output.instruction '{field}'", "Missing")
        except Exception as e:
            self.r.fail("Run schema validation", str(e))

    # ------------------------------------------------------------------
    # Plugin loading
    # ------------------------------------------------------------------

    def _test_plugin_loading(self):
        loader = PluginLoader()
        domains = loader.domains
        expected = {"architecture", "legal", "finance", "healthcare", "software", "general"}
        for d in expected:
            if d in domains:
                self.r.ok(f"PluginLoader: domain '{d}' loaded")
            else:
                self.r.fail(f"PluginLoader: domain '{d}'", "Not loaded")
        if len(domains) >= 6:
            self.r.ok(f"PluginLoader: {len(domains)} domains loaded (>= 6)")
        else:
            self.r.warn(f"Expected >= 6 domains, got {len(domains)}")

    # ------------------------------------------------------------------
    # Health check & adapter init
    # ------------------------------------------------------------------

    def _test_health_check(self):
        adapter = PlatformAdapter()
        h = adapter.health_check()
        if h.get("status") == "healthy":
            self.r.ok("Health check: status = healthy")
        else:
            self.r.fail("Health check", "status not healthy")
        if h.get("ready"):
            self.r.ok("Health check: ready = True")
        else:
            self.r.fail("Health check ready", "Not ready")
        if h.get("domain_count", 0) >= 6:
            self.r.ok(f"Health check: {h.get('domain_count')} domains listed")
        else:
            self.r.fail("Health check domain_count", f"Got {h.get('domain_count')}, expected >= 6")
        if h.get("version") == "2.0.0":
            self.r.ok("Adapter version = 2.0.0")
        else:
            self.r.fail("Adapter version", f"Got {h.get('version')}, expected 2.0.0")

    def _test_adapter_init(self):
        adapter = PlatformAdapter()
        if adapter.prompt_runner:
            self.r.ok("Adapter has PromptRunner")
        else:
            self.r.fail("Adapter init", "No PromptRunner")
        if adapter.prompt_runner.plugin_loader:
            self.r.ok("PromptRunner has PluginLoader")
        else:
            self.r.fail("Adapter init", "No PluginLoader")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _route(self, prompt: str) -> Dict[str, Any]:
        return PlatformAdapter().process(prompt).get("instruction", {})

    def _assert_instruction(self, instr: Dict, label: str,
                            module: str = None, intent: str = None):
        if module and instr.get("module") == module:
            self.r.ok(f"{label}: module = {module}")
        elif module:
            self.r.fail(f"{label} module", f"Expected '{module}', got '{instr.get('module')}'")
        if intent and instr.get("intent") == intent:
            self.r.ok(f"{label}: intent = {intent}")
        elif intent:
            self.r.fail(f"{label} intent", f"Expected '{intent}', got '{instr.get('intent')}'")

    # ------------------------------------------------------------------
    # Domain routing tests
    # ------------------------------------------------------------------

    def _test_architecture_domain(self):
        i = self._route("Design a residential building for a 1000 sqft plot in Mumbai.")
        self._assert_instruction(i, "Architecture routing",
                                 module="architecture_design", intent="design_building")
        params = i.get("data", {}).get("parameters", {})
        if params.get("plot_size") == "1000 sqft":
            self.r.ok("Architecture: plot_size extracted into parameters")
        else:
            self.r.fail("Architecture plot_size", f"Got '{params.get('plot_size')}'")
        if params.get("building_type") == "residential":
            self.r.ok("Architecture: building_type extracted into parameters")
        else:
            self.r.fail("Architecture building_type", f"Got '{params.get('building_type')}'")
        tasks = i.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            self.r.ok(f"Architecture: tasks list has {len(tasks)} items")
        else:
            self.r.fail("Architecture tasks", f"Expected non-empty list, got {tasks}")
        if i.get("output_format") == "design_document":
            self.r.ok("Architecture: output_format = design_document")
        else:
            self.r.fail("Architecture output_format", f"Got '{i.get('output_format')}'")
        topic = i.get("data", {}).get("topic", "")
        if topic:
            self.r.ok(f"Architecture: topic extracted = '{topic[:60]}'")
        else:
            self.r.fail("Architecture topic", "topic is empty")

    def _test_legal_domain(self):
        i = self._route("Contract review for risk analysis under Indian law.")
        self._assert_instruction(i, "Legal routing",
                                 module="legal_compliance", intent="analyze_contract")
        tasks = i.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            self.r.ok(f"Legal: tasks list has {len(tasks)} items")
        else:
            self.r.fail("Legal tasks", f"Expected non-empty list, got {tasks}")
        if i.get("output_format") == "analysis_report":
            self.r.ok("Legal: output_format = analysis_report")
        else:
            self.r.fail("Legal output_format", f"Got '{i.get('output_format')}'")

    def _test_finance_domain(self):
        i = self._route("Calculate the ROI for a 50 lakh investment over 5 years.")
        self._assert_instruction(i, "Finance routing",
                                 module="investment_analyzer", intent="analyze_investment")
        tasks = i.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            self.r.ok(f"Finance: tasks list has {len(tasks)} items")
        else:
            self.r.fail("Finance tasks", f"Expected non-empty list, got {tasks}")
        if i.get("output_format") == "investment_analysis":
            self.r.ok("Finance: output_format = investment_analysis")
        else:
            self.r.fail("Finance output_format", f"Got '{i.get('output_format')}'")

    def _test_healthcare_domain(self):
        i = self._route("Provide a patient assessment for a case of diabetes.")
        self._assert_instruction(i, "Healthcare routing",
                                 module="patient_assessor", intent="patient_assessment")
        tasks = i.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            self.r.ok(f"Healthcare: tasks list has {len(tasks)} items")
        else:
            self.r.fail("Healthcare tasks", f"Expected non-empty list, got {tasks}")
        if i.get("output_format") == "assessment_report":
            self.r.ok("Healthcare: output_format = assessment_report")
        else:
            self.r.fail("Healthcare output_format", f"Got '{i.get('output_format')}'")

    def _test_software_domain(self):
        i = self._route("Design the database schema for a scalable web application.")
        self._assert_instruction(i, "Software routing",
                                 module="database_designer", intent="database_design")
        tasks = i.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            self.r.ok(f"Software: tasks list has {len(tasks)} items")
        else:
            self.r.fail("Software tasks", f"Expected non-empty list, got {tasks}")
        if i.get("output_format") == "database_schema":
            self.r.ok("Software: output_format = database_schema")
        else:
            self.r.fail("Software output_format", f"Got '{i.get('output_format')}'")
    # ------------------------------------------------------------------
    # Structured request (spec-style)
    # ------------------------------------------------------------------

    def _test_structured_request(self):
        adapter = PlatformAdapter()
        req = {
            "domain": "architecture",
            "intent": "design_building",
            "data": {"plot_size": "2000 sqft", "city": "Delhi"},
        }
        result = adapter.process(req)
        if result.get("status") == "success":
            self.r.ok("Structured request: succeeds")
        else:
            self.r.fail("Structured request", result.get("error", "unknown"))
        i = result.get("instruction", {})
        params = i.get("data", {}).get("parameters", {})
        if params.get("plot_size") == "2000 sqft" and params.get("city") == "Delhi":
            self.r.ok("Structured request: provided data in parameters")
        else:
            self.r.fail("Structured request parameters", f"Got: {params}")
        tasks = i.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            self.r.ok("Structured request: tasks list populated")
        else:
            self.r.fail("Structured request tasks", f"Got: {tasks}")

    def _test_topic_field_in_structured(self):
        """Spec-style input: {intent, domain, topic} → data.topic = provided value."""
        adapter = PlatformAdapter()
        req = {
            "domain": "legal",
            "intent": "analyze_contract",
            "topic": "employment contract under Indian law",
        }
        result = adapter.process(req)
        if result.get("status") == "success":
            self.r.ok("Topic-field structured request: succeeds")
        else:
            self.r.fail("Topic-field structured request", result.get("error", "unknown"))
        i = result.get("instruction", {})
        topic = i.get("data", {}).get("topic", "")
        if topic == "employment contract under Indian law":
            self.r.ok("Topic-field: data.topic = explicitly provided value")
        else:
            self.r.fail("Topic-field data.topic", f"Got '{topic}'")
        if i.get("module") == "legal_compliance":
            self.r.ok("Topic-field: module = legal_compliance")
        else:
            self.r.fail("Topic-field module", f"Got '{i.get('module')}'")

    # ------------------------------------------------------------------
    # Context shape
    # ------------------------------------------------------------------

    def _test_context_shape(self):
        """Context must contain ONLY source field (spec requirement)."""
        prompts = [
            "Design a residential building for a 1000 sqft plot in Mumbai.",
            "Contract review for risk analysis under Indian law.",
            "Calculate the ROI for a 50 lakh investment over 5 years.",
        ]
        for prompt in prompts:
            i = self._route(prompt)
            ctx = i.get("context", {})
            if ctx.get("source") == "prompt_runner":
                self.r.ok(f"Context source = 'prompt_runner'")
            else:
                self.r.fail(f"Context source", f"Got '{ctx.get('source')}' for '{prompt[:40]}'")
            extra = [k for k in ctx if k != "source"]
            if not extra:
                self.r.ok(f"Context has no extra fields (spec-compliant)")
            else:
                self.r.fail(f"Context extra fields", f"Found {extra}")

    # ------------------------------------------------------------------
    # Tasks and output_format per domain
    # ------------------------------------------------------------------

    def _test_tasks_and_output_format(self):
        """Every domain prompt should produce non-empty tasks and correct output_format."""
        cases = [
            ("Design a residential building for a 1000 sqft plot.", "design_document"),
            ("Contract review for risk analysis under Indian law.", "analysis_report"),
            ("Calculate the ROI for a 50 lakh investment over 5 years.", "investment_analysis"),
            ("Provide a patient assessment for a case of diabetes.", "assessment_report"),
            ("Design the database schema for a web application.", "database_schema"),
        ]
        for prompt, expected_fmt in cases:
            i = self._route(prompt)
            tasks = i.get("tasks", [])
            fmt = i.get("output_format", "")
            if isinstance(tasks, list) and len(tasks) >= 1:
                self.r.ok(f"tasks non-empty ({len(tasks)} items): '{prompt[:40]}'")
            else:
                self.r.fail("tasks", f"Empty or missing for '{prompt[:40]}'")
            if fmt == expected_fmt:
                self.r.ok(f"output_format = '{fmt}'")
            else:
                self.r.fail(f"output_format", f"Expected '{expected_fmt}', got '{fmt}'")

    # ------------------------------------------------------------------
    # Universal prompt handling
    # ------------------------------------------------------------------

    def _test_universal_prompt(self):
        """Prompts that don't match a specific domain should still produce valid output."""
        adapter = PlatformAdapter()
        general_prompts = [
            "Explain the theory of relativity.",
            "Summarize the key events of World War II.",
        ]
        for prompt in general_prompts:
            result = adapter.process(prompt)
            if result.get("status") == "success":
                self.r.ok(f"Universal: succeeds for '{prompt[:50]}'")
            else:
                self.r.fail(f"Universal prompt", f"Failed: '{prompt[:50]}'")
            i = result.get("instruction", {})
            tasks = i.get("tasks", [])
            if isinstance(tasks, list) and len(tasks) > 0:
                self.r.ok(f"Universal: tasks populated for general prompt")
            else:
                self.r.fail("Universal tasks", f"Empty for: '{prompt[:50]}'")
            if i.get("output_format"):
                self.r.ok(f"Universal: output_format present for general prompt")
            else:
                self.r.fail("Universal output_format", "Missing")

    # ------------------------------------------------------------------
    # Determinism across all domains
    # ------------------------------------------------------------------

    def _test_determinism_all_domains(self):
        prompts = [
            "Design a residential building for a 1000 sqft plot in Mumbai.",
            "Contract review for risk analysis under Indian law.",
            "Calculate the ROI for a 50 lakh investment over 5 years.",
            "Provide a patient assessment for a case of diabetes.",
            "Design the database schema for a scalable web application.",
        ]
        for prompt in prompts:
            i1 = self._route(prompt)
            i2 = self._route(prompt)
            if i1 == i2:
                self.r.ok(f"Determinism: identical output for '{prompt[:45]}'")
            else:
                self.r.fail(f"Determinism", f"Output differs for '{prompt[:45]}'")

    # ------------------------------------------------------------------
    # Unknown / ambiguous prompt
    # ------------------------------------------------------------------

    def _test_unknown_prompt(self):
        i = self._route("qwerty xyzzy florp bloop")
        if i.get("module"):
            self.r.ok("Unknown prompt: module field present (graceful fallback)")
        else:
            self.r.fail("Unknown prompt", "module missing")
        if isinstance(i.get("tasks"), list):
            self.r.ok("Unknown prompt: tasks is a list (graceful fallback)")
        else:
            self.r.fail("Unknown prompt tasks", "tasks is not a list")

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _test_error_handling(self):
        adapter = PlatformAdapter()
        result = adapter.process("")
        if result.get("status") == "error":
            self.r.ok("Error handling: empty string rejected")
        else:
            self.r.fail("Error handling empty string", "Expected error status")
        result2 = adapter.process(None)
        if result2.get("status") == "error":
            self.r.ok("Error handling: None input rejected")
        else:
            self.r.fail("Error handling None input", "Expected error status")

    # ------------------------------------------------------------------
    # Complete instruction fields check
    # ------------------------------------------------------------------

    def _test_instruction_fields_complete(self):
        i = self._route("Design a residential building for a 1000 sqft plot in Mumbai.")
        required_top = ["module", "intent", "data", "tasks", "output_format", "context"]
        for field in required_top:
            if field in i:
                self.r.ok(f"Instruction has required field '{field}'")
            else:
                self.r.fail(f"Instruction field '{field}'", "Missing")
        data = i.get("data", {})
        for df in ["topic", "parameters", "original_prompt"]:
            if df in data:
                self.r.ok(f"Instruction data has '{df}'")
            else:
                self.r.fail(f"Instruction data.{df}", "Missing")
        if isinstance(data.get("parameters"), dict):
            self.r.ok("Instruction data.parameters is a dict")
        else:
            self.r.fail("Instruction data.parameters type", "Not a dict")
        if isinstance(i.get("tasks"), list):
            self.r.ok("Instruction tasks is a list")
        else:
            self.r.fail("Instruction tasks type", "Not a list")
        if isinstance(i.get("output_format"), str) and i.get("output_format"):
            self.r.ok("Instruction output_format is a non-empty string")
        else:
            self.r.fail("Instruction output_format", "Missing or empty")
        ctx = i.get("context", {})
        if list(ctx.keys()) == ["source"]:
            self.r.ok("Instruction context has exactly {source} (spec-compliant)")
        else:
            self.r.fail("Instruction context keys", f"Expected only ['source'], got {list(ctx.keys())}")
        forbidden = ["task", "domain", "confidence", "deterministic_hash",
                     "requires_clarification", "fallback_candidates"]
        for f in forbidden:
            if f not in i:
                self.r.ok(f"Instruction correctly omits '{f}'")
            else:
                self.r.fail(f"Instruction '{f}'", "Should not be present (spec)")


def main():
    validator = IntegrationValidator()
    result = validator.run_all()
    print(result.summary())
    sys.exit(0 if result.all_passed else 1)


if __name__ == "__main__":
    main()
