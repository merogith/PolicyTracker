"""Publish exact configured prompt sources to the allowlisted prototype catalog.

No document content, secrets, inference or historical run receipts are included.
"""
import hashlib
import json
from pathlib import Path
from policytracker.engineering import compose_v2, fingerprint_packet

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build():
    method = read("config/methodology.json")
    pipeline = read("config/v2/pipelines.json")
    tasks = read("config/operations/tasks.json")["tasks"]
    entries = []

    def add(path, label, group, role, route=None, schema=None):
        raw = (ROOT / path).read_bytes()
        entries.append({"path": path, "label": label, "group": group, "role": role,
                        "route": route, "schema": schema, "sha256": hashlib.sha256(raw).hexdigest(),
                        "content": raw.decode("utf-8")})

    add(pipeline["shared_contract"], "Evidence contract", "shared", "Rules included in v2 evidence and analysis requests; visual page recovery has its own standalone instructions.")
    add(pipeline["labeling_contract"], "Labeling rules", "shared", "Consistent categories and independent facets in v2 evidence and analysis requests; not appended to visual page recovery.")
    add("prompts/v2/14-recover-page.md", "Recover difficult pages automatically", "country",
        "Conditional visual transcription before triage; the selected connection receives a hash-bound page image and native/OCR readings. No human review gate.")
    labels = {"triage": "Identify documents", "translate": "Prepare aligned English",
              "extract": "Extract evidence", "reconcile": "Reconcile documents",
              "quality": "Check evidence and reports", "prime": "Write the Country Profile",
              "relabel": "Relabel existing evidence", "briefing": "Prepare a brief",
              "focused_analysis": "Focused evidence analysis", "comparison": "Compare policies",
              "workplan": "Delivery gaps and support options", "chat": "Evidence-grounded chat"}
    for route, spec in pipeline["routes"].items():
        execution = spec.get("execution", "prepared" if route in ("quality", "relabel", "chat") else
                             "analysis" if route in ("briefing", "focused_analysis", "comparison", "workplan") else "country")
        group = "utility" if execution == "prepared" else execution
        role = "Active country worker route." if group == "country" else "Active optional analysis route." if group == "analysis" else "Prepared extension; not dispatched by the local worker."
        add("prompts/v2/" + spec["prompt"], labels[route], group, role, route,
            "schemas/v2/" + spec["schema"] + ".schema.json")
    add("prompts/operations/00-request-contract.md", "Operational request contract", "operations",
        "Appended to the four evidence analysis tasks; defines how selected options affect the output. Independent translation uses only its translation supplement.")
    for task in tasks:
        add(task["supplement"], task["label"] + " — selected options", "operations",
            "Appended after the shared translation route; no operational request contract." if task["id"] == "translate" else
            "Appended after the route prompt and operational contract for this task.")
    method["prompts"] = entries
    method["analysis_tasks"] = [{"id": t["id"], "label": t["label"], "description": t["description"],
                                  "route": t["route"], "artifact": t["artifact"],
                                  "supplement": t["supplement"]} for t in tasks]
    method["pipeline_version"] = pipeline["version"]
    method["execution_note"] = pipeline.get("execution_note", "The local worker dispatches active country and analysis routes; prepared extensions and reference stages are not execution receipts.")
    # Derive the visible assembly order from the real offline composer.
    method["assemblies"] = []
    for route in pipeline["routes"]:
        packet = compose_v2(ROOT, route, {}, {})
        method["assemblies"].append(assembly(route, labels[route], packet))
    recovery_path = "prompts/v2/14-recover-page.md"
    recovery_hash = hashlib.sha256((ROOT / recovery_path).read_bytes()).hexdigest()
    method["assemblies"].append(assembly("recover", "Recover a physical page", {
        "instruction_paths": [recovery_path], "instructions_hash": recovery_hash,
        "component_hashes": {recovery_path: recovery_hash}}))
    for task in tasks:
        packet = compose_v2(ROOT, task["route"], {}, {})
        supplements = [task["supplement"]] if task["id"] == "translate" else ["prompts/operations/00-request-contract.md", task["supplement"]]
        for path in supplements:
            raw = (ROOT/path).read_bytes()
            packet["instructions"] += "\n\n" + raw.decode("utf-8")
            packet["instruction_paths"].append(path)
            packet["component_hashes"][path] = hashlib.sha256(raw).hexdigest()
        for path in (() if task["id"] == "translate" else ("config/operations/tasks.json", "schemas/operations/analysis-request.schema.json")):
            packet["component_hashes"][path] = hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        method["assemblies"].append(assembly('operation:'+task['id'], task['label']+' (Analysis tool)', fingerprint_packet(packet)))
    return method


def assembly(key, label, packet):
    return {"id": key, "label": label, "instruction_paths": packet["instruction_paths"],
            "instructions_hash": packet["instructions_hash"], "component_hashes": packet["component_hashes"]}


if __name__ == "__main__":
    target = ROOT / "integrations/fixtures/methodology.json"
    target.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Built configured methodology and exact source text/hash catalog for configured prompts. No inference.")
