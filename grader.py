"""
DisasterOps-Env: Multi-dimensional reward & grading engine.

Evaluates agent performance across 4 dimensions:
- Lives Saved: Rescue and evacuation effectiveness
- Triage Quality: Prioritization accuracy  
- Resource Efficiency: Optimal resource matching
- Proactive Response: Preemptive action on cascading events

Rewards are issued per-step as partial progress signals.
"""

from typing import List, Dict, Optional
from disaster_sim import DisasterWorld
from schemas import ZoneState, ResourceType


class DisasterGrader:
    """Evaluates agent performance in the disaster response environment."""

    def __init__(self, world: DisasterWorld):
        self.world = world
        self.initial_trapped = sum(z.trapped_people for z in world.zones.values())
        self.initial_casualties = sum(z.casualties for z in world.zones.values())
        self.initial_population = world.total_initial_population
        self.cumulative_reward = 0.0
        self.step_rewards: List[float] = []
        self.actions_taken: List[str] = []
        self.critical_zones_unattended_steps = 0
        self.preemptive_evacuations = 0
        self.missed_evacuations = 0
        self.mismatched_deployments = 0
        self.correct_priority_deployments = 0
        self.total_deployments = 0

    def evaluate_step(self, command: str, action_reward: float,
                      target_zone: Optional[str] = None,
                      resource_type: Optional[str] = None) -> float:
        """
        Evaluate a single step. Returns reward in [-0.15, +0.15] range.
        Combines the action-specific reward with global heuristics.
        """
        reward = action_reward  # Base reward from action processing

        # ── Penalty: critical zones with no resources ──
        critical_unattended = [
            z for z in self.world.zones.values()
            if z.status == ZoneState.CRITICAL
            and not z.resources_present
            and z.trapped_people > 0
        ]
        if critical_unattended:
            penalty = min(len(critical_unattended) * 0.01, 0.04)
            reward -= penalty
            self.critical_zones_unattended_steps += 1

        # ── Reward: lives rescued this step ──
        current_evacuated = sum(z.evacuated_count for z in self.world.zones.values())
        current_casualties = sum(z.casualties for z in self.world.zones.values())
        current_trapped = sum(z.trapped_people for z in self.world.zones.values())

        # Track progress
        if self.initial_trapped > 0:
            rescue_progress = (self.initial_trapped - current_trapped) / self.initial_trapped
            reward += rescue_progress * 0.01  # Small ongoing reward for rescue progress

        # ── Track deployment quality ──
        if command == "deploy_resource" and target_zone:
            self.total_deployments += 1
            zone = self.world.zones.get(target_zone)
            if zone:
                # Check if this was the highest priority zone
                max_priority = max(
                    (z.priority_score for z in self.world.zones.values()
                     if z.status in (ZoneState.CRITICAL, ZoneState.AFFECTED)),
                    default=0.0
                )
                if zone.priority_score >= max_priority * 0.8:
                    self.correct_priority_deployments += 1
                    reward += 0.02

                # Check resource matching
                if resource_type == ResourceType.RESCUE_SQUAD and zone.trapped_people > 5:
                    pass  # Already rewarded in action processing
                elif resource_type == ResourceType.MEDICAL_TEAM and zone.trapped_people < 3 and zone.casualties < 2:
                    self.mismatched_deployments += 1

        # ── Track preemptive evacuations ──
        if command == "evacuate_zone" and target_zone:
            for ev in self.world.cascading_events:
                if not ev.triggered and target_zone in ev.affected_zones:
                    self.preemptive_evacuations += 1

        self.actions_taken.append(command)

        # Clamp individual step reward
        reward = max(-0.15, min(0.15, reward))
        reward = round(reward, 4)
        self.cumulative_reward += reward
        self.step_rewards.append(reward)

        return reward

    def evaluate_final(self) -> float:
        """
        Calculate final episode score in [0.0, 1.0].
        Called at the end of the episode.
        """
        score = 0.0
        summary = self.world.get_casualty_summary()

        # ── 1. Lives Saved Score (0.0 - 0.35) ──
        total_at_risk = max(self.initial_trapped, 1)
        current_trapped = sum(z.trapped_people for z in self.world.zones.values())
        rescued_fraction = (total_at_risk - current_trapped) / total_at_risk
        lives_score = rescued_fraction * 0.35
        score += lives_score

        # ── 2. Casualty Prevention Score (0.0 - 0.20) ──
        final_casualties = sum(z.casualties for z in self.world.zones.values())
        new_casualties = max(0, final_casualties - self.initial_casualties)
        max_possible_new = self.initial_trapped  # Worst case: all trapped become casualties
        if max_possible_new > 0:
            prevention_rate = 1.0 - (new_casualties / max_possible_new)
            casualty_score = prevention_rate * 0.20
        else:
            casualty_score = 0.20
        score += casualty_score

        # ── 3. Triage Quality Score (0.0 - 0.15) ──
        if self.total_deployments > 0:
            priority_accuracy = self.correct_priority_deployments / self.total_deployments
            triage_score = priority_accuracy * 0.15
        else:
            triage_score = 0.0
        score += triage_score

        # ── 4. Proactive Response Score (0.0 - 0.15) ──
        preventable_events = [ev for ev in self.world.cascading_events if ev.preventable]
        if preventable_events:
            preempted = 0
            for ev in preventable_events:
                if ev.triggered:
                    # Check if affected zones were evacuated before trigger
                    for zone_id in ev.affected_zones:
                        zone = self.world.zones.get(zone_id)
                        if zone and zone.status in (ZoneState.EVACUATING, ZoneState.EVACUATED):
                            preempted += 1
                            break
                else:
                    preempted += 1  # Event didn't trigger = handled
            proactive_score = (preempted / len(preventable_events)) * 0.15
        else:
            proactive_score = 0.10  # No preventable events = partial credit
        score += proactive_score

        # ── 5. Efficiency Score (0.0 - 0.10) ──
        steps_used = len(self.step_rewards)
        max_steps = self.world.max_steps
        # Reward using fewer steps (being decisive)
        if steps_used > 0:
            efficiency = 1.0 - (steps_used / max_steps) * 0.3
            efficiency_score = max(0, efficiency * 0.10)
        else:
            efficiency_score = 0.0
        score += efficiency_score

        # ── 6. Penalties ──
        # Penalty for mass preventable casualties
        if self.world.preventable_casualties > 50:
            score -= 0.10
        elif self.world.preventable_casualties > 20:
            score -= 0.05

        # Penalty for never calling mutual aid on hard tasks
        if self.world.max_steps >= 12 and not self.world.mutual_aid_called:
            score -= 0.03

        return round(max(0.001, min(0.999, score)), 3)

    def get_step_reward_for_logging(self) -> float:
        """Get the latest step reward."""
        return self.step_rewards[-1] if self.step_rewards else 0.0
