"""Reconstruct the 40-topic vocabulary from the supplied design, with proposed routing notes."""
import json
from pathlib import Path

ROWS = [
 ("CLM-01", "Climate planning and governance", "Climate", "Strategies, plans, laws, institutional coordination and mainstreaming.", "A finance mechanism also needs CLM-02; do not tag all climate text here."),
 ("CLM-02", "Climate finance and support", "Climate", "Funding mechanisms, investment planning, budget integration, insurance and international support.", "A funding source alone does not establish conditionality."),
 ("CLM-03", "Climate information and risk assessment", "Climate", "Observations, scenarios, vulnerability assessments, risk maps and climate services.", "Use CLM-04 for operational warnings and preparedness."),
 ("CLM-04", "Early warning and disaster preparedness", "Climate", "Warnings, emergency planning, evacuation, civil protection and disaster readiness.", "Do not infer operational warning capacity from a risk study."),
 ("CLM-05", "Climate monitoring and reporting", "Climate", "GHG inventories, transparency, adaptation indicators, evaluation and reporting.", "An expected monitoring indicator is not evidence of a result."),
 ("CLM-06", "Economy-wide emissions targets", "Climate", "National emissions ceilings, reduction pledges, net-zero and economy-wide intensity targets.", "Sectoral targets use the relevant sector topic; keep EU-wide scope explicit."),
 ("CLM-07", "Land carbon and removals", "Climate", "Sequestration, land-use emissions/removals, forest carbon and LULUCF accounting.", "Carbon-sink wording alone does not establish biodiversity benefits."),
 ("ENE-01", "Renewable electricity", "Energy", "Solar, wind, hydropower and other renewable electricity, including distributed generation.", "Rooftop PV alone does not imply an Urban label."),
 ("ENE-02", "Grids and energy storage", "Energy", "Transmission, distribution, interconnection, flexibility, storage and network resilience.", "A generating plant without grid measures belongs to ENE-01 or ENE-05."),
 ("ENE-03", "Clean heating and fuels", "Energy", "District heating, heat pumps, renewable heat and lower-emission fuel switching.", "Vehicle fuel measures use TRN-01; building retrofit packages may also use URB-01."),
 ("ENE-04", "Energy efficiency and demand management", "Energy", "Energy audits, performance standards, efficient equipment and demand management.", "Prefer a more specific building, industrial or transport topic when applicable."),
 ("ENE-05", "Fossil energy transition", "Energy", "Coal/oil/gas transition, fossil asset retirement, subsidy reform and supply changes.", "Do not infer transition success from a plan or fuel switch."),
 ("ENE-06", "Oil and gas methane", "Energy", "Fugitive emissions, leaks, venting and flaring across oil/gas supply.", "Landfill methane uses WST-02; agricultural methane uses AGR-03."),
 ("AGR-01", "Irrigation efficiency", "Agriculture|Water", "Agricultural water delivery, irrigation modernization and water-saving technologies.", "Municipal water supply uses WAT-01; solar irrigation may also use ENE-01."),
 ("AGR-02", "Resilient crops and soils", "Agriculture", "Crop varieties, soil health, erosion control, land management and resilient farming.", "Forest management uses BIO-01; record explicit carbon accounting under CLM-07."),
 ("AGR-03", "Livestock and manure", "Agriculture", "Animal health/resilience, feed, manure and agricultural methane/nitrous oxide measures.", "Human health uses HEA topics."),
 ("AGR-04", "Food systems and farm livelihoods", "Agriculture", "Food security, agricultural advice, storage, value chains and farm livelihoods.", "Food-waste disposal can also use WST-01 when a distinct measure is stated."),
 ("WAT-01", "Water supply and groundwater", "Water", "Water availability, abstraction, groundwater, drinking water, storage and network losses.", "Farm irrigation uses AGR-01; sanitation uses WST-03."),
 ("WAT-02", "River basins and drought management", "Water", "Basin management, allocation, drought planning, environmental flows and shared waters.", "Flood defenses use WAT-03; warnings may also use CLM-04."),
 ("WAT-03", "Flood and coastal protection", "Water", "River/coastal flood risk, defenses, erosion and sea-level adaptation.", "General settlement planning may additionally use URB-02."),
 ("WAT-04", "Water quality and reuse", "Water", "Surface-water quality, pollution prevention, safe reuse and receiving-water protection.", "Wastewater treatment systems use WST-03; keep both if both purposes are explicit."),
 ("BIO-01", "Forest health and management", "Biodiversity", "Forest condition, sustainable management, wildfire/pest control and forest resilience.", "Carbon-only forest targets use CLM-07 without an inferred biodiversity claim."),
 ("BIO-02", "Species, habitats and protected areas", "Biodiversity", "Species conservation, habitats, connectivity and terrestrial/aquatic protected areas.", "Active ecosystem restoration uses BIO-03."),
 ("BIO-03", "Ecosystem restoration", "Biodiversity", "Restoration of forests, wetlands, peatlands and ecosystems, including ecosystem adaptation.", "Record carbon or adaptation co-benefits only with evidence."),
 ("HEA-01", "Heat and human health", "Health", "Heat-health plans, cooling access, exposure and vulnerable-group protection.", "Urban greening uses URB-03 when the physical intervention is stated."),
 ("HEA-02", "Climate-sensitive disease and exposure", "Health", "Infectious disease, water/vector-borne illness, air-quality exposure and surveillance.", "Do not assume health outcomes from emissions reductions alone."),
 ("HEA-03", "Resilient health services", "Health", "Health facilities, service delivery, emergency capacity, staffing and essential supplies.", "General civil protection uses CLM-04."),
 ("URB-01", "Building energy performance", "Urban|Energy", "Building insulation, retrofits, performance codes, passive design and energy-saving systems.", "Urban is a taxonomy domain here, not proof of urban geographic scope."),
 ("URB-02", "Resilient settlements and infrastructure", "Urban", "Spatial planning, building safety, urban drainage and local infrastructure resilience.", "Sector-specific transport or energy networks use their specific topics."),
 ("URB-03", "Urban cooling and green spaces", "Urban", "Trees, green/blue spaces, shading and cooling-oriented public-space design.", "General forest restoration uses BIO-03; health links require explicit evidence."),
 ("WST-01", "Materials, recycling and circularity", "Waste", "Prevention, separate collection, recycling, composting, food waste and circular material use.", "Landfill gas uses WST-02; industrial production measures may use IND-01."),
 ("WST-02", "Solid-waste disposal and methane", "Waste", "Landfill management/emissions, gas capture and disposal-facility resilience.", "Oil/gas methane uses ENE-06."),
 ("WST-03", "Wastewater and sanitation", "Waste|Water", "Sewage, wastewater treatment, sanitation, sludge and associated emissions/resilience.", "Receiving-water quality/reuse measures may also use WAT-04."),
 ("TRN-01", "Low-emission vehicles and fuels", "Transport", "Electrification, charging, cleaner transport fuels and vehicle standards.", "Public transport service improvements use TRN-02 where relevant."),
 ("TRN-02", "Public, active and shared mobility", "Transport", "Public transport, rail shift, walking, cycling and reduced private-car dependence.", "Transport hazard resilience uses TRN-03."),
 ("TRN-03", "Resilient transport networks", "Transport", "Protection/adaptation of roads, railways, ports, airports and logistics.", "Emissions measures use TRN-01 or TRN-02."),
 ("IND-01", "Cleaner production and industrial efficiency", "Industry", "Industrial energy/material efficiency, production technology, modernization and factory resilience.", "Process gases/refrigerants use IND-02."),
 ("IND-02", "Process emissions and refrigerants", "Industry", "Industrial process emissions, cement/chemicals, fluorinated gases and refrigerants.", "Generic factory energy efficiency uses IND-01."),
 ("TOU-01", "Tourism adaptation and destination resilience", "Tourism", "Destination risks, changing seasons, diversification and resilient visitor infrastructure.", "Only use Tourism when the sector is explicit."),
 ("TOU-02", "Tourism resource efficiency", "Tourism", "Tourism-specific water, energy, waste and sustainable visitor/accommodation measures.", "Keep sector topics too where the source explicitly describes the intervention."),
]


def main():
    root = Path(__file__).resolve().parents[1]
    data = {"version": "1.0.0", "status": "proposed_not_benchmarked",
            "provenance": "IDs and topic names from supplied design v1.1 pp. 7-9. Definitions condensed; routing rules are proposed engineering guidance. Referenced companion JSON was not supplied.",
            "cross_cutting_tags": ["gender", "youth", "children", "disability", "older_people", "just_transition", "livelihoods", "capacity", "finance", "technology", "data", "transboundary", "hazards"],
            "topics": [{"id": i, "name": n, "domains": d.split("|"), "definition": definition, "routing_rule": route}
                       for i, n, d, definition, route in ROWS]}
    (root / "config/topic-pool.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Wrote {len(ROWS)} topics")


if __name__ == "__main__":
    main()
