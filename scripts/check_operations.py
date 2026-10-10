"""Validate operational schemas, inventory projection and offline prompt effects."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from policytracker.operations import compose_operation

ROOT=Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))

def main():
    region=read("integrations/fixtures/regional-workspace.json")
    inventory=read("data/manifests/corpus.json")
    assert region["inventory_date"]==inventory["inventory_date"], "Rebuild the regional inventory projection"
    assert len(region["countries"])==len(inventory["countries"])
    assert sum(c["document_count"] for c in region["countries"])==len(region["documents"])==len(inventory["documents"])
    assert len({d["id"] for d in region["documents"]})==len(inventory["documents"])
    expected={d["document_id"]:d for d in inventory["documents"]}
    assert {d["id"] for d in region["documents"]}==set(expected), "Rebuild the regional inventory projection"
    for doc in region["documents"]:
        assert all(doc[key]==expected[doc["id"]][key] for key in ("country_code", "title", "declared_type", "pages", "submission_date", "metadata_status")), "Stale document metadata: rebuild the regional inventory projection"
    countries={c["country_code"]:c for c in inventory["countries"]}
    assert {c["code"] for c in region["countries"]}==set(countries)
    for country in region["countries"]:
        assert country["document_count"]==countries[country["code"]]["documents"]
        assert country["pages"]==countries[country["code"]]["pages"]
    assert all(c["prime_release_id"] is None for c in region["countries"])
    assert all(set(c["features"])=={"brief", "commitments"} for c in region["countries"])
    assert all(s==("not_generated" if c["document_count"] else "no_sources") for c in region["countries"] for s in c["features"].values())
    product=read("config/product.json")
    assert product["primary_layer"]["published_versions_per_country"]==1
    assert product["secondary_layer"]["required_for_mvp_acceptance"] is False
    plan=read("data/manifests/initial-batch-plan.json")
    assert plan["status"]=="planned_not_executed"
    for job in plan["countries"]:
        assert job["human_review_required"] is False
        assert "expert_acceptance" not in job["required_stages"]
        if job["document_ids"]:
            assert job["required_stages"][-1]=="automatic_publication_respecting_pin"
    catalog=read("config/operations/tasks.json")
    schema=read("schemas/operations/analysis-request.schema.json")
    Draft202012Validator.check_schema(schema)
    api=read("integrations/api/openapi.json")
    Draft202012Validator(api["components"]["schemas"]["RegionalWorkspace"]).validate(region)
    kaz=[d["id"] for d in region["documents"] if d["country_code"]=="KAZ"]
    examples=[]
    for task in catalog["tasks"]:
        r={"schema_version":"2.0.0","kind":"ad_hoc","task":task["id"],
           "source_groups":[{"id":"selected","label":"Selected documents","document_ids":kaz}],
           "filters":{"domain_ids":[],"topic_ids":[],"hazards":[] if task["id"]=="translate" else ["flood"],"risk_functions":[]},
           "requested_fields":[o["id"] for o in task["options"] if o["default"]],
           "comparison_mode":None,"include_analyst_proposals":False,"question":"Which commitments require external finance?" if task["id"]=="brief" else "", "instructions":"Preserve national and local actor roles.",
           "model":{"route":"codex_chatgpt","model":"gpt-6-astra","effort":"xhigh","fallback_allowed":"never"},
           "output":{"artifact":task["artifact"],"language":"en","include_original_evidence":True,"coverage_mode":"all_selected_documents"},
           "uploads":[],"execution_state":"not_run"}
        if task["id"]=="compare":
            r["comparison_mode"]="revision"
            r["source_groups"]=[{"id":"earlier","label":"Earlier edition","document_ids":[kaz[0]]},{"id":"later","label":"Later edition","document_ids":[kaz[1]]}]
        p=compose_operation(ROOT,r,{"fixture":True})
        assert p["route"]==task["route"] and p["execution_state"]=="not_run"
        context=json.loads(p["input"])["task_context"]
        assert len(context["selected_options"])==len(r["requested_fields"])
        assert context["operation_request"]["instructions"]==r["instructions"]
        changed=copy.deepcopy(r);changed["model"]["effort"]="high"
        assert compose_operation(ROOT,changed,{"fixture":True})["request_hash"]!=p["request_hash"]
        pending=copy.deepcopy(r);pending["uploads"]=[{"filename":"support.pdf","state":"local_pending"}]
        try: compose_operation(ROOT,pending,{})
        except ValueError as e: assert "pending uploads" in str(e)
        else: raise AssertionError("Pending upload was compiled as known evidence")
        examples.append(r)
    target=ROOT/"examples/operations/requests.json";target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(examples,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Verified {len(countries)}-country/{len(expected)}-document projection, two empty view states, five operational requests/prompt routes, changed model hashes and pending-upload rejection. No inference.")

if __name__=="__main__":main()
