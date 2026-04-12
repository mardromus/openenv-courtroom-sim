---
title: DisasterOps-Env
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
---

# 🚨 DisasterOps-Env: Emergency Disaster Response & Resource Coordination

> **The first OpenEnv-compliant environment for training AI agents to coordinate real-world disaster response operations.**

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![HF Space](https://img.shields.io/badge/🤗-Live%20on%20HF%20Spaces-yellow)](https://huggingface.co/spaces/kushagragoyal/Drorpo)

## 💡 What Is This?

DisasterOps-Env simulates the work of an **Emergency Operations Center (EOC) Coordinator** — the person who manages multi-agency response during natural disasters and mass casualty events.

The agent must:
- **Triage incoming situation reports** from multiple affected zones
- **Deploy scarce resources** (medical teams, rescue squads, helicopters, supply trucks) to where they're needed most
- **Evacuate populations** before cascading secondary events (dam breaches, aftershocks, chemical spills)
- **Make moral triage decisions** when resources aren't sufficient to save everyone
- **Race against time** — casualties accumulate every step in unattended critical zones

### Why This Matters

- **3.5M+ disaster-related deaths** since 1970 globally (WMO). Better coordination saves lives.
- **No existing RL environment** for disaster response coordination — this fills a genuine gap.
- **Tests genuine reasoning**: Evidence chain construction, temporal planning, resource optimization, and moral decision-making under uncertainty.

---

## 🧩 Environment Design

### Observation Space

Each observation contains the full situational awareness a coordinator would have:

| Field | Type | Description |
|-------|------|-------------|
| `situation_reports` | `List[SitRep]` | Incoming field reports with severity, casualty counts, zone IDs |
| `zone_statuses` | `Dict[str, ZoneStatus]` | Status of every zone: population, trapped, casualties, damage, accessibility |
| `resource_pool` | `ResourcePool` | Available resources by type (medical, rescue, helicopter, truck) |
| `deployed_resources` | `List[Dict]` | Where each resource unit is currently deployed |
| `road_network` | `Dict[str, str]` | Road conditions: open, congested, blocked, flooded, destroyed |
| `shelter_status` | `Dict[str, ShelterInfo]` | Shelter capacity, occupancy, supply levels |
| `casualty_summary` | `CasualtySummary` | Running totals: at-risk, rescued, evacuated, casualties, trapped |
| `pending_warnings` | `List[str]` | ⚠️ Warnings about upcoming cascading events (dam breach, aftershock) |
| `weather_conditions` | `str` | Affects helicopter operations and road conditions |
| `time_elapsed_hours` | `float` | Simulated elapsed time |

### Action Space

```json
{
  "command": "deploy_resource | evacuate_zone | open_shelter | request_sitrep | assess_zone | call_mutual_aid | recall_resource | submit_report",
  "target_zone": "zone-id-string",
  "resource_type": "medical_team | rescue_squad | helicopter | supply_truck",
  "parameters": {}
}
```

| Action | Effect | Reward Signal |
|--------|--------|---------------|
| `deploy_resource` | Sends resource unit to zone. Rescue squads extract trapped people. Medical teams treat casualties. | +0.04 to critical zone, +0.03 for correct resource matching |
| `evacuate_zone` | Begins population evacuation. Preemptive evacuation before cascading events earns bonus. | +0.08 for preemptive evacuation of warned zone |
| `open_shelter` | Opens emergency shelter for evacuees. | +0.02 |
| `request_sitrep` | Gets detailed situation report. | +0.01 |
| `assess_zone` | Reveals hidden zone details. | +0.01 |
| `call_mutual_aid` | Requests additional resources (arrive in 2 steps). | +0.02 |
| `recall_resource` | Pulls back deployed resource for redeployment. | 0.00 |

### Reward Function

**Multi-dimensional, per-step partial rewards** (NOT binary end-of-episode):

```
Step Reward = Action_Reward + Rescue_Progress - Unattended_Penalty

Final Score (0.0 - 1.0) =
  Lives_Saved (35%) +         # Fraction of trapped people rescued
  Casualty_Prevention (20%) + # Prevented new casualties vs worst case
  Triage_Quality (15%) +      # Deployed to highest-priority zones first
  Proactive_Response (15%) +  # Preempted cascading events
  Efficiency (10%) -          # Decisiveness bonus
  Penalties                   # Mass preventable casualties, failure to call mutual aid
```

**Key Innovation**: The agent receives a **dam breach warning 2-3 steps before it happens**. If it evacuates the downstream zone, it saves 200+ lives. If it prioritizes existing casualties instead, those people die. This creates a genuine **temporal reasoning + moral optimization** challenge.

---

## 🎯 Tasks (5 Scenarios, Easy → Nightmare)

| Task ID | Difficulty | Scenario | Zones | Resources | Steps | Key Challenge |
|---------|-----------|----------|-------|-----------|-------|---------------|
| `disaster-001-flood` | 🟢 Easy | River flooding in 3 residential zones | 5 | Plenty | 8 | Basic triage: deploy resources by casualty count |
| `disaster-002-earthquake` | 🟡 Medium | 6.5 earthquake. Aftershock at step 5 | 8 | Moderate | 10 | Plan for aftershock + blocked roads + preemptive evac |
| `disaster-003-hurricane` | 🔴 Hard | Cat-4 hurricane. Dam at risk. Helicopters grounded | 12 | Scarce | 12 | Weather constraints + preventive vs reactive tradeoff |
| `disaster-004-cascading` | 🟣 Expert | Earthquake + chemical spill + dam breach | 12 | Very scarce | 14 | Multi-hazard + fog of war (inaccurate reports) |
| `disaster-005-megadisaster` | ⚫ Nightmare | 8.1 earthquake + tsunami. Mass casualties | 15 | Minimal | 16 | Cannot save everyone — maximize lives with triage |

### Cascading Event Examples
- **Aftershock**: Damages 2 new zones, destroys a road
- **Dam Breach**: Floods downstream village (250 people) if not preemptively evacuated
- **Chemical Plume Expansion**: Toxic gas spreads to adjacent residential zone
- **Tsunami Afterwave**: Re-inundates coastal zones
- **Bridge Collapse**: Severs route between north and south

---

## 🚀 Setup & Usage

### 1. Run the Server Locally

```bash
pip install -r requirements.txt
uvicorn env:app --host 0.0.0.0 --port 7860
```

### 2. Docker

```bash
docker build -t disasterops-env .
docker run -p 7860:7860 disasterops-env
```

### 3. Run Baseline Inference

```bash
export HF_TOKEN="your_huggingface_token"
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"

python inference.py
```

### 4. Run Specific Task

```bash
export TASK_ID="disaster-003-hurricane"
python inference.py
```

### 5. Validate Submission

```bash
bash scripts/validate-submission.sh https://kushagragoyal-drorpo.hf.space
```

---

## 📊 Baseline Scores

| Task | Difficulty | Baseline Score | Notes |
|------|-----------|---------------|-------|
| `disaster-001-flood` | Easy | ~0.45-0.65 | Model handles basic deployment well |
| `disaster-002-earthquake` | Medium | ~0.30-0.50 | Aftershock preemption is inconsistent |
| `disaster-003-hurricane` | Hard | ~0.20-0.40 | Dam evacuation timing is challenging |
| `disaster-004-cascading` | Expert | ~0.15-0.30 | Multi-hazard coordination is difficult |
| `disaster-005-megadisaster` | Nightmare | ~0.10-0.25 | Triage decisions challenge frontier models |

*Scores vary based on model and temperature. Tested with Qwen2.5-72B-Instruct.*

---

## 🏗️ Project Structure

```
disasterops-env/
├── env.py              # FastAPI server (/reset, /step, /state)
├── schemas.py          # Typed Pydantic models (Action, Observation, StepResult)
├── disaster_sim.py     # Disaster world simulation engine
├── tasks.py            # 5 task scenario definitions
├── grader.py           # Multi-dimensional reward & grading engine
├── inference.py        # Baseline inference script
├── openenv.yaml        # OpenEnv manifest
├── Dockerfile          # Container build
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project metadata
├── README.md           # This file
└── server/
    └── app.py          # Server entry point
```

---

## 🧠 Design Philosophy

1. **Every step matters**: Casualties accumulate in real-time for unattended zones. Wasting a step costs lives.
2. **Information is imperfect**: In expert-level tasks, some field reports are inaccurate (fog of war).
3. **Actions have consequences**: Deploying a helicopter in a storm wastes a turn. Evacuating the wrong zone loses time.
4. **Preemption beats reaction**: The highest rewards come from acting on warnings BEFORE cascading events trigger.
5. **You can't save everyone**: In the nightmare scenario, the agent must make painful triage decisions to maximize total lives saved.

---

*Built for the OpenEnv Hackathon. Simulating disaster response to train better AI coordinators.* 🚨
