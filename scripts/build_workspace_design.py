"""Project supplied inventory into the regional UI; never infer completed analysis."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(path, data):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    inventory = read("data/manifests/corpus.json")
    features = [{k: v[k] for k in ("id", "label", "short", "description")}
                for v in read("config/methodology.json")["views"]]
    countries = []
    documents = []
    for d in inventory["documents"]:
        documents.append({"id":d["document_id"],"country_code":d["country_code"],"title":d["title"],
                          "declared_type":d["declared_type"],"pages":d["pages"],"submission_date":d.get("submission_date"),
                          "metadata_status":d["metadata_status"],"flagged_pages":len(d.get("flagged_pages",[])),
                          "english_status":"not_prepared"})
    for c in inventory["countries"]:
        countries.append({"code":c["country_code"],"name":c["name"],"document_count":c["documents"],"pages":c["pages"],
                          "prime_release_id":None,"prime_mode":"latest_successful","history_count":0,
                          "features":{f["id"]:("not_generated" if c["documents"] else "no_sources") for f in features}})
    region={"schema_version":"1.0.0","inventory_date":inventory["inventory_date"],
            "status_basis":"Supplied local inventory; no production release registry is connected. No completed Prime reports have been produced.",
            "country_code_note":inventory["country_code_note"],"features":features,"countries":countries,"documents":documents}
    write("integrations/fixtures/regional-workspace.json",region)
    vocab=read("config/v2/vocabulary.json")
    taxonomy=read("config/v2/taxonomy.json")
    tasks=read("config/operations/tasks.json")
    meanings={d["id"]:d["options"] for d in read("config/v2/label-guide.json")["dimensions"]}
    tasks["facets"]={"domains":taxonomy["domains"],"topics":taxonomy["topics"],
                     "hazards":meanings["hazards"],"risk_functions":meanings["risk_functions"]}
    write("integrations/fixtures/operation-tasks.json",tasks)
    string={"type":"string"}
    def array(items): return {"type":"array","items":items,"uniqueItems":True}
    def obj(**fields): return {"type":"object","properties":fields,"required":list(fields),"additionalProperties":False}
    schema=obj(schema_version={"const":"2.0.0"},kind={"const":"ad_hoc"},task={"enum":[t["id"] for t in tasks["tasks"]]},
               source_groups=array(obj(id=string,label={"type":"string","minLength":1},document_ids=array(string))),
               filters=obj(topic_ids=array({"enum":[t["id"] for t in taxonomy["topics"]]}),domain_ids=array({"enum":[d["id"] for d in taxonomy["domains"]]}),hazards=array({"enum":vocab["hazards"]}),risk_functions=array({"enum":vocab["risk_functions"]})),
               requested_fields=array({"enum":sorted({o["id"] for t in tasks["tasks"] for o in t["options"]})}),
               comparison_mode={"enum":[None,*[m["id"] for m in tasks["comparison_modes"]]]},
               include_analyst_proposals={"type":"boolean"},question=string,instructions=string,
               model=obj(route={"enum":["codex_chatgpt","openai_api"]},model=string,effort={"enum":["default","none","minimal","low","medium","high","xhigh","max","ultra"]},fallback_allowed={"const":"never"}),
               output=obj(artifact={"enum":[t["artifact"] for t in tasks["tasks"]]},language={"type":"string","minLength":1,"maxLength":80},include_original_evidence={"const":True},coverage_mode={"const":"all_selected_documents"}),
               uploads=array(obj(filename=string,state={"const":"local_pending"})),execution_state={"const":"not_run"})
    schema.update({"$schema":"https://json-schema.org/draft/2020-12/schema","title":"Operational analysis request 2.0.0"})
    schema["properties"]["source_groups"]["minItems"]=1
    schema["properties"]["source_groups"]["items"]["properties"]["document_ids"]["minItems"]=1
    schema["allOf"]=[{"if":{"properties":{"task":{"const":"translate"}}},"then":{"properties":{"requested_fields":{"maxItems":0}}},"else":{"properties":{"requested_fields":{"minItems":1}}}}]
    write("schemas/operations/analysis-request.schema.json",schema)
    print(f"Prepared regional metadata for {len(countries)} countries / {len(documents)} documents; zero completed reports. Task definitions loaded from editable JSON.")


if __name__ == "__main__":
    main()
