"""
DisasterOps-Env: Disaster World Simulation Engine.

Simulates an enterprise-grade disaster response scenario with:
- Geographic zones with populations, damage, and casualty dynamics
- Resource allocation and deployment with constraints
- Road network with dynamic closures
- Cascading secondary events (aftershocks, dam breaches, chemical spills)
- Time-based casualty accumulation in unattended critical zones
- Shelter management and evacuation logistics
"""

import copy
import random
from typing import Dict, List, Optional, Tuple
from schemas import (
    ZoneStatus, ResourceUnit, ResourcePool, SitRep, ShelterInfo,
    CasualtySummary, CascadingEvent, Observation, ZoneState,
    ResourceType, RoadCondition
)


class DisasterWorld:
    """Core simulation engine for the disaster response environment."""

    def __init__(self):
        self.zones: Dict[str, ZoneStatus] = {}
        self.resources: List[ResourceUnit] = []
        self.roads: Dict[str, str] = {}
        self.shelters: Dict[str, ShelterInfo] = {}
        self.cascading_events: List[CascadingEvent] = []
        self.sitreps: List[SitRep] = []
        self.current_step: int = 0
        self.max_steps: int = 10
        self.time_per_step_hours: float = 0.5
        self.weather: str = "clear"
        self.helicopters_grounded: bool = False
        self.incident_name: str = ""
        self.mutual_aid_called: bool = False
        self.mutual_aid_arrives_step: int = -1
        self.action_log: List[str] = []
        self.total_initial_population: int = 0
        self.preventable_casualties: int = 0
        self.operational_budget: float = 0.0
        self.wind_direction: str = "none"
        self._seed: int = 42
        random.seed(self._seed)

    @property
    def time_elapsed_hours(self) -> float:
        return self.current_step * self.time_per_step_hours

    def get_resource_pool(self) -> ResourcePool:
        """Calculate current resource availability."""
        available = [r for r in self.resources if r.status == "available"]
        deployed = [r for r in self.resources if r.status == "deployed"]
        return ResourcePool(
            medical_teams=sum(1 for r in available if r.resource_type == ResourceType.MEDICAL_TEAM),
            rescue_squads=sum(1 for r in available if r.resource_type == ResourceType.RESCUE_SQUAD),
            helicopters=sum(1 for r in available if r.resource_type == ResourceType.HELICOPTER),
            supply_trucks=sum(1 for r in available if r.resource_type == ResourceType.SUPPLY_TRUCK),
            total_available=len(available),
            total_deployed=len(deployed),
            units=[r for r in self.resources]
        )

    def get_deployed_resources(self) -> List[Dict]:
        """Get list of deployed resource details."""
        return [
            {"unit_id": r.unit_id, "type": r.resource_type, "zone": r.deployed_to}
            for r in self.resources if r.status == "deployed"
        ]

    def get_casualty_summary(self) -> CasualtySummary:
        """Calculate running casualty counts."""
        total_pop = 0
        total_rescued = 0
        total_evacuated = 0
        total_casualties = 0
        total_trapped = 0
        for z in self.zones.values():
            total_pop += z.population
            total_rescued += max(0, z.population - z.casualties - z.trapped_people)
            total_evacuated += z.evacuated_count
            total_casualties += z.casualties
            total_trapped += z.trapped_people
        rescue_rate = total_rescued / max(total_pop, 1)
        return CasualtySummary(
            total_population_at_risk=self.total_initial_population,
            total_rescued=total_evacuated,
            total_evacuated=total_evacuated,
            total_casualties=total_casualties,
            total_trapped=total_trapped,
            rescue_rate=round(rescue_rate, 3)
        )

    def get_pending_warnings(self) -> List[str]:
        """Get warnings for upcoming cascading events."""
        warnings = []
        for ev in self.cascading_events:
            if not ev.triggered and ev.warning_text:
                warn_at = ev.trigger_step - ev.warning_steps_before
                if self.current_step >= warn_at and self.current_step < ev.trigger_step:
                    steps_until = ev.trigger_step - self.current_step
                    warnings.append(
                        f"⚠️ WARNING [{steps_until} steps away]: {ev.warning_text}"
                    )
        return warnings

    def get_available_actions(self) -> List[str]:
        """Context-aware list of available actions."""
        actions = ["request_sitrep", "assess_zone", "submit_report"]
        pool = self.get_resource_pool()
        if pool.total_available > 0:
            actions.append("deploy_resource")
        if pool.total_deployed > 0:
            actions.append("recall_resource")
        affected = [z for z in self.zones.values() if z.status in ("affected", "critical")]
        if affected:
            actions.append("evacuate_zone")
        closed_shelters = [s for s in self.shelters.values() if not s.is_open]
        if closed_shelters:
            actions.append("open_shelter")
        blocked = [k for k, v in self.roads.items() if v in ("blocked", "flooded")]
        if blocked:
            actions.append("reroute_traffic")
        if not self.mutual_aid_called:
            actions.append("call_mutual_aid")
        return actions

    def build_observation(self, last_action_result: str = "") -> Observation:
        """Build the complete observation for the agent."""
        # Recalculate zone priority scores
        for z in self.zones.values():
            z.priority_score = self._calculate_priority(z)

        return Observation(
            situation_reports=self.sitreps[-5:],  # Last 5 sitreps
            zone_statuses=copy.deepcopy(self.zones),
            resource_pool=self.get_resource_pool(),
            deployed_resources=self.get_deployed_resources(),
            road_network=dict(self.roads),
            shelter_status=copy.deepcopy(self.shelters),
            casualty_summary=self.get_casualty_summary(),
            time_elapsed_hours=round(self.time_elapsed_hours, 1),
            pending_warnings=self.get_pending_warnings(),
            weather_conditions=self.weather,
            wind_direction=self.wind_direction,
            operational_budget=self.operational_budget,
            available_actions=self.get_available_actions(),
            incident_name=self.incident_name,
            current_step=self.current_step,
            max_steps=self.max_steps,
            last_action_result=last_action_result
        )

    def _calculate_priority(self, zone: ZoneStatus) -> float:
        """Calculate zone urgency priority score."""
        if zone.status in ("normal", "evacuated", "recovered"):
            return 0.0
        score = 0.0
        # Casualties drive priority
        score += min(zone.casualties * 0.01, 0.3)
        # Trapped people are urgent
        score += min(zone.trapped_people * 0.015, 0.3)
        # Damage level
        score += zone.damage_level * 0.2
        # Critical status multiplier
        if zone.status == "critical":
            score *= 1.5
        # No resources = higher priority
        if not zone.resources_present and zone.status in ("affected", "critical"):
            score += 0.15
        # Special zone types get priority
        if zone.zone_type in ("hospital", "school"):
            score *= 1.3
        return round(min(score, 1.0), 3)

    # ──────────────────────────────────────────────────────────────────────
    # Time step: advance the world simulation
    # ──────────────────────────────────────────────────────────────────────

    def advance_time(self):
        """Advance the simulation by one time step. Called at start of each step()."""
        self.current_step += 1

        # Accumulate casualties in unattended critical zones
        for zone_id, zone in self.zones.items():
            if zone.status == "critical" and not zone.resources_present:
                # Accelerating casualty rate for unattended critical zones
                new_casualties = min(
                    max(1, int(zone.trapped_people * 0.08)),
                    zone.trapped_people
                )
                zone.casualties += new_casualties
                zone.trapped_people = max(0, zone.trapped_people - new_casualties)
            elif zone.status == "affected" and not zone.resources_present:
                # Slower casualty rate for affected (non-critical) zones
                new_casualties = min(
                    max(0, int(zone.trapped_people * 0.03)),
                    zone.trapped_people
                )
                zone.casualties += new_casualties
                zone.trapped_people = max(0, zone.trapped_people - new_casualties)

        # Process deployed resources — rescue and treat
        for resource in self.resources:
            if resource.status == "deployed" and resource.deployed_to:
                zone = self.zones.get(resource.deployed_to)
                if zone:
                    self._process_resource_effect(resource, zone)

        # Trigger cascading events
        for event in self.cascading_events:
            if not event.triggered and self.current_step >= event.trigger_step:
                self._trigger_cascading_event(event)

        # Handle spreading events (like chemical plumes based on wind)
        self._process_spreading_hazards()

        # Check mutual aid arrival
        if self.mutual_aid_called and self.current_step >= self.mutual_aid_arrives_step:
            self._deliver_mutual_aid()

        # Update weather effects
        self._update_weather_effects()

        # Generate new sitreps for changed zones
        self._generate_auto_sitreps()

    def _process_resource_effect(self, resource: ResourceUnit, zone: ZoneStatus):
        """Apply the effect of a deployed resource on a zone."""
        if resource.resource_type == ResourceType.MEDICAL_TEAM:
            # Medical teams reduce casualties from trapped people
            treated = min(5, zone.trapped_people)
            zone.trapped_people -= treated
            zone.evacuated_count += treated
        elif resource.resource_type == ResourceType.RESCUE_SQUAD:
            # Rescue squads extract trapped people
            rescued = min(8, zone.trapped_people)
            zone.trapped_people -= rescued
            zone.evacuated_count += rescued
        elif resource.resource_type == ResourceType.HELICOPTER:
            # Helicopters can do rapid evacuation if not grounded
            if not self.helicopters_grounded:
                rescued = min(15, zone.trapped_people)
                zone.trapped_people -= rescued
                zone.evacuated_count += rescued
        elif resource.resource_type == ResourceType.SUPPLY_TRUCK:
            # Supply trucks help with general population evacuation
            evacuated = min(20, max(0, zone.population - zone.evacuated_count - zone.casualties - zone.trapped_people))
            zone.evacuated_count += evacuated

        # Check if zone can be upgraded
        if zone.trapped_people == 0 and zone.status in ("affected", "critical"):
            if zone.evacuated_count >= zone.population * 0.8:
                zone.status = ZoneState.RECOVERED

    def _trigger_cascading_event(self, event: CascadingEvent):
        """Trigger a cascading secondary event."""
        event.triggered = True
        # Check if it was preventable and if agent took prevention action
        if event.preventable and event.prevention_action:
            # Check if evacuation was done for preventable events
            for zone_id in event.affected_zones:
                zone = self.zones.get(zone_id)
                if zone and zone.status == ZoneState.EVACUATING:
                    # Agent preempted — reduce impact
                    continue

        # Apply event effects
        for zone_id in event.affected_zones:
            zone = self.zones.get(zone_id)
            if zone and zone.status not in (ZoneState.EVACUATED, ZoneState.EVACUATING):
                zone.damage_level = min(1.0, zone.damage_level + 0.3)
                additional_trapped = int(zone.population * 0.15)
                zone.trapped_people += additional_trapped
                zone.status = ZoneState.CRITICAL
                # If not evacuated, add preventable casualties
                new_casualties = int(zone.population * 0.05)
                zone.casualties += new_casualties
                self.preventable_casualties += new_casualties

        # Apply road closures
        for road in event.road_closures:
            if road in self.roads:
                self.roads[road] = RoadCondition.DESTROYED

        # Add sitrep
        self.sitreps.append(SitRep(
            timestamp_hours=self.time_elapsed_hours,
            zone_id=event.affected_zones[0] if event.affected_zones else "unknown",
            report=f"🔴 CASCADING EVENT: {event.description}",
            severity="critical",
            casualties_reported=sum(
                self.zones[zid].casualties for zid in event.affected_zones
                if zid in self.zones
            ),
            trapped_reported=sum(
                self.zones[zid].trapped_people for zid in event.affected_zones
                if zid in self.zones
            ),
            verified=True  # Ensure verified=True here correctly
        ))
        
        # Enable spreading if configured
        if event.spread_direction:
            event.spread_active = True

    def _process_spreading_hazards(self):
        """Processes events that spread step-by-step to adjacent zones."""
        for event in self.cascading_events:
            if not event.spread_active or not event.triggered:
                continue

            # Need to find zones to spread to
            new_affected = []
            for current_zone in event.affected_zones:
                if current_zone in event.adjacency_map:
                    # Look up neighbors in the wind direction
                    neighbors_in_wind = event.adjacency_map[current_zone].get(self.wind_direction, "")
                    if neighbors_in_wind:
                        for neighbor in neighbors_in_wind.split(","):
                            neighbor = neighbor.strip()
                            if neighbor and neighbor not in event.affected_zones and neighbor not in new_affected:
                                new_affected.append(neighbor)
            
            # Apply damage to the newly affected zones based on spread rate limit
            # Only spread up to 'spread_rate_zones_per_step' zones per step
            new_affected = new_affected[:event.spread_rate_zones_per_step]
            
            for zone_id in new_affected:
                event.affected_zones.append(zone_id)
                zone = self.zones.get(zone_id)
                if zone and zone.status not in (ZoneState.EVACUATED, ZoneState.EVACUATING):
                    zone.damage_level = min(1.0, zone.damage_level + 0.3)
                    zone.status = ZoneState.CRITICAL
                    new_casualties = int(zone.population * 0.1)
                    zone.casualties += new_casualties
                    zone.trapped_people += int(zone.population * 0.2)
                    self.preventable_casualties += new_casualties
                    
                    self.sitreps.append(SitRep(
                        timestamp_hours=self.time_elapsed_hours,
                        zone_id=zone_id,
                        report=f"☣️ SPREADING HAZARD: Hazard from {event.event_id} has spread to {zone.name} via {self.wind_direction} winds!",
                        severity="catastrophic",
                        casualties_reported=new_casualties,
                        verified=True
                    ))

    def _deliver_mutual_aid(self):
        """Deliver mutual aid resources when they arrive."""
        if not any(r.unit_id.startswith("mutual_aid") for r in self.resources):
            mutual_aid_units = [
                ResourceUnit(unit_id="mutual_aid_med_1", resource_type=ResourceType.MEDICAL_TEAM, status="available"),
                ResourceUnit(unit_id="mutual_aid_rescue_1", resource_type=ResourceType.RESCUE_SQUAD, status="available"),
                ResourceUnit(unit_id="mutual_aid_truck_1", resource_type=ResourceType.SUPPLY_TRUCK, status="available"),
            ]
            self.resources.extend(mutual_aid_units)
            self.sitreps.append(SitRep(
                timestamp_hours=self.time_elapsed_hours,
                zone_id="command",
                report="✅ Mutual aid resources have arrived: 1 medical team, 1 rescue squad, 1 supply truck.",
                severity="low"
            ))

    def _update_weather_effects(self):
        """Update weather and its effects on operations."""
        if self.weather in ("storm", "severe_storm"):
            self.helicopters_grounded = True
        else:
            self.helicopters_grounded = False

    def _generate_auto_sitreps(self):
        """Generate sitreps for zones that changed status."""
        for zone_id, zone in self.zones.items():
            if zone.status == ZoneState.CRITICAL and zone.trapped_people > 0:
                if not zone.resources_present:
                    self.sitreps.append(SitRep(
                        timestamp_hours=self.time_elapsed_hours,
                        zone_id=zone_id,
                        report=f"URGENT: {zone.name} has {zone.trapped_people} trapped, "
                               f"{zone.casualties} casualties. NO resources on scene!",
                        severity="critical",
                        casualties_reported=zone.casualties,
                        trapped_reported=zone.trapped_people,
                        verified=True
                    ))

    # ──────────────────────────────────────────────────────────────────────
    # Action Processing
    # ──────────────────────────────────────────────────────────────────────

    def process_action(self, command: str, target_zone: Optional[str],
                       resource_type: Optional[str],
                       parameters: Optional[Dict]) -> Tuple[str, float]:
        """
        Process an agent action. Returns (result_message, step_reward_delta).
        """
        reward = 0.0
        result = ""
        cost = 0.0

        if command == "deploy_resource":
            cost = 15000 if resource_type == ResourceType.HELICOPTER else 5000
        elif command == "evacuate_zone":
            cost = 10000
        elif command == "call_mutual_aid":
            cost = 100000
        elif command == "open_shelter":
            cost = 15000
            
        if self.operational_budget < cost:
            return f"Insufficient budget! Needed ${cost:,.2f}, have ${self.operational_budget:,.2f}", -0.05
            
        self.operational_budget -= cost

        if command == "deploy_resource":
            result, reward = self._action_deploy(target_zone, resource_type)
        elif command == "evacuate_zone":
            result, reward = self._action_evacuate(target_zone)
        elif command == "open_shelter":
            result, reward = self._action_open_shelter(target_zone)
        elif command == "request_sitrep":
            result, reward = self._action_request_sitrep(target_zone)
        elif command == "assess_zone":
            result, reward = self._action_assess_zone(target_zone)
        elif command == "reroute_traffic":
            result, reward = self._action_reroute(target_zone, parameters)
        elif command == "call_mutual_aid":
            result, reward = self._action_mutual_aid()
        elif command == "recall_resource":
            result, reward = self._action_recall(target_zone, resource_type)
        elif command == "submit_report":
            result, reward = self._action_submit_report(parameters)
        else:
            result = f"Unknown command: {command}"
            reward = -0.02

        self.action_log.append(f"Step {self.current_step}: {command} -> {target_zone} ({result})")
        return result, reward

    def _action_deploy(self, target_zone: Optional[str],
                       resource_type: Optional[str]) -> Tuple[str, float]:
        """Deploy a resource to a zone."""
        if not target_zone or target_zone not in self.zones:
            return f"Invalid zone: {target_zone}", -0.01
        if not resource_type:
            return "Must specify resource_type", -0.01

        zone = self.zones[target_zone]

        # Check accessibility
        if zone.accessibility == "blocked":
            # Check if any road to zone is open
            road_key = f"road_to_{target_zone}"
            if road_key in self.roads and self.roads[road_key] in ("blocked", "destroyed"):
                if resource_type != ResourceType.HELICOPTER:
                    return f"Zone {zone.name} is blocked. Only helicopters can reach it.", -0.01

        # Check helicopter grounding
        if resource_type == ResourceType.HELICOPTER and self.helicopters_grounded:
            return "Helicopters are grounded due to weather conditions!", -0.03

        # Find available resource of this type
        available = [r for r in self.resources
                     if r.resource_type == resource_type and r.status == "available"]
        if not available:
            return f"No available {resource_type} units", -0.01

        unit = available[0]
        unit.status = "deployed"
        unit.deployed_to = target_zone
        zone.resources_present.append(unit.unit_id)

        reward = 0.0
        # Reward for deploying to high-priority zones
        if zone.status == ZoneState.CRITICAL:
            reward += 0.04
            # Bonus for correct resource matching
            if resource_type == ResourceType.RESCUE_SQUAD and zone.trapped_people > 5:
                reward += 0.03
            elif resource_type == ResourceType.MEDICAL_TEAM and zone.casualties > 0:
                reward += 0.03
        elif zone.status == ZoneState.AFFECTED:
            reward += 0.02
        elif zone.status == ZoneState.NORMAL:
            reward -= 0.02  # Penalty for deploying to unaffected zone

        return (f"Deployed {resource_type} ({unit.unit_id}) to {zone.name}. "
                f"Zone has {zone.trapped_people} trapped, {zone.casualties} casualties."), reward

    def _action_evacuate(self, target_zone: Optional[str]) -> Tuple[str, float]:
        """Begin evacuation of a zone."""
        if not target_zone or target_zone not in self.zones:
            return f"Invalid zone: {target_zone}", -0.01

        zone = self.zones[target_zone]
        if zone.status in (ZoneState.EVACUATED, ZoneState.EVACUATING):
            return f"{zone.name} is already being evacuated.", 0.0

        if zone.status == ZoneState.NORMAL:
            # Check if there's a cascading event warning for this zone
            warned = False
            for ev in self.cascading_events:
                if not ev.triggered and target_zone in ev.affected_zones:
                    warn_step = ev.trigger_step - ev.warning_steps_before
                    if self.current_step >= warn_step:
                        warned = True
                        break
            if warned:
                zone.status = ZoneState.EVACUATING
                evacuated = int(zone.population * 0.6)
                zone.evacuated_count += evacuated
                return (f"Preemptive evacuation of {zone.name} started! "
                        f"{evacuated} people moved to safety."), 0.08
            else:
                return f"{zone.name} is not affected. No evacuation needed.", -0.02

        zone.status = ZoneState.EVACUATING
        # Evacuate untrapped people
        evacuable = max(0, zone.population - zone.trapped_people - zone.casualties - zone.evacuated_count)
        evacuated = min(evacuable, 50)  # Can evacuate up to 50 per step
        zone.evacuated_count += evacuated

        reward = 0.01 * (evacuated / max(zone.population, 1)) * 5
        if zone.needs_evacuation:
            reward += 0.04  # Bonus for evacuating zones flagged for evacuation

        return (f"Evacuating {zone.name}: {evacuated} people moved. "
                f"{zone.trapped_people} still trapped."), round(reward, 3)

    def _action_open_shelter(self, target_zone: Optional[str]) -> Tuple[str, float]:
        """Open an emergency shelter."""
        shelter = None
        for s in self.shelters.values():
            if not s.is_open:
                if target_zone and s.zone_id == target_zone:
                    shelter = s
                    break
                elif not target_zone:
                    shelter = s
                    break

        if not shelter:
            return "No closed shelters available to open.", 0.0

        shelter.is_open = True
        return f"Opened shelter {shelter.shelter_id} in {shelter.zone_id} (capacity: {shelter.capacity})", 0.02

    def _action_request_sitrep(self, target_zone: Optional[str]) -> Tuple[str, float]:
        """Request situation report for a zone."""
        if target_zone and target_zone in self.zones:
            zone = self.zones[target_zone]
            sitrep = SitRep(
                timestamp_hours=self.time_elapsed_hours,
                zone_id=target_zone,
                report=(
                    f"SITREP for {zone.name}: Status={zone.status}, "
                    f"Population={zone.population}, Trapped={zone.trapped_people}, "
                    f"Casualties={zone.casualties}, Damage={zone.damage_level:.0%}, "
                    f"Resources on scene: {len(zone.resources_present)}"
                ),
                severity="high" if zone.status in ("critical",) else "moderate",
                casualties_reported=zone.casualties,
                trapped_reported=zone.trapped_people
            )
            self.sitreps.append(sitrep)
            return sitrep.report, 0.01
        else:
            # General sitrep
            critical = [z for z in self.zones.values() if z.status == ZoneState.CRITICAL]
            affected = [z for z in self.zones.values() if z.status == ZoneState.AFFECTED]
            report = (
                f"General SITREP: {len(critical)} critical zones, {len(affected)} affected zones. "
                f"Total casualties: {self.get_casualty_summary().total_casualties}"
            )
            self.sitreps.append(SitRep(
                timestamp_hours=self.time_elapsed_hours,
                zone_id="command",
                report=report,
                severity="high"
            ))
            return report, 0.01

    def _action_assess_zone(self, target_zone: Optional[str]) -> Tuple[str, float]:
        """Assess a zone for damage (reveals hidden information)."""
        if not target_zone or target_zone not in self.zones:
            return f"Invalid zone: {target_zone}", -0.01

        zone = self.zones[target_zone]
        # Assessment reveals true state
        assessment = (
            f"Assessment of {zone.name}: "
            f"Structural damage: {zone.damage_level:.0%}. "
            f"Trapped: {zone.trapped_people}. Casualties: {zone.casualties}. "
            f"Access: {zone.accessibility}. "
            f"Evacuation needed: {'YES' if zone.needs_evacuation else 'NO'}. "
            f"Priority: {zone.priority_score:.2f}"
        )
        return assessment, 0.01

    def _action_reroute(self, target_zone: Optional[str],
                        parameters: Optional[Dict]) -> Tuple[str, float]:
        """Attempt to clear or reroute around blocked roads."""
        blocked_roads = {k: v for k, v in self.roads.items()
                        if v in (RoadCondition.BLOCKED, RoadCondition.FLOODED)}
        if not blocked_roads:
            return "No blocked roads to reroute.", 0.0

        # Clear the first blocked road (or specified one)
        target_road = None
        if target_zone:
            road_key = f"road_to_{target_zone}"
            if road_key in blocked_roads:
                target_road = road_key
        if not target_road:
            target_road = list(blocked_roads.keys())[0]

        old_condition = self.roads[target_road]
        if old_condition == RoadCondition.BLOCKED:
            self.roads[target_road] = RoadCondition.CONGESTED
            # Update zone accessibility
            zone_id = target_road.replace("road_to_", "")
            if zone_id in self.zones:
                self.zones[zone_id].accessibility = "limited"
            return f"Cleared debris on {target_road}. Road now congested but passable.", 0.02
        elif old_condition == RoadCondition.FLOODED:
            return f"{target_road} is flooded. Cannot clear until water recedes.", 0.0
        elif old_condition == RoadCondition.DESTROYED:
            return f"{target_road} is destroyed. Cannot repair in the field.", -0.01

        return "Road rerouting attempted.", 0.0

    def _action_mutual_aid(self) -> Tuple[str, float]:
        """Call for mutual aid — additional resources arrive in 2 steps."""
        if self.mutual_aid_called:
            return "Mutual aid already requested.", 0.0
        self.mutual_aid_called = True
        self.mutual_aid_arrives_step = self.current_step + 2
        return ("Mutual aid requested. Additional resources will arrive in 2 steps "
                "(1 medical team, 1 rescue squad, 1 supply truck)."), 0.02

    def _action_recall(self, target_zone: Optional[str],
                       resource_type: Optional[str]) -> Tuple[str, float]:
        """Recall a deployed resource back to available pool."""
        deployed = [r for r in self.resources if r.status == "deployed"]
        if not deployed:
            return "No deployed resources to recall.", 0.0

        target_unit = None
        for r in deployed:
            if target_zone and r.deployed_to == target_zone:
                if resource_type and r.resource_type == resource_type:
                    target_unit = r
                    break
                elif not resource_type:
                    target_unit = r
                    break
            elif not target_zone:
                target_unit = r
                break

        if not target_unit:
            return "No matching deployed resource found to recall.", 0.0

        old_zone = target_unit.deployed_to
        if old_zone and old_zone in self.zones:
            zone = self.zones[old_zone]
            if target_unit.unit_id in zone.resources_present:
                zone.resources_present.remove(target_unit.unit_id)

        target_unit.status = "available"
        target_unit.deployed_to = None
        return f"Recalled {target_unit.resource_type} ({target_unit.unit_id}) from {old_zone}.", 0.0

    def _action_submit_report(self, parameters: Optional[Dict]) -> Tuple[str, float]:
        """Submit final incident report (typically last action)."""
        summary = self.get_casualty_summary()
        report = (
            f"INCIDENT REPORT SUBMITTED. "
            f"Population at risk: {summary.total_population_at_risk}. "
            f"Evacuated: {summary.total_evacuated}. "
            f"Casualties: {summary.total_casualties}. "
            f"Rescue rate: {summary.rescue_rate:.1%}."
        )
        return report, 0.0

    def is_done(self) -> bool:
        """Check if the episode is complete."""
        if self.current_step >= self.max_steps:
            return True
        # All zones recovered/evacuated
        active = [z for z in self.zones.values()
                  if z.status in (ZoneState.AFFECTED, ZoneState.CRITICAL, ZoneState.EVACUATING)]
        if not active and self.current_step > 0:
            return True
        return False
