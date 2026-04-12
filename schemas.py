"""
DisasterOps-Env: Typed Pydantic models for the Disaster Response Environment.

Defines the complete API contract: Action, Observation, StepResult, and all
supporting types for zone status, resources, situation reports, and shelters.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class ZoneType(str, Enum):
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    HOSPITAL = "hospital"
    SCHOOL = "school"
    BRIDGE = "bridge"
    DAM = "dam"
    COMMERCIAL = "commercial"
    SHELTER = "shelter"

class ZoneState(str, Enum):
    NORMAL = "normal"
    AFFECTED = "affected"
    CRITICAL = "critical"
    EVACUATING = "evacuating"
    EVACUATED = "evacuated"
    RECOVERED = "recovered"
    DESTROYED = "destroyed"

class ResourceType(str, Enum):
    MEDICAL_TEAM = "medical_team"
    RESCUE_SQUAD = "rescue_squad"
    HELICOPTER = "helicopter"
    SUPPLY_TRUCK = "supply_truck"

class CommandType(str, Enum):
    DEPLOY_RESOURCE = "deploy_resource"
    EVACUATE_ZONE = "evacuate_zone"
    OPEN_SHELTER = "open_shelter"
    REQUEST_SITREP = "request_sitrep"
    ASSESS_ZONE = "assess_zone"
    REROUTE_TRAFFIC = "reroute_traffic"
    CALL_MUTUAL_AID = "call_mutual_aid"
    RECALL_RESOURCE = "recall_resource"
    SUBMIT_REPORT = "submit_report"

class Severity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"

class RoadCondition(str, Enum):
    OPEN = "open"
    CONGESTED = "congested"
    BLOCKED = "blocked"
    FLOODED = "flooded"
    DESTROYED = "destroyed"


# ──────────────────────────────────────────────────────────────────────────────
# Supporting Models
# ──────────────────────────────────────────────────────────────────────────────

class ZoneStatus(BaseModel):
    """Status of a single zone in the disaster area."""
    zone_id: str
    zone_type: str
    name: str
    population: int
    status: str
    casualties: int = 0
    trapped_people: int = 0
    damage_level: float = Field(0.0, ge=0.0, le=1.0)
    resources_present: List[str] = Field(default_factory=list)
    accessibility: str = "accessible"
    priority_score: float = 0.0
    needs_evacuation: bool = False
    evacuated_count: int = 0

class ResourceUnit(BaseModel):
    """A single resource unit."""
    unit_id: str
    resource_type: str
    status: str = "available"           # available, deployed, in_transit, grounded
    deployed_to: Optional[str] = None   # zone_id if deployed
    capacity: int = 1                   # how many people it can handle per step

class ResourcePool(BaseModel):
    """All available resources."""
    medical_teams: int = 0
    rescue_squads: int = 0
    helicopters: int = 0
    supply_trucks: int = 0
    total_available: int = 0
    total_deployed: int = 0
    units: List[ResourceUnit] = Field(default_factory=list)

class SitRep(BaseModel):
    """Incoming situation report from a field team."""
    timestamp_hours: float
    zone_id: str
    report: str
    severity: str
    verified: bool = True
    casualties_reported: int = 0
    trapped_reported: int = 0

class ShelterInfo(BaseModel):
    """Status of an emergency shelter."""
    shelter_id: str
    zone_id: str
    capacity: int
    occupancy: int = 0
    is_open: bool = False
    supplies_remaining: float = Field(1.0, ge=0.0, le=1.0)

class CasualtySummary(BaseModel):
    """Running casualty counts."""
    total_population_at_risk: int = 0
    total_rescued: int = 0
    total_evacuated: int = 0
    total_casualties: int = 0
    total_trapped: int = 0
    rescue_rate: float = 0.0

class CascadingEvent(BaseModel):
    """A secondary event that triggers during the disaster."""
    event_id: str
    description: str
    trigger_step: int
    warning_text: Optional[str] = None
    warning_steps_before: int = 2
    affected_zones: List[str] = Field(default_factory=list)
    road_closures: List[str] = Field(default_factory=list)
    triggered: bool = False
    preventable: bool = False
    prevention_action: Optional[str] = None
    
    # Spreading hazard fields
    spread_active: bool = False
    spread_direction: Optional[str] = None  # e.g., 'north', 'south'
    spread_rate_zones_per_step: int = 1
    adjacency_map: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    # adjacency_map format: {"zone_id": {"north": "other_zone", "east": "..."}}


# ──────────────────────────────────────────────────────────────────────────────
# Core API Models
# ──────────────────────────────────────────────────────────────────────────────

class Action(BaseModel):
    """Agent's action in the disaster response environment."""
    command: str = Field(
        ...,
        description="Action type: deploy_resource, evacuate_zone, open_shelter, "
                    "request_sitrep, assess_zone, reroute_traffic, call_mutual_aid, "
                    "recall_resource, submit_report"
    )
    target_zone: Optional[str] = Field(
        None,
        description="Target zone ID (e.g., 'zone-residential-north')"
    )
    resource_type: Optional[str] = Field(
        None,
        description="Resource type: medical_team, rescue_squad, helicopter, supply_truck"
    )
    parameters: Optional[Dict] = Field(
        default_factory=dict,
        description="Additional parameters for the command"
    )

class Observation(BaseModel):
    """What the agent observes after each action."""
    situation_reports: List[SitRep] = Field(default_factory=list)
    zone_statuses: Dict[str, ZoneStatus] = Field(default_factory=dict)
    resource_pool: ResourcePool = Field(default_factory=ResourcePool)
    deployed_resources: List[Dict] = Field(default_factory=list)
    road_network: Dict[str, str] = Field(default_factory=dict)
    shelter_status: Dict[str, ShelterInfo] = Field(default_factory=dict)
    casualty_summary: CasualtySummary = Field(default_factory=CasualtySummary)
    operational_budget: float = 0.0
    time_elapsed_hours: float = 0.0
    pending_warnings: List[str] = Field(default_factory=list)
    weather_conditions: str = "clear"
    wind_direction: str = "none"
    available_actions: List[str] = Field(default_factory=list)
    incident_name: str = ""
    current_step: int = 0
    max_steps: int = 0
    last_action_result: str = ""

class StepResult(BaseModel):
    """Result returned from step(), reset(), and state()."""
    observation: Observation
    reward: float = 0.0
    done: bool = False
    error: Optional[str] = None
