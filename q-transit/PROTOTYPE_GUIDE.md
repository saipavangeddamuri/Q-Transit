# Q-TRANSIT: Comprehensive Prototype User Manual & Technical Guide

**Project:** Q-TRANSIT (Quantum-Enhanced Intelligent Bus Scheduling and Route Optimization)  
**Problem Statement ID:** UC-053  
**Team:** HYPERQUBITS  
**Category:** Data-driven simulation and optimization decision-support system  
**Target Environment:** Local laptop running VS Code on Windows (PowerShell)  

---

## Table of Contents
1. [Executive Summary & Purpose](#1-executive-summary--purpose)
2. [End-to-End System Workflow](#2-end-to-end-system-workflow)
3. [User Interface Walkthrough: Every Screen & Option Explained](#3-user-interface-walkthrough-every-screen--option-explained)
   - [Top Navigation & Control Bar](#top-navigation--control-bar)
   - [Screen 1: Data Ingestion & Validation](#screen-1-data-ingestion--validation)
   - [Screen 2: Optimization Configuration](#screen-2-optimization-configuration)
   - [Screen 3: Live Progress Tracker (8 Pipeline Stages)](#screen-3-live-progress-tracker-8-pipeline-stages)
   - [Screen 4: Simulation Results & Visuals](#screen-4-simulation-results--visuals)
     - [KPI Summary Cards](#kpi-summary-cards)
     - [Sub-View 1: Visual Bus Schedule Timeline (Gantt)](#sub-view-1-visual-bus-schedule-timeline-gantt)
     - [Sub-View 2: Fair Comparison Table](#sub-view-2-fair-comparison-table)
     - [Sub-View 3: QUBO Mathematical Model Inspector](#sub-view-3-qubo-mathematical-model-inspector)
     - [Sub-View 4: QAOA Measured Candidates & Bitstrings](#sub-view-4-qaoa-measured-candidates--bitstrings)
     - [Sub-View 5: Independent Classical Validator Report](#sub-view-5-independent-classical-validator-report)
     - [Decision Transparency Table](#decision-transparency-table)
   - [Screen 5: Export & Download Center](#screen-5-export--download-center)
4. [Mathematical & Algorithmic Architecture](#4-mathematical--algorithmic-architecture)
   - [Decision Variables & Pre-Filtering](#decision-variables--pre-filtering)
   - [Normalized Service Value & Trip Utility](#normalized-service-value--trip-utility)
   - [QUBO Matrix Formulation](#qubo-matrix-formulation)
   - [QAOA Quantum Circuit & Ising Mapping](#qaoa-quantum-circuit--ising-mapping)
   - [Deterministic Classical Greedy Baseline](#deterministic-classical-greedy-baseline)
   - [Independent Classical Validator (6 Rules)](#independent-classical-validator-6-rules)
5. [Report Artifacts Explained (The 6 Downloadable Files)](#5-report-artifacts-explained-the-6-downloadable-files)
6. [Hackathon Judging & Demonstration Guide](#6-hackathon-judging--demonstration-guide)
7. [Troubleshooting & FAQ](#7-troubleshooting--faq)

---

## 1. Executive Summary & Purpose

Public transit operators face a complex combinatorial challenge every day: deciding which scheduled bus trips to operate and assigning finite bus fleets to those trips. A naive schedule that attempts to run every trip easily causes fleet capacity overruns and conflicting assignments where one bus is double-booked for two overlapping routes. Conversely, a schedule that minimizes operating costs alone starves critical passenger routes of service.

**Q-TRANSIT** solves this challenge by providing an end-to-end, data-driven simulation prototype that:
1. Ingests candidate trips and bus fleet inventories via standard CSV files.
2. Validates domain constraints (capacity, time windows, and schedule overlaps).
3. Evaluates a deterministic **Classical Greedy Baseline**.
4. Formulates the assignment problem as a **Quadratic Unconstrained Binary Optimization (QUBO)** model.
5. Simulates the **Quantum Approximate Optimization Algorithm (QAOA)** using IBM Qiskit and the Aer quantum simulator.
6. Decodes measured quantum bitstrings and subjects every candidate to **Independent Classical Validation**.
7. Compares classical and quantum approaches side-by-side using identical input data and objective definitions.
8. Produces transparent visualizations, plain-language decision explanations, and downloadable audit-ready CSV reports.

---

## 2. End-to-End System Workflow

The architecture follows a strict sequential pipeline where each stage has a single, well-defined responsibility:

```
[CSV Files: trips.csv & buses.csv]
                │
                ▼
      1. INGESTION & VALIDATION ──────► [Row-level error/warning log]
                │
                ▼
      2. PREPROCESSING & UTILITY ─────► [Basic eligibility pruning: demand ≤ cap, interval in window]
                │
        ┌───────┴───────┐
        ▼               ▼
 3. GREEDY BASELINE   4. QUBO BUILDER ──► [Matrix Q: Linear rewards + Conflict Penalties]
        │               │
        │               ▼
        │         5. QAOA SIMULATOR ────► [Ansatz Circuit: Cost & Mixer Unitaries on Qiskit Aer]
        │               │
        │               ▼
        │         6. CANDIDATE DECODER ──► [Bitstrings -> Trip-to-bus assignments]
        │               │
        └───────┬───────┘
                ▼
     7. INDEPENDENT VALIDATOR ────────► [6 Hard operational constraint checks]
                │
                ▼
     8. FAIR COMPARISON & REPORTING ──► [Side-by-side KPIs, Gantt Timeline, 6 Export Files]
```

---

## 3. User Interface Walkthrough: Every Screen & Option Explained

The dashboard runs locally at `http://localhost:5173`. Below is an exhaustive breakdown of every screen, sub-tab, button, slider, and data metric.

### Top Navigation & Control Bar

- **Title & Metadata Badges:**
  - `Q-TRANSIT`: The project name.
  - `UC-053`: Problem statement identifier.
  - `HYPERQUBITS`: Hackathon team identifier.
- **Backend Status Indicator:**
  - Shows a green dot and `Backend: online` when the FastAPI backend at `http://127.0.0.1:8000` is reachable.
  - Shows a red dot and `Backend: offline` if the server is stopped or starting.
- **⚡ Load Sample Dataset Button:**
  - Loads the benchmark synthetic dataset (6 candidate trips and 3 available buses) in one click without manually picking files.
- **Top Workflow Tabs:**
  - `1. Data Ingestion & Validation`: CSV upload, schema check, and data preview.
  - `2. Optimization Configuration`: Objective weights, QAOA parameters, and penalty knobs.
  - `3. Simulation & Results Dashboard`: Real-time pipeline tracker, KPIs, Gantt chart, comparison matrix, QUBO breakdown, and candidate bitstrings.
  - `4. Export CSV Reports`: Download center for verified CSV and JSON files.

---

### Screen 1: Data Ingestion & Validation

This screen handles file inputs, data integrity verification, and eligibility checking.

#### Left Box: `trips.csv`
- **Purpose:** Represents the set of candidate trips being considered for scheduling.
- **Browse File Button:** Allows uploading a `.csv` file from your laptop.
- **Text Area:** Allows directly pasting or manually editing CSV text.
- **Required Columns:**
  - `trip_id`: Unique text identifier for the candidate trip (e.g., `T001`).
  - `route_id`: Route label (e.g., `R1`, `R2`). Used for grouping and visual timeline color-coding.
  - `start_min`: Trip start time in minutes after midnight (e.g., `480` = 08:00 AM).
  - `duration_min`: Trip duration in minutes (e.g., `30`). Must be strictly greater than 0.
  - `passenger_demand`: Estimated number of passengers needing transport (e.g., `42`). Must be $\ge 0$.
  - `priority`: Relative service importance multiplier (e.g., `1.0`, `1.2`). Must be $\ge 0$.
  - `operating_cost`: Cost in currency units to operate this trip (e.g., `500`). Must be $\ge 0$.

#### Right Box: `buses.csv`
- **Purpose:** Represents the available fleet inventory.
- **Browse File Button:** Uploads a fleet `.csv` file.
- **Text Area:** Direct paste or manual editing.
- **Required Columns:**
  - `bus_id`: Unique bus identifier (e.g., `B001`).
  - `capacity`: Maximum passenger capacity (e.g., `50`). Must be $> 0$.
  - `available_from_min`: Start of bus availability in minutes after midnight (e.g., `420` = 07:00 AM).
  - `available_to_min`: End of bus availability (e.g., `720` = 12:00 PM). Must be strictly $> \text{available\_from\_min}$.

#### Action Button: `Verify & Inspect CSVs`
- Executes strict schema parsing, ID uniqueness checks, numeric range assertions, and eligibility filtering via `POST /api/validate-csv`.

#### Data Quality & Eligibility Inspection Report (Visible after validation)
- **Status Badge:** Shows `Valid Dataset` (green) if passes, or `Errors Detected` (red) if issues exist.
- **Summary Metric Cards:**
  - `Trips Received`: Total count of trip rows parsed.
  - `Buses Available`: Total count of bus rows parsed.
  - `Eligible (Trip, Bus) Pairs`: The number of valid assignments where the bus has enough capacity and the trip falls inside the bus's availability window. In the sample data, this equals **14 pairs**.
  - `Unassignable Trips`: Count of trips that cannot fit *any* bus in the fleet (due to demand exceeding all bus capacities or operating outside all availability windows).
- **Reported Issues & Warnings:** Displays row-by-row notices with exact file name, row number, column, and reason.
- **Data Preview Table:** Lists all valid trips alongside calculated `end_min`, `service_value`, normalized values, calculated `utility`, and list of `Eligible Buses`.

---

### Screen 2: Optimization Configuration

This screen lets the planner customize the mathematical objective, quantum circuit parameters, and constraint penalties before launching the run.

#### 1. Operating Cost Weight (`cost_weight`) Slider
- **Range:** `0.00` to `1.00` in steps of `0.05` (Default: `0.20`).
- **Meaning:** Controls the trade-off between maximizing passenger service vs. minimizing fleet operating costs.
  - At `0.00`: Pure service focus (maximize served passengers regardless of cost).
  - At `0.20` (Default): Balanced service-first policy (rewards high passenger routes while keeping costs in check).
  - At `1.00`: Pure cost minimization (favors omitting expensive trips).
- **Formula Preview:** Displays the exact live utility equation:
  $$\text{utility}_i = (1 - \text{cost\_weight}) \cdot \text{norm\_service}_i - \text{cost\_weight} \cdot \text{norm\_cost}_i$$

#### 2. QAOA Circuit Depth ($p$) Dropdown
- **Options:**
  - `p = 1 (Standard Laptop Demo)` (Default): 1 alternating layer of cost and mixer unitaries. Fast, highly reliable, and completes in < 2 seconds.
  - `p = 2 (Deeper Ansatz)`: 2 layers. Increases variational expressiveness.
  - `p = 3 (High Precision)`: 3 layers. Greater circuit depth for exploring deeper parameter spaces.

#### 3. Measurement Shots Dropdown
- **Options:** `256`, `512` (Default), `1024`, `2048` Shots.
- **Meaning:** Number of times the optimized quantum circuit is sampled on the Aer simulator to generate the empirical distribution of bitstrings.

#### 4. Max Classical Optimizer Iterations (COBYLA)
- **Range:** `5` to `100` (Default: `25`).
- **Meaning:** Maximum iteration budget for the classical COBYLA optimizer to tune the circuit rotation angles $(\gamma, \beta)$ to minimize expected QUBO energy.

#### 5. Random Simulation Seed
- **Default:** `42`.
- **Meaning:** Sets the seed for both the classical parameter initializer and the quantum circuit measurement sampler, ensuring 100% reproducible results across runs.

#### 6. Duplicate Trip Penalty ($P_{\text{duplicate}}$)
- **Default:** `2.0`.
- **Meaning:** Energy penalty added to the QUBO objective when the same trip is assigned to two different buses simultaneously. Must be large enough to make duplicate assignments mathematically unfavorable.

#### 7. Schedule Overlap Penalty ($P_{\text{overlap}}$)
- **Default:** `2.0`.
- **Meaning:** Energy penalty added to the QUBO objective when two trips with overlapping time intervals $[t^{\text{start}}, t^{\text{end}})$ are assigned to the same physical bus.

#### 8. Laptop Safety Boundary Callout
- Clarifies the variable cap of **16 binary variables** for real-time laptop execution. (The benchmark 6-trip instance uses 14 variables).

#### Action Button: `🚀 Execute Full Optimization Pipeline`
- Sends configuration to `POST /api/run-simulation`, switches to the Results view, and initiates the live optimization run.

---

### Screen 3: Live Progress Tracker (8 Pipeline Stages)

While the simulation executes, a glowing progress bar displays the exact operational stage without fake percentages:
1. `Validating data`: Strict validation of input CSV rows.
2. `Preprocessing trips`: Computing end times, service values, and normalized utilities.
3. `Building baseline`: Executing the deterministic classical greedy scheduler.
4. `Constructing QUBO`: Building the $N \times N$ upper-triangular matrix $Q$ with diagonal rewards and off-diagonal conflict penalties.
5. `Running QAOA`: Optimizing $(\gamma, \beta)$ angles with COBYLA and sampling bitstrings on `qiskit_aer.AerSimulator`.
6. `Validating candidates`: Passing each sampled bitstring through the independent 6-rule validator.
7. `Comparing results`: Evaluating the fair comparison matrix against the baseline.
8. `Preparing reports`: Writing all 6 CSV and JSON audit artifacts to disk.

---

### Screen 4: Simulation Results & Visuals

Once the run completes, this comprehensive dashboard displays the outcomes.

#### KPI Summary Cards (Top Row)
- **Trips Scheduled:** Number of trips assigned to buses out of candidate trips, plus the eligible-trip coverage percentage.
- **Passengers Served:** Total passengers accommodated across all scheduled trips, plus passenger demand coverage.
- **Operating Cost:** Total operating cost of all scheduled trips, plus fleet utilization percentage.
- **Independent Feasibility:** Green `100% Feasible` badge if zero violations occurred, or red `Infeasible` badge if hard constraints were violated.
- **Solver Runtimes:** Exact wall-clock time for the Classical Greedy Baseline (typically `< 0.001s`) vs. the QAOA Quantum Simulator (typically `~0.08s` to `1.5s`).

---

#### Sub-View 1: Visual Bus Schedule Timeline (Gantt)

An interactive, responsive schedule timeline:
- **Vertical Axis:** Fleet buses (`B001`, `B002`, `B003`) along with their passenger capacities.
- **Horizontal Axis:** Service hours (07:00 to 12:00) with tick marks in HH:MM format.
- **Dashed Background Window:** Shows the exact availability window of each bus.
- **Trip Blocks:** Each assigned trip is rendered as a rounded block occupying its interval $[t^{\text{start}}, t^{\text{end}})$:
  - Color-coded by Route ID (`R1` = Cyan, `R2` = Purple, `R3` = Amber).
  - Displays Trip ID and passenger count (e.g., `T001 42p`).
  - Non-overlapping layout demonstrates that trips on the same bus are sequenced feasibly.
- **Interactive Tooltip:** Hovering over any trip block reveals:
  - Trip ID & Route ID
  - Start Time, End Time & Duration
  - Modeled passenger demand
  - Trip operating cost

---

#### Sub-View 2: Fair Comparison Table

Presents a strict side-by-side comparison between the **Classical Greedy Baseline** and the **Best Feasible QAOA Candidate**:

| Metric | Definition |
|---|---|
| **Trips Served** | Total candidate trips assigned to an available bus. |
| **Passenger Demand Served** | Sum of passenger demand across all assigned trips. |
| **Weighted Service Value** | Sum of $(\text{demand}_i \times \text{priority}_i)$ for assigned trips. |
| **Operating Cost** | Total financial cost of operating the scheduled trips. |
| **Trip Utility** | Sum of normalized service rewards minus normalized operating costs. |
| **Coverage Rate (Eligible Trips)** | $\frac{\text{Trips Served}}{\text{Valid Trips with } \ge 1 \text{ Eligible Bus}} \times 100\%$ |
| **Passenger Demand Coverage** | $\frac{\text{Demand Served}}{\text{Total Demand across Eligible Trips}} \times 100\%$ |
| **Fleet Utilization** | $\frac{\text{Assigned Trip Minutes}}{\text{Total Available Fleet Minutes}} \times 100\%$ |
| **Constraint Violations** | Hard violations detected by the independent validator (0 = Feasible). |
| **Solver Runtime (s)** | Measured wall-clock time spent inside each respective solver routine. |
| **Feasible Schedule** | `Yes` (green badge) if passes all 6 independent checks; `No` (red) if any rule fails. |

---

#### Sub-View 3: QUBO Mathematical Model Inspector

Allows full transparency into how the scheduling problem was encoded for quantum simulation:
- **Matrix Dimension:** Shows the size of the QUBO matrix ($14 \times 14$ for the benchmark).
- **Penalty Constants:** Shows the active $P_{\text{duplicate}}$ and $P_{\text{overlap}}$ values.
- **Tab 1: Diagonal Terms (Linear Rewards):**
  - Lists every variable index $k$, name (e.g., `x_T001_B001`), trip ID, bus ID, trip utility, and the resulting diagonal coefficient $Q_{kk} = -\text{utility}_i$.
- **Tab 2: Off-Diagonal Terms (Conflict Penalties):**
  - Lists interacting variable pairs $(k, l)$ where $k < l$.
  - Indicates the penalty type:
    - `DUPLICATE_TRIP_PENALTY`: For the same trip assigned to two different buses (e.g., `x_T001_B001` and `x_T001_B002`).
    - `OVERLAP_SCHEDULE_PENALTY`: For overlapping trips assigned to the same bus (e.g., `x_T001_B001` and `x_T002_B001`).
  - Displays the penalty value added to $Q_{kl}$ and an explanation.

---

#### Sub-View 4: QAOA Measured Candidates & Bitstrings

Displays the empirical distribution of candidate solutions measured from the quantum circuit:
- **Candidate Index (#):** Ranked by measurement frequency. The best feasible candidate is highlighted with a cyan star (`★`).
- **Measured Bitstring:** A binary string of 0s and 1s of length $N$ (e.g., `00100000110010`). Each position corresponds to a specific $(i, b)$ variable.
- **Frequency & Probability Bar:** Visual bar indicating how many shots collapsed to this bitstring and its percentage of the total sample.
- **QUBO Energy:** The evaluated energy $E(x) = x^T Q x$. Lower (more negative) values indicate better candidate solutions according to the objective and penalty landscape.
- **Trips Served & Utility:** Number of distinct trips scheduled and total utility.
- **Feasibility Badge:**
  - `Feasible` (green badge): Passes all classical checks.
  - `X Violations` (red badge): Shows the exact number of hard violations detected. Hovering shows a tooltip detailing which buses or trips conflicted.

---

#### Sub-View 5: Independent Classical Validator Report

Displays the results of running the independent verification engine against the schedule:
- **6 Standard Operational Rule Cards:**
  1. `Trip Existence Check`: Every assigned trip ID exists in `trips.csv`.
  2. `Bus Existence Check`: Every assigned bus ID exists in `buses.csv`.
  3. `Single Assignment Rule`: No trip is assigned to multiple buses simultaneously.
  4. `Fleet Capacity Limit`: Trip passenger demand $\le$ assigned bus capacity.
  5. `Time Window Compliance`: Trip interval $[t^{\text{start}}, t^{\text{end}})$ is fully contained in bus availability $[\text{avail\_from}, \text{avail\_to}]$.
  6. `No Schedule Conflicts`: No two trips on the same bus have overlapping half-open intervals ($t_i^{\text{start}} < t_j^{\text{end}}$ and $t_j^{\text{start}} < t_i^{\text{end}}$).
- **Rule Badges:** Green `Passed` if compliant, or Red `X Failed` if any violation occurred.
- **Violation Breakdown:** If any rule fails, a red warning panel details the exact constraint, affected trip/bus IDs, and an explanation.

---

#### Decision Transparency Table

Located directly beneath the results views, this table provides plain-language operational accountability for every candidate trip:
- **Trip ID & Route:** Identifies the service.
- **Assigned Bus:** The bus scheduled to run the trip, or `None` if omitted.
- **Status Badge:** `Scheduled` (green) or `Unassigned` (amber).
- **Operational Reason:** Plain-language explanation:
  - *Example (Selected):* `"Assigned to B001: highest priority/utility without schedule conflict."`
  - *Example (Omitted):* `"All eligible buses have conflicting overlapping trip assignments."` or `"Utility is non-positive; operating cost exceeds weighted service reward."`

---

### Screen 5: Export & Download Center

Provides direct download cards for all 6 generated audit reports associated with the active run ID. Each file can be saved directly to your laptop for offline inspection, spreadsheet analysis, or judge presentation.

---

## 4. Mathematical & Algorithmic Architecture

### Decision Variables & Pre-Filtering

Let $T$ be the set of candidate trips and $B$ be the set of available buses. A decision variable $x_{i,b} \in \{0, 1\}$ indicates whether trip $i \in T$ is operated by bus $b \in B$:
$$x_{i,b} = \begin{cases} 1 & \text{if trip } i \text{ is assigned to bus } b \\ 0 & \text{otherwise} \end{cases}$$

To prevent combinatorial explosion and avoid generating obviously infeasible quantum states, pre-filtering eliminates ineligible pairs $(i,b)$ before QUBO construction:
$$\text{Eligible}(i,b) \iff \Big(\text{passenger\_demand}_i \le \text{capacity}_b\Big) \;\land\; \Big(t_i^{\text{start}} \ge \text{available\_from}_b\Big) \;\land\; \Big(t_i^{\text{end}} \le \text{available\_to}_b\Big)$$
where $t_i^{\text{end}} = t_i^{\text{start}} + \text{duration}_i$.

---

### Normalized Service Value & Trip Utility

To ensure that passenger rewards and monetary operating costs are balanced transparently without arbitrary scaling artifacts:

1. **Service Value:**
   $$\text{service\_value}_i = \text{passenger\_demand}_i \times \text{priority}_i$$

2. **Normalization Maxima:**
   $$M_{\text{service}} = \max_{i \in T}(\text{service\_value}_i), \qquad M_{\text{cost}} = \max_{i \in T}(\text{operating\_cost}_i)$$
   If a maximum is zero, the normalized value is set to zero.

3. **Normalized Terms:**
   $$\text{norm\_service}_i = \frac{\text{service\_value}_i}{M_{\text{service}}}, \qquad \text{norm\_cost}_i = \frac{\text{operating\_cost}_i}{M_{\text{cost}}}$$

4. **Trip Utility (Section 21.1):**
   $$\text{utility}_i = (1 - w_{\text{cost}}) \cdot \text{norm\_service}_i - w_{\text{cost}} \cdot \text{norm\_cost}_i$$
   where $w_{\text{cost}} \in [0, 1]$ is the configurable `cost_weight` (default $0.20$).

Trips with $\text{utility}_i \le 0$ provide zero or negative net value (operating cost outweighs passenger service) and are excluded from scheduling.

---

### QUBO Matrix Formulation

QUBO problems are expressed as minimizing a quadratic function of binary variables:
$$\min_{x \in \{0,1\}^N} E(x) = \sum_{k=1}^N Q_{kk} x_k + \sum_{1 \le k < l \le N} Q_{kl} x_k x_l$$

Q-TRANSIT builds the upper-triangular matrix $Q$ with three components:

1. **Linear Objective Rewards (Diagonal $Q_{kk}$):**
   For variable $k = (i, b)$:
   $$Q_{kk} = -\text{utility}_i$$
   Negating the utility converts the maximization of service value into an energy minimization problem.

2. **Constraint A: Single Bus Assignment ($P_{\text{duplicate}}$):**
   A trip should not be operated by more than one bus. For the same trip $i$ across two distinct buses $b \ne c$:
   $$Q_{(i,b), (i,c)} \mathrel{+}= P_{\text{duplicate}}$$
   If both $x_{i,b} = 1$ and $x_{i,c} = 1$, the product $x_{i,b} x_{i,c} = 1$, penalizing the energy by $+P_{\text{duplicate}}$.

3. **Constraint B: No Same-Bus Overlapping Trips ($P_{\text{overlap}}$):**
   Two trips $i$ and $j$ conflict if their half-open time intervals $[t^{\text{start}}, t^{\text{end}})$ overlap:
   $$\text{Overlap}(i,j) \iff \Big(t_i^{\text{start}} < t_j^{\text{end}}\Big) \;\land\; \Big(t_j^{\text{start}} < t_i^{\text{end}}\Big)$$
   For any conflicting pair $(i, j)$ assigned to the same bus $b$:
   $$Q_{(i,b), (j,b)} \mathrel{+}= P_{\text{overlap}}$$

---

### QAOA Quantum Circuit & Ising Mapping

To execute the QUBO on a quantum simulator, binary variables $x_k \in \{0, 1\}$ are mapped to Pauli $Z$ operators acting on qubits:
$$x_k = \frac{I - Z_k}{2}$$
Substituting this transformation into $E(x)$ converts the QUBO matrix into an Ising Cost Hamiltonian:
$$H_C = C \cdot I + \sum_{k=1}^N h_k Z_k + \sum_{1 \le k < l \le N} J_{kl} Z_k Z_l$$
where:
$$h_k = -\frac{Q_{kk}}{2} - \sum_{l > k} \frac{Q_{kl}}{4} - \sum_{l < k} \frac{Q_{lk}}{4}, \qquad J_{kl} = \frac{Q_{kl}}{4}, \qquad C = \sum_k \frac{Q_{kk}}{2} + \sum_{k < l} \frac{Q_{kl}}{4}$$

The QAOA circuit is built in Qiskit as follows:
1. **Initial State:** Apply Hadamard gates $H^{\otimes N}$ to initialize the equal superposition state $|+\rangle^{\otimes N}$.
2. **Alternating Layers (Depth $p$):** For layer $s = 1, \dots, p$:
   - **Cost Unitary $e^{-i \gamma_s H_C}$:** Applied via single-qubit $R_Z(2 \gamma_s h_k)$ gates and two-qubit $R_{ZZ}(2 \gamma_s J_{kl})$ gates.
   - **Mixer Unitary $e^{-i \beta_s H_M}$:** Applied via single-qubit $R_X(2 \beta_s)$ gates where $H_M = \sum_{k=1}^N X_k$.
3. **Classical Optimization:** The classical optimizer (COBYLA) iteratively tunes the variational parameters $(\vec{\gamma}, \vec{\beta})$ to minimize the expectation value $\langle \psi(\vec{\gamma}, \vec{\beta}) | H_C | \psi(\vec{\gamma}, \vec{\beta}) \rangle$.
4. **Measurement:** The optimal parameterized circuit is measured over 512 shots on `AerSimulator(seed_simulator=seed)`.

---

### Deterministic Classical Greedy Baseline

The greedy baseline acts as an empirical benchmark. Its rules are deterministic and transparent:
1. Filter out candidate trips with $\text{utility}_i \le 0$ or no eligible buses.
2. Sort candidate trips in descending order of utility ($\text{utility}_i$ highest to lowest).
3. Tie-breaking rule: If two trips have identical utility, sort by `trip_id` in ascending lexicographical order.
4. Iterate through the sorted trips. For each trip, check eligible buses sorted by `bus_id` in ascending order (`B001`, `B002`, `B003`).
5. Assign the trip to the first bus that has no time overlap with already-assigned trips.
6. If all eligible buses have overlapping conflicts, mark the trip as unassigned with an explicit explanation.

---

### Independent Classical Validator (6 Rules)

The validator is implemented in [`validator.py`](file:///c:/Users/ROSHAN/OneDrive/Documents/SAI%20pvan/q-transit/backend/validator.py) as an isolated module completely independent of the QUBO builder and QAOA solver:
1. `TRIP_EXISTENCE`: Asserts that every assigned trip exists in `trips.csv`.
2. `BUS_EXISTENCE`: Asserts that every assigned bus exists in `buses.csv`.
3. `NO_DUPLICATE_ASSIGNMENT`: Asserts that $\sum_b x_{i,b} \le 1$ for all trips $i$.
4. `BUS_CAPACITY`: Asserts that $\text{passenger\_demand}_i \le \text{capacity}_b$ for all assignments $(i, b)$.
5. `BUS_AVAILABILITY_WINDOW`: Asserts that $[t_i^{\text{start}}, t_i^{\text{end}}) \subseteq [\text{available\_from}_b, \text{available\_to}_b]$.
6. `NO_BUS_OVERLAP`: Asserts that for any two trips $i \ne j$ assigned to the same bus $b$, $\text{Overlap}(i,j) = \text{False}$.

A schedule is marked `FEASIBLE` if and only if total violations across all 6 rules equal 0. If even one violation exists, it is marked `INFEASIBLE`.

---

## 5. Report Artifacts Explained (The 6 Downloadable Files)

Each run generates 6 standalone audit artifacts stored in `backend/runs/{run_id}/`:

### 1. `final_schedule.csv`
Contains the final selected schedule (the best feasible QAOA candidate if one was found, otherwise the classical baseline):
- `trip_id`: Candidate trip identifier.
- `route_id`: Route identifier.
- `bus_id`: Assigned bus identifier, or `UNASSIGNED`.
- `start_min`, `end_min`: Operational time interval.
- `passenger_demand`: Modeled passenger demand.
- `capacity`: Capacity of the assigned bus.
- `operating_cost`: Financial cost to operate the trip.
- `assignment_source`: Origin of the schedule (`FINAL`).
- `validation_status`: `FEASIBLE` or `UNASSIGNED`.

### 2. `baseline_schedule.csv`
Contains the schedule generated by the deterministic classical greedy baseline, including operational reasons for any unassigned trips.

### 3. `qaoa_candidates.csv`
A complete audit log of all unique bitstrings measured by QAOA on the quantum simulator:
- `candidate_id`: Ordinal ranking by measurement count.
- `bitstring`: Raw binary decision string (length $N$).
- `count`, `probability`: Number of shots that collapsed to this state and relative frequency.
- `qubo_energy`: Evaluated QUBO energy $E(x) = x^T Q x$.
- `trips_served_count`, `passenger_demand_served`: Operational yield.
- `operating_cost`, `service_value`, `total_utility`: Financial and service metrics.
- `is_feasible`: `Yes` or `No`.
- `violations_count`: Number of constraint violations detected.
- `validation_summary`: Plain-language explanation of violations.

### 4. `validation_report.csv`
The official compliance report generated by the independent classical validator:
- `constraint_name`: Name of the rule evaluated.
- `violation_count`: Count of detected violations (0 = Pass).
- `affected_identifiers`: Comma-separated list of affected trip or bus IDs.
- `explanation`: Compliance confirmation or explanation of the failure.

### 5. `comparison_metrics.csv`
Side-by-side performance table containing all documented metrics for both the Greedy Baseline and Best Feasible QAOA Candidate.

### 6. `run_metadata.json`
Full audit trail of the run:
- `run_id`, `status`, `timestamp_utc`
- Solver settings: `cost_weight`, `qaoa_p`, `shots`, `max_iter`, `seed`, `p_duplicate`, `p_overlap`, `variable_cap`, `wall_time_limit_sec`
- Normalization constants: `max_service_value`, `max_operating_cost`
- Wall-clock solver runtimes for baseline and QAOA
- Warnings and system disclaimers

---

## 6. Hackathon Judging & Demonstration Guide

Follow this 5-minute pitch sequence when demonstrating the prototype to judges:

### Minute 1: The Problem & The Solution
> *"Public transit operators have to schedule bus trips without double-booking buses or exceeding passenger capacities, all while balancing passenger demand against operating costs. Q-TRANSIT is an intelligent decision-support system that combines classical heuristics with simulated quantum optimization (QAOA) to solve this scheduling challenge."*

### Minute 2: Ingestion & Eligibility
1. Open `http://localhost:5173`.
2. Click **`⚡ Load Sample Dataset`**.
3. Point out that the dataset contains 6 trips and 3 buses.
4. Click **`Verify & Inspect CSVs`** and explain:
   - Basic eligibility pruning: Bus capacity must fit demand, and trip times must lie inside bus availability.
   - This pre-filters the search space down to 14 binary assignment variables.

### Minute 3: Objective & Quantum Setup
1. Switch to **`2. Optimization Configuration`**.
2. Show the **Operating Cost Weight** slider:
   - Explain how it normalizes service rewards and costs into a transparent utility metric.
3. Highlight the QAOA settings: Depth $p=1$, 512 shots, seed 42, and the $P_{\text{duplicate}}$ and $P_{\text{overlap}}$ penalty values.
4. Click **`🚀 Execute Full Optimization Pipeline`**.

### Minute 4: Results & Visual Timeline
1. Show the **Visual Bus Schedule Timeline (Gantt)**:
   - Point out that trips on each bus follow non-overlapping time intervals.
   - Hover over a trip block to show the popup details.
2. Switch to the **Fair Comparison Table**:
   - Highlight the side-by-side metrics (trips served, demand served, coverage rate, runtime).
   - Address the results honestly:
     > *"Notice that our deterministic greedy baseline found a 6-trip schedule, while QAOA found a 4-trip feasible schedule. We report actual empirical findings rather than claiming artificial quantum advantage on small toy instances."*

### Minute 5: Validation & Export
1. Click **`🛡️ Classical Validator Report`**:
   - Emphasize that every schedule is audited by an independent 6-rule validator that does not reuse optimizer assumptions.
2. Click **`4. Export CSV Reports`**:
   - Download `final_schedule.csv` and `comparison_metrics.csv` to show that the prototype generates audit-ready reports.

---

## 7. Troubleshooting & FAQ

#### Q1: Why did QAOA schedule 4 trips while the greedy baseline scheduled 6 trips?
**A:** On small, small-qubit demonstration instances, classical greedy heuristics can easily identify near-optimal combinations in negligible time. QAOA is an approximate variational quantum algorithm designed for large combinatorial search landscapes. Showing that the greedy baseline outperforms QAOA on a 14-variable laptop simulation is the scientifically honest outcome demanded by Section 1.1 and Section 11.3 of the project specification.

#### Q2: Why are some measured QAOA bitstrings marked "Infeasible"?
**A:** In a QUBO formulation, hard operational constraints are enforced via soft penalty terms ($P_{\text{duplicate}}$ and $P_{\text{overlap}}$). A quantum circuit samples from a probability distribution over all computational basis states. States with higher energy (constraint violations) have lower probability, but can still be sampled. The **Independent Classical Validator** catches these violations and ensures that only 100% compliant candidates are considered.

#### Q3: What happens if a trip has passenger demand greater than all buses?
**A:** The CSV validation engine detects this during preprocessing. The trip is flagged as unassignable, a warning is added to the report, and the trip is excluded from the QUBO formulation. It is never silently dropped.

#### Q4: What happens if the variable cap (16 variables) is exceeded?
**A:** To keep laptop demonstrations responsive and prevent exponential statevector simulation slowdowns, the system automatically skips QAOA, sets the run status to `partial`, preserves the classical baseline schedule, and provides an explanation.

#### Q5: How do I restart the backend or frontend servers?
- **Backend:** In PowerShell, run:
  ```powershell
  python -m uvicorn main:app --host 127.0.0.1 --port 8000 --app-dir "q-transit\backend"
  ```
- **Frontend:** In PowerShell, run:
  ```powershell
  cd "q-transit\frontend"
  cmd /c npm run dev -- --host
  ```

