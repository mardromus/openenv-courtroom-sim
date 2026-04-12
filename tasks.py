"""
DisasterOps-Env: Task Scenarios.

5 disaster scenarios ranging from Easy (simple flood) to Nightmare (multi-hazard megadisaster).
Each task defines zones, resources, roads, shelters, cascading events, and initial conditions.
"""

from typing import List
from schemas import (
    ZoneStatus, ResourceUnit, ShelterInfo, CascadingEvent, SitRep,
    ZoneState, ZoneType, ResourceType, RoadCondition
)
from disaster_sim import DisasterWorld


def build_flood_easy() -> DisasterWorld:
    """
    Task 1: RIVER FLOOD (Easy)
    - 5 zones, 3 affected
    - Plenty of resources
    - All roads open
    - No cascading events
    - 8 max steps
    """
    world = DisasterWorld()
    world.incident_name = "River Flood — Central District"
    world.max_steps = 8
    world.weather = "overcast"
    world.operational_budget = 1000000.0  # Infinite essentially

    world.zones = {
        "zone-res-north": ZoneStatus(
            zone_id="zone-res-north", zone_type=ZoneType.RESIDENTIAL,
            name="North Residential", population=300,
            status=ZoneState.CRITICAL, casualties=5, trapped_people=25,
            damage_level=0.6, accessibility="accessible"
        ),
        "zone-res-south": ZoneStatus(
            zone_id="zone-res-south", zone_type=ZoneType.RESIDENTIAL,
            name="South Residential", population=200,
            status=ZoneState.AFFECTED, casualties=2, trapped_people=10,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-commercial": ZoneStatus(
            zone_id="zone-commercial", zone_type=ZoneType.COMMERCIAL,
            name="Commercial District", population=150,
            status=ZoneState.AFFECTED, casualties=0, trapped_people=5,
            damage_level=0.2, accessibility="accessible"
        ),
        "zone-hospital": ZoneStatus(
            zone_id="zone-hospital", zone_type=ZoneType.HOSPITAL,
            name="Central Hospital", population=100,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
        "zone-shelter-park": ZoneStatus(
            zone_id="zone-shelter-park", zone_type=ZoneType.SHELTER,
            name="City Park Shelter Area", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
    }
    world.total_initial_population = sum(z.population for z in world.zones.values())

    world.resources = [
        ResourceUnit(unit_id="med_1", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="med_2", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="med_3", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="rescue_1", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="rescue_2", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="heli_1", resource_type=ResourceType.HELICOPTER),
        ResourceUnit(unit_id="truck_1", resource_type=ResourceType.SUPPLY_TRUCK),
        ResourceUnit(unit_id="truck_2", resource_type=ResourceType.SUPPLY_TRUCK),
    ]

    world.roads = {
        "road_to_zone-res-north": RoadCondition.OPEN,
        "road_to_zone-res-south": RoadCondition.OPEN,
        "road_to_zone-commercial": RoadCondition.OPEN,
        "road_to_zone-hospital": RoadCondition.OPEN,
        "road_to_zone-shelter-park": RoadCondition.OPEN,
    }

    world.shelters = {
        "shelter-park": ShelterInfo(
            shelter_id="shelter-park", zone_id="zone-shelter-park",
            capacity=300, is_open=False
        )
    }

    world.sitreps = [
        SitRep(
            timestamp_hours=0.0, zone_id="zone-res-north",
            report="INITIAL ALERT: Severe flooding in North Residential. "
                   "25 people trapped, 5 confirmed casualties. Immediate response needed.",
            severity="critical", casualties_reported=5, trapped_reported=25
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-res-south",
            report="Flooding reaching South Residential. 10 people trapped on rooftops. "
                   "2 casualties reported.",
            severity="high", casualties_reported=2, trapped_reported=10
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-commercial",
            report="Minor flooding in Commercial District. 5 people trapped in basement. "
                   "No casualties yet.",
            severity="moderate", casualties_reported=0, trapped_reported=5
        ),
    ]

    return world


def build_earthquake_medium() -> DisasterWorld:
    """
    Task 2: EARTHQUAKE (Medium)
    - 8 zones, 6 affected, including a hospital
    - 2 roads blocked
    - Moderate resources
    - Aftershock at step 5 damages 2 more zones
    - 10 max steps
    """
    world = DisasterWorld()
    world.incident_name = "6.5 Earthquake — Metro Region"
    world.max_steps = 10
    world.weather = "clear"
    world.operational_budget = 500000.0

    world.zones = {
        "zone-res-west": ZoneStatus(
            zone_id="zone-res-west", zone_type=ZoneType.RESIDENTIAL,
            name="West Residential", population=400,
            status=ZoneState.CRITICAL, casualties=12, trapped_people=45,
            damage_level=0.7, accessibility="accessible"
        ),
        "zone-res-east": ZoneStatus(
            zone_id="zone-res-east", zone_type=ZoneType.RESIDENTIAL,
            name="East Residential", population=350,
            status=ZoneState.AFFECTED, casualties=3, trapped_people=15,
            damage_level=0.4, accessibility="accessible"
        ),
        "zone-school": ZoneStatus(
            zone_id="zone-school", zone_type=ZoneType.SCHOOL,
            name="Central School", population=200,
            status=ZoneState.CRITICAL, casualties=8, trapped_people=35,
            damage_level=0.8, accessibility="limited"
        ),
        "zone-hospital-main": ZoneStatus(
            zone_id="zone-hospital-main", zone_type=ZoneType.HOSPITAL,
            name="Main Hospital", population=150,
            status=ZoneState.AFFECTED, casualties=2, trapped_people=10,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-industrial": ZoneStatus(
            zone_id="zone-industrial", zone_type=ZoneType.INDUSTRIAL,
            name="Industrial Zone", population=100,
            status=ZoneState.AFFECTED, casualties=1, trapped_people=8,
            damage_level=0.5, accessibility="blocked"
        ),
        "zone-commercial-center": ZoneStatus(
            zone_id="zone-commercial-center", zone_type=ZoneType.COMMERCIAL,
            name="City Center", population=250,
            status=ZoneState.AFFECTED, casualties=4, trapped_people=20,
            damage_level=0.4, accessibility="accessible"
        ),
        "zone-res-north-hill": ZoneStatus(
            zone_id="zone-res-north-hill", zone_type=ZoneType.RESIDENTIAL,
            name="North Hill Residential", population=180,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
        "zone-shelter-stadium": ZoneStatus(
            zone_id="zone-shelter-stadium", zone_type=ZoneType.SHELTER,
            name="City Stadium Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
    }
    world.total_initial_population = sum(z.population for z in world.zones.values())

    world.resources = [
        ResourceUnit(unit_id="med_1", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="med_2", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="rescue_1", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="rescue_2", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="rescue_3", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="heli_1", resource_type=ResourceType.HELICOPTER),
        ResourceUnit(unit_id="truck_1", resource_type=ResourceType.SUPPLY_TRUCK),
        ResourceUnit(unit_id="truck_2", resource_type=ResourceType.SUPPLY_TRUCK),
    ]

    world.roads = {
        "road_to_zone-res-west": RoadCondition.OPEN,
        "road_to_zone-res-east": RoadCondition.OPEN,
        "road_to_zone-school": RoadCondition.CONGESTED,
        "road_to_zone-hospital-main": RoadCondition.OPEN,
        "road_to_zone-industrial": RoadCondition.BLOCKED,
        "road_to_zone-commercial-center": RoadCondition.OPEN,
        "road_to_zone-res-north-hill": RoadCondition.OPEN,
        "road_to_zone-shelter-stadium": RoadCondition.OPEN,
    }

    world.shelters = {
        "shelter-stadium": ShelterInfo(
            shelter_id="shelter-stadium", zone_id="zone-shelter-stadium",
            capacity=500, is_open=False
        )
    }

    # Aftershock at step 5
    world.cascading_events = [
        CascadingEvent(
            event_id="aftershock-1",
            description="5.2 magnitude aftershock hits North Hill and East Residential areas",
            trigger_step=5,
            warning_text="Seismologists warn of significant aftershock likely in the North Hill area. "
                         "Consider preemptive evacuation.",
            warning_steps_before=2,
            affected_zones=["zone-res-north-hill", "zone-res-east"],
            road_closures=["road_to_zone-school"],
            preventable=True,
            prevention_action="evacuate_zone"
        )
    ]

    world.sitreps = [
        SitRep(
            timestamp_hours=0.0, zone_id="zone-res-west",
            report="CRITICAL: Major structural collapse in West Residential. "
                   "45 trapped under rubble, 12 confirmed dead. Multiple buildings down.",
            severity="critical", casualties_reported=12, trapped_reported=45
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-school",
            report="CRITICAL: Central School partially collapsed during class hours. "
                   "35 children and staff trapped. 8 casualties confirmed.",
            severity="critical", casualties_reported=8, trapped_reported=35
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-industrial",
            report="Industrial Zone: Road blocked by debris. 8 workers trapped. "
                   "Access only by helicopter.",
            severity="high", casualties_reported=1, trapped_reported=8
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-hospital-main",
            report="Main Hospital partially damaged. 10 patients needing relocation. "
                   "ER still operational but at limited capacity.",
            severity="high", casualties_reported=2, trapped_reported=10
        ),
    ]

    return world


def build_hurricane_hard() -> DisasterWorld:
    """
    Task 3: CATEGORY 4 HURRICANE (Hard)
    - 12 zones, 10 affected
    - Helicopters grounded for steps 1-3
    - Dam at risk of failure (cascading event at step 6)
    - Must evacuate dam-adjacent zones preemptively
    - Scarce resources
    - 12 max steps
    """
    world = DisasterWorld()
    world.incident_name = "Category 4 Hurricane Aria"
    world.max_steps = 12
    world.weather = "severe_storm"
    world.helicopters_grounded = True
    world.operational_budget = 300000.0

    world.zones = {
        "zone-coastal-south": ZoneStatus(
            zone_id="zone-coastal-south", zone_type=ZoneType.RESIDENTIAL,
            name="South Coastal", population=500,
            status=ZoneState.CRITICAL, casualties=15, trapped_people=60,
            damage_level=0.9, accessibility="limited"
        ),
        "zone-coastal-east": ZoneStatus(
            zone_id="zone-coastal-east", zone_type=ZoneType.RESIDENTIAL,
            name="East Coastal", population=300,
            status=ZoneState.CRITICAL, casualties=8, trapped_people=30,
            damage_level=0.7, accessibility="accessible"
        ),
        "zone-downtown": ZoneStatus(
            zone_id="zone-downtown", zone_type=ZoneType.COMMERCIAL,
            name="Downtown", population=400,
            status=ZoneState.AFFECTED, casualties=3, trapped_people=20,
            damage_level=0.4, accessibility="accessible"
        ),
        "zone-res-central": ZoneStatus(
            zone_id="zone-res-central", zone_type=ZoneType.RESIDENTIAL,
            name="Central Residential", population=350,
            status=ZoneState.AFFECTED, casualties=2, trapped_people=15,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-hospital-coastal": ZoneStatus(
            zone_id="zone-hospital-coastal", zone_type=ZoneType.HOSPITAL,
            name="Coastal Hospital", population=120,
            status=ZoneState.CRITICAL, casualties=5, trapped_people=20,
            damage_level=0.6, accessibility="limited"
        ),
        "zone-school-west": ZoneStatus(
            zone_id="zone-school-west", zone_type=ZoneType.SCHOOL,
            name="West Side School", population=180,
            status=ZoneState.AFFECTED, casualties=1, trapped_people=12,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-dam-valley": ZoneStatus(
            zone_id="zone-dam-valley", zone_type=ZoneType.DAM,
            name="Valley Dam", population=20,
            status=ZoneState.AFFECTED, casualties=0, trapped_people=0,
            damage_level=0.5, accessibility="limited",
            needs_evacuation=True
        ),
        "zone-downstream-village": ZoneStatus(
            zone_id="zone-downstream-village", zone_type=ZoneType.RESIDENTIAL,
            name="Downstream Village", population=250,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible",
            needs_evacuation=True
        ),
        "zone-industrial-port": ZoneStatus(
            zone_id="zone-industrial-port", zone_type=ZoneType.INDUSTRIAL,
            name="Port Industrial", population=80,
            status=ZoneState.AFFECTED, casualties=1, trapped_people=5,
            damage_level=0.5, accessibility="blocked"
        ),
        "zone-res-highland": ZoneStatus(
            zone_id="zone-res-highland", zone_type=ZoneType.RESIDENTIAL,
            name="Highland Residential", population=200,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
        "zone-shelter-convention": ZoneStatus(
            zone_id="zone-shelter-convention", zone_type=ZoneType.SHELTER,
            name="Convention Center Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
        "zone-shelter-church": ZoneStatus(
            zone_id="zone-shelter-church", zone_type=ZoneType.SHELTER,
            name="Community Church Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
    }
    world.total_initial_population = sum(z.population for z in world.zones.values())

    world.resources = [
        ResourceUnit(unit_id="med_1", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="med_2", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="rescue_1", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="rescue_2", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="heli_1", resource_type=ResourceType.HELICOPTER, status="grounded"),
        ResourceUnit(unit_id="heli_2", resource_type=ResourceType.HELICOPTER, status="grounded"),
        ResourceUnit(unit_id="truck_1", resource_type=ResourceType.SUPPLY_TRUCK),
    ]

    world.roads = {
        "road_to_zone-coastal-south": RoadCondition.FLOODED,
        "road_to_zone-coastal-east": RoadCondition.CONGESTED,
        "road_to_zone-downtown": RoadCondition.OPEN,
        "road_to_zone-res-central": RoadCondition.OPEN,
        "road_to_zone-hospital-coastal": RoadCondition.CONGESTED,
        "road_to_zone-school-west": RoadCondition.OPEN,
        "road_to_zone-dam-valley": RoadCondition.CONGESTED,
        "road_to_zone-downstream-village": RoadCondition.OPEN,
        "road_to_zone-industrial-port": RoadCondition.BLOCKED,
        "road_to_zone-res-highland": RoadCondition.OPEN,
        "road_to_zone-shelter-convention": RoadCondition.OPEN,
        "road_to_zone-shelter-church": RoadCondition.OPEN,
    }

    world.shelters = {
        "shelter-convention": ShelterInfo(
            shelter_id="shelter-convention", zone_id="zone-shelter-convention",
            capacity=400, is_open=False
        ),
        "shelter-church": ShelterInfo(
            shelter_id="shelter-church", zone_id="zone-shelter-church",
            capacity=150, is_open=False
        ),
    }

    # Dam breach at step 6, warning at step 4
    world.cascading_events = [
        CascadingEvent(
            event_id="dam-breach",
            description="Valley Dam breach! Massive flooding in Downstream Village!",
            trigger_step=6,
            warning_text="Engineers report Valley Dam integrity at 40%. "
                         "URGENT: Evacuate Downstream Village immediately!",
            warning_steps_before=2,
            affected_zones=["zone-downstream-village"],
            road_closures=["road_to_zone-downstream-village"],
            preventable=True,
            prevention_action="evacuate_zone"
        ),
        # Weather clears at step 4 (helicopters available)
        CascadingEvent(
            event_id="weather-clear",
            description="Storm passing. Helicopter operations resuming.",
            trigger_step=4,
            warning_text="Meteorology: Storm eye passing over. Expect brief operational window for helicopters.",
            warning_steps_before=1,
            affected_zones=[],
            road_closures=[]
        ),
    ]

    world.sitreps = [
        SitRep(
            timestamp_hours=0.0, zone_id="zone-coastal-south",
            report="CRITICAL: South Coastal devastated by storm surge. 60 trapped, 15 dead. "
                   "Road flooded — ground access impossible. Only air rescue possible when weather clears.",
            severity="critical", casualties_reported=15, trapped_reported=60
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-coastal-east",
            report="CRITICAL: East Coastal heavily damaged. 30 trapped. "
                   "Road congested but passable.",
            severity="critical", casualties_reported=8, trapped_reported=30
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-hospital-coastal",
            report="Coastal Hospital damaged, 20 patients need evacuation. "
                   "5 casualties among bedridden patients.",
            severity="critical", casualties_reported=5, trapped_reported=20
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-dam-valley",
            report="⚠️ Valley Dam showing stress fractures. Engineers monitoring. "
                   "250 people in Downstream Village may need preemptive evacuation.",
            severity="high", casualties_reported=0, trapped_reported=0
        ),
    ]

    # Override weather clearing logic
    def custom_weather_update(w=world):
        if w.current_step >= 4:
            w.weather = "overcast"
            w.helicopters_grounded = False
            for r in w.resources:
                if r.resource_type == ResourceType.HELICOPTER and r.status == "grounded":
                    r.status = "available"
    world._custom_weather_hook = custom_weather_update

    return world


def build_cascading_expert() -> DisasterWorld:
    """
    Task 4: EARTHQUAKE + CHEMICAL SPILL + DAM BREACH (Expert)
    - 12 zones
    - Multi-hazard: earthquake + industrial chemical spill + dam risk
    - Some field reports INACCURATE (fog of war)
    - Very scarce resources
    - 14 max steps
    """
    world = DisasterWorld()
    world.incident_name = "Multi-Hazard Crisis — Earthquake + Industrial Disaster"
    world.max_steps = 14
    world.weather = "clear"
    world.wind_direction = "east"
    world.operational_budget = 150000.0

    world.zones = {
        "zone-res-alpha": ZoneStatus(
            zone_id="zone-res-alpha", zone_type=ZoneType.RESIDENTIAL,
            name="Alpha District", population=450,
            status=ZoneState.CRITICAL, casualties=18, trapped_people=50,
            damage_level=0.8, accessibility="accessible"
        ),
        "zone-res-beta": ZoneStatus(
            zone_id="zone-res-beta", zone_type=ZoneType.RESIDENTIAL,
            name="Beta District", population=300,
            status=ZoneState.AFFECTED, casualties=5, trapped_people=20,
            damage_level=0.4, accessibility="accessible"
        ),
        "zone-res-gamma": ZoneStatus(
            zone_id="zone-res-gamma", zone_type=ZoneType.RESIDENTIAL,
            name="Gamma District", population=200,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.1, accessibility="accessible"
        ),
        "zone-chem-plant": ZoneStatus(
            zone_id="zone-chem-plant", zone_type=ZoneType.INDUSTRIAL,
            name="Meridian Chemical Plant", population=60,
            status=ZoneState.CRITICAL, casualties=3, trapped_people=12,
            damage_level=0.9, accessibility="limited",
            needs_evacuation=True
        ),
        "zone-chem-adjacent": ZoneStatus(
            zone_id="zone-chem-adjacent", zone_type=ZoneType.RESIDENTIAL,
            name="Plant-Adjacent Homes", population=180,
            status=ZoneState.AFFECTED, casualties=0, trapped_people=5,
            damage_level=0.2, accessibility="accessible",
            needs_evacuation=True
        ),
        "zone-hospital-central": ZoneStatus(
            zone_id="zone-hospital-central", zone_type=ZoneType.HOSPITAL,
            name="Central General Hospital", population=200,
            status=ZoneState.AFFECTED, casualties=3, trapped_people=8,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-school-main": ZoneStatus(
            zone_id="zone-school-main", zone_type=ZoneType.SCHOOL,
            name="Main District School", population=250,
            status=ZoneState.CRITICAL, casualties=6, trapped_people=30,
            damage_level=0.6, accessibility="congested"
        ),
        "zone-dam-north": ZoneStatus(
            zone_id="zone-dam-north", zone_type=ZoneType.DAM,
            name="North Reservoir Dam", population=10,
            status=ZoneState.AFFECTED, casualties=0, trapped_people=0,
            damage_level=0.4, accessibility="limited",
            needs_evacuation=True
        ),
        "zone-dam-downstream": ZoneStatus(
            zone_id="zone-dam-downstream", zone_type=ZoneType.RESIDENTIAL,
            name="River Valley Town", population=320,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible",
            needs_evacuation=True
        ),
        "zone-commercial-hub": ZoneStatus(
            zone_id="zone-commercial-hub", zone_type=ZoneType.COMMERCIAL,
            name="Metro Commercial Hub", population=300,
            status=ZoneState.AFFECTED, casualties=2, trapped_people=10,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-shelter-arena": ZoneStatus(
            zone_id="zone-shelter-arena", zone_type=ZoneType.SHELTER,
            name="Sports Arena Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
        "zone-shelter-community": ZoneStatus(
            zone_id="zone-shelter-community", zone_type=ZoneType.SHELTER,
            name="Community Center Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
    }
    world.total_initial_population = sum(z.population for z in world.zones.values())

    world.resources = [
        ResourceUnit(unit_id="med_1", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="med_2", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="rescue_1", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="rescue_2", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="heli_1", resource_type=ResourceType.HELICOPTER),
        ResourceUnit(unit_id="truck_1", resource_type=ResourceType.SUPPLY_TRUCK),
    ]

    world.roads = {
        "road_to_zone-res-alpha": RoadCondition.CONGESTED,
        "road_to_zone-res-beta": RoadCondition.OPEN,
        "road_to_zone-res-gamma": RoadCondition.OPEN,
        "road_to_zone-chem-plant": RoadCondition.BLOCKED,
        "road_to_zone-chem-adjacent": RoadCondition.CONGESTED,
        "road_to_zone-hospital-central": RoadCondition.OPEN,
        "road_to_zone-school-main": RoadCondition.CONGESTED,
        "road_to_zone-dam-north": RoadCondition.OPEN,
        "road_to_zone-dam-downstream": RoadCondition.OPEN,
        "road_to_zone-commercial-hub": RoadCondition.OPEN,
        "road_to_zone-shelter-arena": RoadCondition.OPEN,
        "road_to_zone-shelter-community": RoadCondition.OPEN,
    }

    world.shelters = {
        "shelter-arena": ShelterInfo(
            shelter_id="shelter-arena", zone_id="zone-shelter-arena",
            capacity=600, is_open=False
        ),
        "shelter-community": ShelterInfo(
            shelter_id="shelter-community", zone_id="zone-shelter-community",
            capacity=200, is_open=False
        ),
    }

    world.cascading_events = [
        CascadingEvent(
            event_id="chem-spill-expand",
            description="Chemical plume from Meridian Plant expanding to adjacent residential area! "
                        "Toxic gas levels rising — immediate evacuation required!",
            trigger_step=4,
            warning_text="HAZMAT sensors detect increasing chemical concentrations near Plant-Adjacent Homes. "
                         "Evacuate zone-chem-adjacent IMMEDIATELY.",
            warning_steps_before=2,
            affected_zones=["zone-chem-adjacent"],
            road_closures=[],
            preventable=True,
            prevention_action="evacuate_zone",
            spread_direction="east",
            spread_rate_zones_per_step=1,
            adjacency_map={
                "zone-chem-adjacent": {"east": "zone-res-gamma"},
                "zone-res-gamma": {"east": "zone-res-beta"},
                "zone-res-beta": {"east": "zone-commercial-hub"}
            }
        ),
        CascadingEvent(
            event_id="dam-failure",
            description="North Reservoir Dam has failed! Flash flooding in River Valley Town!",
            trigger_step=8,
            warning_text="Dam engineers report accelerating seepage at North Reservoir. "
                         "Dam failure imminent. EVACUATE River Valley Town.",
            warning_steps_before=3,
            affected_zones=["zone-dam-downstream"],
            road_closures=["road_to_zone-dam-downstream"],
            preventable=True,
            prevention_action="evacuate_zone"
        ),
    ]

    # Mix of true and slightly inaccurate sitreps (fog of war!)
    world.sitreps = [
        SitRep(
            timestamp_hours=0.0, zone_id="zone-res-alpha",
            report="CRITICAL: Multiple collapsed buildings in Alpha District. "
                   "Approximately 50 trapped. 18 dead. Rescue teams urgently needed.",
            severity="critical", casualties_reported=18, trapped_reported=50
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-chem-plant",
            report="HAZMAT ALERT: Meridian Chemical Plant ruptured. 12 workers trapped. "
                   "Unknown chemical release in progress. Road blocked by debris.",
            severity="critical", casualties_reported=3, trapped_reported=12
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-school-main",
            report="School collapse — estimated 30 students trapped. 6 fatalities. "
                   "Teachers conducting headcount.",
            severity="critical", casualties_reported=6, trapped_reported=30
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-res-beta",
            report="Beta District: Moderate damage. Reports of 20 people stuck in elevators "
                   "and damaged buildings.",
            severity="high", casualties_reported=5, trapped_reported=20,
            verified=False  # This one's slightly inaccurate
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-dam-north",
            report="North Reservoir Dam: Minor seepage observed. Engineers dispatched to assess. "
                   "No immediate danger but monitoring recommended.",
            severity="moderate", casualties_reported=0, trapped_reported=0
        ),
    ]

    return world


def build_megadisaster_nightmare() -> DisasterWorld:
    """
    Task 5: MEGADISASTER — EARTHQUAKE + TSUNAMI + INFRASTRUCTURE COLLAPSE (Nightmare)
    - 15 zones, almost all affected
    - Minimal resources
    - 3 shelters at near-capacity
    - Multiple cascading events
    - Must call mutual aid
    - Genuine triage decisions — CANNOT save everyone
    - 16 max steps
    """
    world = DisasterWorld()
    world.incident_name = "Megadisaster — 8.1 Earthquake + Tsunami"
    world.max_steps = 16
    world.weather = "storm"
    world.helicopters_grounded = True
    world.operational_budget = 100000.0

    world.zones = {
        "zone-coast-1": ZoneStatus(
            zone_id="zone-coast-1", zone_type=ZoneType.RESIDENTIAL,
            name="Bayview Coast", population=600,
            status=ZoneState.CRITICAL, casualties=40, trapped_people=80,
            damage_level=0.95, accessibility="blocked"
        ),
        "zone-coast-2": ZoneStatus(
            zone_id="zone-coast-2", zone_type=ZoneType.RESIDENTIAL,
            name="Harbour Heights", population=400,
            status=ZoneState.CRITICAL, casualties=25, trapped_people=55,
            damage_level=0.85, accessibility="limited"
        ),
        "zone-port": ZoneStatus(
            zone_id="zone-port", zone_type=ZoneType.INDUSTRIAL,
            name="Commercial Port", population=150,
            status=ZoneState.CRITICAL, casualties=10, trapped_people=30,
            damage_level=0.9, accessibility="blocked"
        ),
        "zone-downtown-core": ZoneStatus(
            zone_id="zone-downtown-core", zone_type=ZoneType.COMMERCIAL,
            name="Downtown Core", population=500,
            status=ZoneState.CRITICAL, casualties=15, trapped_people=40,
            damage_level=0.6, accessibility="congested"
        ),
        "zone-hospital-general": ZoneStatus(
            zone_id="zone-hospital-general", zone_type=ZoneType.HOSPITAL,
            name="General Hospital", population=250,
            status=ZoneState.CRITICAL, casualties=8, trapped_people=25,
            damage_level=0.5, accessibility="congested"
        ),
        "zone-school-central": ZoneStatus(
            zone_id="zone-school-central", zone_type=ZoneType.SCHOOL,
            name="Central High School", population=300,
            status=ZoneState.CRITICAL, casualties=10, trapped_people=45,
            damage_level=0.7, accessibility="accessible"
        ),
        "zone-res-mid-1": ZoneStatus(
            zone_id="zone-res-mid-1", zone_type=ZoneType.RESIDENTIAL,
            name="Midtown East", population=350,
            status=ZoneState.AFFECTED, casualties=5, trapped_people=20,
            damage_level=0.4, accessibility="accessible"
        ),
        "zone-res-mid-2": ZoneStatus(
            zone_id="zone-res-mid-2", zone_type=ZoneType.RESIDENTIAL,
            name="Midtown West", population=300,
            status=ZoneState.AFFECTED, casualties=3, trapped_people=15,
            damage_level=0.3, accessibility="accessible"
        ),
        "zone-bridge-main": ZoneStatus(
            zone_id="zone-bridge-main", zone_type=ZoneType.BRIDGE,
            name="Main River Bridge", population=0,
            status=ZoneState.AFFECTED, casualties=0, trapped_people=0,
            damage_level=0.6, accessibility="limited"
        ),
        "zone-dam-reservoir": ZoneStatus(
            zone_id="zone-dam-reservoir", zone_type=ZoneType.DAM,
            name="City Reservoir Dam", population=15,
            status=ZoneState.AFFECTED, casualties=0, trapped_people=0,
            damage_level=0.4, accessibility="limited",
            needs_evacuation=True
        ),
        "zone-dam-flood-plain": ZoneStatus(
            zone_id="zone-dam-flood-plain", zone_type=ZoneType.RESIDENTIAL,
            name="Flood Plain Settlement", population=280,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible",
            needs_evacuation=True
        ),
        "zone-industrial-north": ZoneStatus(
            zone_id="zone-industrial-north", zone_type=ZoneType.INDUSTRIAL,
            name="North Industrial", population=100,
            status=ZoneState.AFFECTED, casualties=2, trapped_people=8,
            damage_level=0.4, accessibility="accessible"
        ),
        "zone-shelter-arena": ZoneStatus(
            zone_id="zone-shelter-arena", zone_type=ZoneType.SHELTER,
            name="City Arena Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.1, accessibility="accessible"
        ),
        "zone-shelter-school-gym": ZoneStatus(
            zone_id="zone-shelter-school-gym", zone_type=ZoneType.SHELTER,
            name="School Gymnasium Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
        "zone-shelter-church": ZoneStatus(
            zone_id="zone-shelter-church", zone_type=ZoneType.SHELTER,
            name="Cathedral Shelter", population=0,
            status=ZoneState.NORMAL, casualties=0, trapped_people=0,
            damage_level=0.0, accessibility="accessible"
        ),
    }
    world.total_initial_population = sum(z.population for z in world.zones.values())

    # MINIMAL resources — this is the nightmare
    world.resources = [
        ResourceUnit(unit_id="med_1", resource_type=ResourceType.MEDICAL_TEAM),
        ResourceUnit(unit_id="rescue_1", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="rescue_2", resource_type=ResourceType.RESCUE_SQUAD),
        ResourceUnit(unit_id="heli_1", resource_type=ResourceType.HELICOPTER, status="grounded"),
        ResourceUnit(unit_id="truck_1", resource_type=ResourceType.SUPPLY_TRUCK),
    ]

    world.roads = {
        "road_to_zone-coast-1": RoadCondition.DESTROYED,
        "road_to_zone-coast-2": RoadCondition.FLOODED,
        "road_to_zone-port": RoadCondition.DESTROYED,
        "road_to_zone-downtown-core": RoadCondition.CONGESTED,
        "road_to_zone-hospital-general": RoadCondition.CONGESTED,
        "road_to_zone-school-central": RoadCondition.OPEN,
        "road_to_zone-res-mid-1": RoadCondition.OPEN,
        "road_to_zone-res-mid-2": RoadCondition.OPEN,
        "road_to_zone-bridge-main": RoadCondition.BLOCKED,
        "road_to_zone-dam-reservoir": RoadCondition.CONGESTED,
        "road_to_zone-dam-flood-plain": RoadCondition.OPEN,
        "road_to_zone-industrial-north": RoadCondition.OPEN,
        "road_to_zone-shelter-arena": RoadCondition.OPEN,
        "road_to_zone-shelter-school-gym": RoadCondition.OPEN,
        "road_to_zone-shelter-church": RoadCondition.CONGESTED,
    }

    world.shelters = {
        "shelter-arena": ShelterInfo(
            shelter_id="shelter-arena", zone_id="zone-shelter-arena",
            capacity=500, is_open=False
        ),
        "shelter-gym": ShelterInfo(
            shelter_id="shelter-gym", zone_id="zone-shelter-school-gym",
            capacity=200, is_open=False
        ),
        "shelter-cathedral": ShelterInfo(
            shelter_id="shelter-cathedral", zone_id="zone-shelter-church",
            capacity=300, is_open=False
        ),
    }

    world.cascading_events = [
        # Weather clears at step 3
        CascadingEvent(
            event_id="weather-improvement",
            description="Storm subsiding. Helicopter operations now possible.",
            trigger_step=3,
            warning_text="Meteorology: Storm weakening. Helicopter ops possible next window.",
            warning_steps_before=1,
            affected_zones=[], road_closures=[]
        ),
        # Tsunami afterwave at step 5
        CascadingEvent(
            event_id="tsunami-afterwave",
            description="Secondary tsunami wave strikes coast! Harbour Heights and Bayview re-inundated!",
            trigger_step=5,
            warning_text="Tsunami warning center: Secondary wave approaching coast in ~1 hour. "
                         "Evacuate all coastal zones.",
            warning_steps_before=2,
            affected_zones=["zone-coast-1", "zone-coast-2"],
            road_closures=[],
            preventable=False
        ),
        # Bridge collapse at step 7
        CascadingEvent(
            event_id="bridge-collapse",
            description="Main River Bridge has collapsed! Route between north and south severed!",
            trigger_step=7,
            warning_text="Structural engineers: Main River Bridge showing critical stress. "
                         "Collapse imminent — reroute all traffic.",
            warning_steps_before=2,
            affected_zones=["zone-bridge-main"],
            road_closures=["road_to_zone-bridge-main"],
            preventable=False
        ),
        # Dam breach at step 10
        CascadingEvent(
            event_id="dam-breach-mega",
            description="City Reservoir Dam breached! Flash flooding in Flood Plain Settlement!",
            trigger_step=10,
            warning_text="CRITICAL: City Reservoir Dam at 25% structural integrity. "
                         "Breach expected. EVACUATE Flood Plain Settlement IMMEDIATELY.",
            warning_steps_before=3,
            affected_zones=["zone-dam-flood-plain"],
            road_closures=["road_to_zone-dam-flood-plain"],
            preventable=True,
            prevention_action="evacuate_zone"
        ),
    ]

    world.sitreps = [
        SitRep(
            timestamp_hours=0.0, zone_id="command",
            report="MEGADISASTER DECLARATION: 8.1 earthquake followed by tsunami. "
                   "Multiple areas devastated. Resources critically insufficient. "
                   "This is a mass casualty event. Request mutual aid IMMEDIATELY.",
            severity="catastrophic", casualties_reported=0, trapped_reported=0
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-coast-1",
            report="CRITICAL: Bayview Coast — tsunami-struck. 80+ trapped in debris. "
                   "40+ confirmed dead. Road destroyed — ground access IMPOSSIBLE.",
            severity="critical", casualties_reported=40, trapped_reported=80
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-school-central",
            report="CRITICAL: Central High School collapsed during hours. 45 students trapped. "
                   "10 confirmed casualties. Road is clear — this is accessible.",
            severity="critical", casualties_reported=10, trapped_reported=45
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-hospital-general",
            report="General Hospital structural damage. 25 patients need immediate evacuation. "
                   "ER is overwhelmed with walk-in casualties.",
            severity="critical", casualties_reported=8, trapped_reported=25
        ),
        SitRep(
            timestamp_hours=0.0, zone_id="zone-dam-reservoir",
            report="City Reservoir Dam sustained earthquake damage. Engineers assessing. "
                   "280 people in Flood Plain Settlement are at risk if dam fails.",
            severity="high", casualties_reported=0, trapped_reported=0
        ),
    ]

    # Weather clearing hook
    def custom_weather_hook(w=world):
        if w.current_step >= 3:
            w.weather = "overcast"
            w.helicopters_grounded = False
            for r in w.resources:
                if r.resource_type == ResourceType.HELICOPTER and r.status == "grounded":
                    r.status = "available"
    world._custom_weather_hook = custom_weather_hook

    return world


# ──────────────────────────────────────────────────────────────────────────────
# Task Registry
# ──────────────────────────────────────────────────────────────────────────────

TASK_BUILDERS = {
    "disaster-001-flood": build_flood_easy,
    "disaster-002-earthquake": build_earthquake_medium,
    "disaster-003-hurricane": build_hurricane_hard,
    "disaster-004-cascading": build_cascading_expert,
    "disaster-005-megadisaster": build_megadisaster_nightmare,
}

TASK_METADATA = {
    "disaster-001-flood": {
        "difficulty": "easy",
        "description": "River flood in 3 residential zones. Plenty of resources, all roads open.",
        "max_steps": 8,
    },
    "disaster-002-earthquake": {
        "difficulty": "medium",
        "description": "6.5 earthquake with aftershock. 6 affected zones. Blocked roads. Preemptive evacuation needed.",
        "max_steps": 10,
    },
    "disaster-003-hurricane": {
        "difficulty": "hard",
        "description": "Category 4 hurricane with dam breach risk. Helicopters grounded. Time-critical pre-emptive actions.",
        "max_steps": 12,
    },
    "disaster-004-cascading": {
        "difficulty": "expert",
        "description": "Earthquake + chemical spill + dam breach. Multi-hazard with fog-of-war. Very scarce resources.",
        "max_steps": 14,
    },
    "disaster-005-megadisaster": {
        "difficulty": "nightmare",
        "description": "8.1 earthquake + tsunami. 15 zones, minimal resources, multiple cascading events. Cannot save everyone.",
        "max_steps": 16,
    },
}


def get_task_ids() -> List[str]:
    return list(TASK_BUILDERS.keys())


def build_task(task_id: str) -> DisasterWorld:
    builder = TASK_BUILDERS.get(task_id)
    if not builder:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(TASK_BUILDERS.keys())}")
    return builder()
