"""Build isolated, invented presentation fixtures. Never import or process a country."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))

def build():
    base = read('examples/v2/extraction.json')['records'][0]
    knowledge = read('integrations/fixtures/knowledge.json')
    records, evidence = [], []
    sources = [dict(document_id=f'design-doc-{n}', title=title, pages=12, sha256=str(n)*64, segments=[])
               for n,title in [(1,'Invented adaptation plan · earlier edition'),(2,'Invented policy update · later edition')]]
    def add(title, text, topics, *, kind='commitment', doc=0, labels=None):
        n=len(records)+1; rid=f'design-r-{n}'; eid=f'design-e-{n}'; sid=f'design-s-{n}'
        r=copy.deepcopy(base)
        r.update(local_id=rid,label_en=title,description_en=text,kind=kind,
                 targets=[],actors=[],finance=[],indicators=[],risk_contexts=[],details=[],missing_fields=[],
                 evidence_ids=[eid],quality_flags=['Invented interface fixture; not a government finding.'])
        r['labels']={k:[] for k in r['labels']};r['labels']['topic_ids']=topics
        r['labels'].update(labels or {})
        r['geography']['evidence_ids']=[eid]
        r['field_support']=[dict(field_path='/labels',evidence_ids=[eid],basis='classification',reason='Illustrative classification under the fixture codebook; inspect the invented statement.'),dict(field_path='/description_en',evidence_ids=[eid],basis='explicit',reason='Exact invented English statement.')]
        evidence.append(dict(local_id=eid,segment_id=sid,english_segment_id=sid,quote_original=text,context_evidence_ids=[]))
        sources[doc]['segments'].append(dict(id=sid,page=n,language='en',text=text,english_text=text,translation_method='identity'))
        records.append(r)
        return r,eid
    def target(r,eid,metric,value,period,condition=None,basis='absolute',unit='systems'):
        t=copy.deepcopy(base['targets'][0]);t.update(local_id=f"{r['local_id']}-t-{len(r['targets'])+1}",metric_text=metric,metric_key_candidate=None,unit_key_candidate=None,unit_raw=unit,target_period=period,basis=basis,conditionality='explicitly_conditional' if condition else 'not_stated',condition_text=condition,evidence_ids=[eid],sector_scope=[],gas_scope=[])
        t['value']=dict(raw_token=str(value),decimal=str(value),evidence_id=eid,notation='dot_decimal') if value is not None else None
        r['targets'].append(t);return t
    def actor(r,eid,name,role='lead'):
        r['actors'].append(dict(local_id=f"{r['local_id']}-actor",name_original=name,name_en=name,role=role,target_ids=[],evidence_ids=[eid]))
    r,e=add('Install flood early-warning systems','Install 20 flood early-warning systems by 2030, conditional on international financing. The Water Ministry will lead delivery.',['CLM-04'],labels=dict(objectives=['disaster_risk_reduction'],hazards=['flood'],risk_components=['capacity'],risk_functions=['early_warning_preparedness'],cross_cutting_tags=['finance'],policy_instruments=['information_warning']))
    target(r,e,'Flood early-warning systems',20,'2030','Subject to international financing');actor(r,e,'Water Ministry')
    r['details']=[dict(local_id='support-1',kind='support_need',text_en='International financing is required.',target_ids=[r['targets'][0]['local_id']],evidence_ids=[e])]
    r['missing_fields']=[dict(field_path='/finance',reason='not_stated',detail='No amount is stated in this invented passage.'),dict(field_path='/targets/0/baseline_value',reason='not_stated',detail=None)]
    # One genuinely bilingual passage, with stored English alignment.
    evidence[0]['quote_original']='К 2030 году установить 20 систем раннего предупреждения о наводнениях при условии международного финансирования. Ведущее ведомство — Министерство водных ресурсов.'
    sources[0]['segments'][0].update(text=evidence[0]['quote_original'],language='ru',translation_method='machine_translation')
    r,e=add('Modernize irrigation across two scenarios','Modernize 30 hectares of irrigation by 2030; extend to 50 hectares by 2035 if external finance is secured. The Agriculture Agency is the lead.',['AGR-01'],labels=dict(objectives=['adaptation'],hazards=['drought'],policy_instruments=['infrastructure_service']))
    target(r,e,'Irrigation area modernized',30,'2030',unit='hectares');target(r,e,'Irrigation area modernized',50,'2035','If external finance is secured',unit='hectares');actor(r,e,'Agriculture Agency')
    r,e=add('Prioritize heat protection for older people','Heat protection for older people is an explicit priority; no action or numeric target is specified.',['HEA-01'],kind='priority',labels=dict(hazards=['extreme_heat'],population_groups=['older_people'],objectives=['adaptation']))
    r,e=add('Flood exposure and emergency access','Flood-prone settlements face disrupted road access. Older people have limited evacuation access; local shelters provide emergency capacity.',['CLM-08','TRN-03'],kind='context',labels=dict(hazards=['flood'],risk_components=['exposure','vulnerability','capacity'],population_groups=['older_people']))
    r['risk_contexts']=[dict(local_id='risk-context-4',hazard_text='flood',exposed_assets_or_places=['settlements','roads'],vulnerability_drivers=['Limited evacuation access for older people'],stated_capacities=['Local shelters'],consequence_en='Disrupted road access',likelihood_text=None,severity_text=None,assessment_period=None,scenario=None,target_ids=[],action_link='context_only',link_basis='explicit',evidence_ids=[e])]
    r,e=add('Prepare community cooling plans','Prepare community cooling plans with participation by older people and persons with disabilities. No deadline or lead institution is stated.',['HEA-01','URB-02'],labels=dict(objectives=['adaptation'],hazards=['extreme_heat'],population_groups=['older_people','persons_with_disabilities'],cross_cutting_tags=['participation','disability'],policy_instruments=['strategy_plan']))
    r['missing_fields']=[dict(field_path='/actors',reason='not_stated',detail='Lead institution is not stated.'),dict(field_path='/targets',reason='not_stated',detail='No deadline or structured target is stated.')]
    r,e=add('Reported warning-system operation in 2024','The invented update reports that five warning systems operated in 2024. This statement does not assess progress against the 2030 target.',['CLM-04'],kind='implementation_observation',doc=1,labels=dict(hazards=['flood'],risk_functions=['early_warning_preparedness']));r['reference_period']='2024'
    r,e=add('Reduce emissions against a BAU scenario','Reduce emissions by 25 percent against a business-as-usual scenario by 2030.',['CLM-06'],labels=dict(objectives=['mitigation']))
    target(r,e,'Emissions reduction',25,'2030',basis='BAU_reduction',unit='percent');r['targets'][0]['scenario']='Business as usual'
    r,e=add('Reduce emissions against a historical baseline','Reduce emissions by 40 percent against the 1990 historical baseline by 2030, subject to international support.',['CLM-06'],doc=1,labels=dict(objectives=['mitigation'],cross_cutting_tags=['finance']))
    t=target(r,e,'Emissions reduction',40,'2030','Subject to international support',basis='historical_reduction',unit='percent');t['baseline_period']='1990'
    r,e=add('Support wastewater resilience','Improve wastewater and sanitation systems. Partners are a financing source; no delivery condition is stated.',['WST-03'],labels=dict(objectives=['adaptation'],cross_cutting_tags=['finance']))
    r['finance']=[dict(local_id='finance-source-9',kind='financing_source',amount=None,currency=None,price_period=None,implementation_period=None,description_en='Partners are named as a financing source; no amount is specified.',target_ids=[],evidence_ids=[e])]
    r,e=add('Establish community repair circles','Establish community repair circles to maintain emergency equipment. The local term repair circles has no agreed topic mapping in this example.',[],labels=dict(objectives=['disaster_risk_reduction'],risk_functions=['early_warning_preparedness']))
    r['labels']['unmapped_terms']=[dict(term='repair circles',proposed_definition='Community arrangements for equipment maintenance',facet='topic',evidence_ids=[e])]
    r,e=add('Conflicting warning-system deadline','The later invented edition states 20 flood warning systems by 2032; continuity with the earlier 2030 statement is unresolved.',['CLM-04'],doc=1,labels=dict(hazards=['flood'],risk_functions=['early_warning_preparedness']))
    target(r,e,'Flood warning systems',20,'2032');r['quality_flags'].append('The earlier statement says 2030; both values remain visible. Continuity is unresolved, not a missing value.')
    r,e=add('Coordinate resilient public services','Coordinate health, water, electricity and transport services for heat emergencies. Agencies will share risk information, prepare backup arrangements and consult affected communities. Financing responsibilities remain ambiguous; the schedule is in an unprocessed annex, and a scanned finance table is unreadable.',['HEA-03','ENE-02','TRN-03'],labels=dict(objectives=['adaptation','disaster_risk_reduction'],hazards=['extreme_heat','compound_hazard'],risk_components=['systemic_cascading_risk'],risk_functions=['early_warning_preparedness','coping_continuity'],cross_cutting_tags=['capacity','data','participation']))
    r['missing_fields']=[dict(field_path='/actors',reason='ambiguous',detail='Agencies are named collectively.'),dict(field_path='/indicators',reason='not_applicable',detail='This passage specifies coordination only.')]
    r['quality_flags'].extend(['Schedule annex not processed; no source-absence inference.', 'Scanned finance table unreadable; no funding-absence inference.'])
    def f(text,ids,kind='source_fact'):
        return dict(text_en=text,kind=kind,citations=dict(record_ids=ids,evidence_ids=[records[int(x.split('-')[-1])-1]['evidence_ids'][0] for x in ids]),calculation=None,limitations=['Invented demonstration; no country assessment.'])
    headline=[f('Flood warning systems have a financing condition and unresolved deadlines across the two invented editions.',['design-r-1','design-r-11'],'derived'),f('Heat protection is a source-stated priority; the cooling action lacks a stated lead and timeframe.',['design-r-3','design-r-5']),f('The two emissions percentages use different bases and cannot support a numerical ambition comparison.',['design-r-7','design-r-8'],'derived')]
    section_ids=read('config/methodology.json')['views'][0]['schema_sections']
    sections=[dict(section_id=s,state='not_found_in_scope',findings=[],gap_note='No additional finding is supplied for this synthetic section.') for s in section_ids]
    mapping={'risk_context_and_drr':0,'adaptation_and_resilience':1,'mitigation':2,'changes_and_coherence':0,'finance_and_support':0,'inclusion_and_development':1}
    for s in sections:
        if s['section_id'] in mapping:s.update(state='found',findings=[headline[mapping[s['section_id']]]],gap_note=None)
        if s['section_id']=='monitoring':s.update(state='not_processed',gap_note='An illustrative annex is unprocessed. This does not establish absent monitoring.')
        if s['section_id']=='scope_and_method':s.update(state='found',findings=[f('This interface collection contains invented source passages and classifications; it is not a national assessment.',['design-r-1'],'derived')],gap_note=None)
        if s['section_id']=='implementation_and_actors':s.update(state='found',findings=[f('The Water Ministry is named as lead for the conditional warning-system action.',['design-r-1'])],gap_note=None)
        if s['section_id']=='limitations':s.update(state='found',findings=[f('The coordination passage identifies an unprocessed schedule annex and unreadable finance table.',['design-r-12'])],gap_note=None)
    p=dict(id='design-example-v2',country_code='KAZ',synthetic=True,presentation_fixture=True,created_at='2026-10-09T09:00:00Z',provenance_note='Invented presentation fixture. Not imported, generated, checked or selected as a Country Profile.',sources=sources,validation={},archive={},
           validation_codebook={k:knowledge.get(k) for k in ['taxonomy_version','vocabulary_version','domains','topics','dimensions']},
           extraction=dict(records=records,evidence=evidence,coverage=[dict(segment_id=e['segment_id'],disposition='extracted',record_ids=[records[i]['local_id']],reason='Synthetic passage') for i,e in enumerate(evidence)],notes=['Invented interface examples; not a processed country.'],issues=[]),
           report=dict(country_codes=['KAZ'],source_group_ids=['design-only'],availability='partial',headline_findings=headline,sections=sections,prioritized_commitments=[dict(commitment_id='design-r-1',reason='Analytical highlight: explicit financing condition and unresolved timing; not a national priority ranking.',evidence_ids=['design-e-1','design-e-11'])],followup_questions=[f('Which financing and deadline apply to the warning-system action?',['design-r-1','design-r-11'],'analyst_suggestion')],limitations=['All passages and classifications are invented for interface verification.','The collection includes an unprocessed annex and an unreadable table example.','No implementation progress or unique-commitment totals are established.']),
           reconciliation=dict(relations=[dict(kind='unresolved',source_record_ids=['design-r-1'],target_record_ids=['design-r-11'],evidence_ids=['design-e-1','design-e-11'],reason='Different stated deadlines; no established supersession.')],issues=['Preserve both source variants.']))
    p['validation_codebook']['guide_version']=knowledge['version']
    return p

if __name__=='__main__':
    target=ROOT/'integrations/fixtures/report-experience.json'
    target.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Built 12 isolated synthetic source records. No country data or model calls.')
