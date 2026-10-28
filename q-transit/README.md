# Q-TRANSIT — Quantum-Enhanced Intelligent Bus Scheduling & Route Optimization

**Problem Statement ID:** UC-053  
**Team:** HYPERQUBITS  
**Prototype Category:** Data-driven simulation and optimization decision-support system  
**Development Environment:** VS Code on Windows / PowerShell  

---

## 1. Executive Summary

**Q-TRANSIT** is an end-to-end simulation prototype designed to help public transport planners select feasible bus trips and assign fleet resources while simultaneously balancing:
- Passenger demand on candidate routes
- Bus passenger capacities
- Bus operational availability windows
- Trip start and end times (half-open intervals $[t^{\text{start}}, t^{\text{end}})$)
- Schedule conflicts between overlapping trips assigned to the same bus
- Route operating costs

The system integrates a deterministic **Classical Greedy Baseline**, formulates the scheduling challenge as a **Quadratic Unconstrained Binary Optimization (QUBO)** model, executes the **Quantum Approximate Optimization Algorithm (QAOA)** on a simulated quantum backend (IBM Qiskit & Aer simulator), decodes the measured candidate bitstrings, subjects every candidate to **Independent Classical Validation**, and generates comprehensive side-by-side comparison tables, interactive visual Gantt timelines, and downloadable CSV audit reports.

> **Responsible Quantum Computing Disclaimer:**  
> Q-TRANSIT utilizes simulated quantum computation. Simulator runtimes on a classical CPU/laptop do not represent the physical execution speed of a fault-tolerant quantum computer. In accordance with Section 1.1 and 11.3 of the technical specifications, this prototype reports empirical measurements without claiming unverified quantum advantage.

---

## 2. System Architecture

```text
                     USER
                      |
                      v
             REACT WEB DASHBOARD
       (Vite + TypeScript + Modern CSS)
                      |
                      v
               FASTAPI BACKEND
                      |
                      v
         CSV INGESTION & VALIDATION
                      |
                      v
             DATA PREPROCESSING
                      |
             +--------+--------+
             |                 |
             v                 v
     CLASSICAL BASELINE    QUBO BUILDER
             |                 |
             |                 v
             |           QAOA SIMULATOR
             |           (Qiskit + Aer)
             |                 |
             |                 v
             |        MEASURED BITSTRINGS
             |                 |
             |                 v
             |         DECODE CANDIDATES
             |                 |
             +--------+--------+
                      |
                      v
            INDEPENDENT VALIDATOR
                      |
                      v
            FAIR COMPARISON ENGINE
                      |
                      v
        RESULTS, TIMELINE & EXPLANATIONS
                      |
                      v
            DOWNLOADABLE CSV REPORTS
```

---

## 3. Mathematical Model & Decision Logic

### 3.1 Decision Variables
Binary assignment variables $x_{i,b} \in \{0, 1\}$:
$$x_{i,b} = \begin{cases} 1 & \text{if candidate trip } i \text{ is assigned to bus } b \\ 0 & \text{otherwise} \end{cases}$$

Basic feasibility filtering is performed prior to QUBO formulation:
1. Trip passenger demand must not exceed bus capacity ($\text{demand}_i \le \text{capacity}_b$).
2. Trip duration must be fully contained in bus availability ($t_i^{\text{start}} \ge \text{avail\_from}_b$ and $t_i^{\text{end}} \le \text{avail\_to}_b$).

### 3.2 Service Reward, Cost Normalization & Trip Utility
- Service value: $\text{service\_value}_i = \text{passenger\_demand}_i \times \text{priority}_i$
- Normalization:
  - $\text{norm\_service}_i = \text{service\_value}_i / \max(\text{service\_value})$
  - $\text{norm\_cost}_i = \text{operating\_cost}_i / \max(\text{operating\_cost})$
- Trip utility formula (Section 21.1):
  $$\text{utility}_i = (1 - \text{cost\_weight}) \times \text{norm\_service}_i - \text{cost\_weight} \times \text{norm\_cost}_i$$
  *(Default `cost_weight` = 0.20)*

### 3.3 QUBO Objective & Penalty Terms
Solver minimizes the total energy $E(x)$:
$$E(x) = -\sum_{i,b} \text{utility}_i x_{i,b} + P_{\text{duplicate}} \sum_i \sum_{b < c} x_{i,b} x_{i,c} + P_{\text{overlap}} \sum_{(i,j) \in C} \sum_b x_{i,b} x_{j,b}$$

- **Diagonal Terms ($Q_{kk}$):** $-\text{utility}_i$ rewards serving high-utility trips.
- **Constraint A ($P_{\text{duplicate}}$):** Penalizes assigning the same trip $i$ to multiple buses.
- **Constraint B ($P_{\text{overlap}}$):** Penalizes assigning two overlapping trips $i, j$ ($t_i^{\text{start}} < t_j^{\text{end}}$ and $t_j^{\text{start}} < t_i^{\text{end}}$) to the same bus $b$.

### 3.4 QAOA Quantum Circuit Mapping
Binary variables $x_k$ are mapped to Pauli $Z$ operators ($x_k = \frac{I - Z_k}{2}$), yielding the Ising Cost Hamiltonian:
$$H_C = C \cdot I + \sum_k h_k Z_k + \sum_{k < l} J_{kl} Z_k Z_l$$
The circuit applies alternating layers of cost unitary $U(C, \gamma) = e^{-i \gamma H_C}$ and mixer unitary $U(B, \beta) = e^{-i \beta \sum X_k}$, optimized with classical COBYLA and simulated using IBM Qiskit Aer.

---

## 4. Project Folder Structure

```text
q-transit/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py                 # FastAPI endpoints & pipeline orchestration
│   ├── requirements.txt        # Backend dependencies
│   ├── schemas.py              # Pydantic models for trips, buses, results
│   ├── csv_loader.py           # Strict CSV ingestion & row-level error reporting
│   ├── preprocessing.py        # Normalization, utility & bus eligibility
│   ├── baseline.py             # Deterministic Classical Greedy Baseline
│   ├── qubo_builder.py         # Binary variables & QUBO matrix builder
│   ├── qaoa_solver.py          # Qiskit QAOA circuit simulation & optimizer
│   ├── decoder.py              # Bitstring to schedule mapping
│   ├── validator.py            # Independent classical constraint validator
│   ├── comparison.py           # Fair comparison metric computations
│   ├── reporting.py            # CSV & JSON report generation
│   ├── sample_data/
│   │   ├── trips.csv           # Synthetic 6-trip benchmark
│   │   └── buses.csv           # Synthetic 3-bus fleet benchmark
│   ├── runs/                   # Run-specific generated reports
│   └── tests/
│       ├── conftest.py
│       ├── test_csv_loader.py
│       ├── test_baseline.py
│       ├── test_qubo.py
│       ├── test_validator.py
│       ├── test_reporting.py
│       └── test_simulation_pipeline.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── client.ts
        ├── components/
        │   ├── GanttTimeline.tsx
        │   ├── ComparisonTable.tsx
        │   ├── QUBOInspector.tsx
        │   ├── CandidateDistribution.tsx
        │   ├── ValidatorReportCard.tsx
        │   └── ExportPanel.tsx
        ├── types/
        │   └── index.ts
        └── styles/
            └── index.css
```

---

## 5. Setup & Running Instructions (Windows PowerShell)

### Prerequisites
- **Python 3.10+** (tested on Python 3.15)
- **Node.js 18+** (tested on Node v24)
- **PowerShell**

### Step 1: Clone or Navigate to the Workspace
```powershell
cd "q-transit"
```

### Step 2: Backend Setup
Install Python dependencies:
```powershell
pip install -r backend/requirements.txt
```

Run automated backend test suite (16 tests covering validator, baseline, QUBO, reporting, and full simulation):
```powershell
python -m pytest backend/tests -v
```

Start the FastAPI backend server:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API docs are viewable at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).*

### Step 3: Frontend Setup
In a new PowerShell window, navigate to the frontend directory:
```powershell
cd "q-transit\frontend"
cmd /c npm install
cmd /c npm run build
```

Start the interactive Vite development server:
```powershell
cmd /c npm run dev
```
*Open your browser at [http://localhost:5173](http://localhost:5173).*

---

## 6. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check confirming service status and metadata |
| `GET` | `/api/sample-data` | Retrieves the synthetic benchmark trips and buses dataset |
| `POST` | `/api/validate-csv` | Validates uploaded CSVs, calculates utility & checks eligibility |
| `POST` | `/api/run-simulation` | Executes the complete optimization pipeline |
| `GET` | `/api/results/{run_id}` | Retrieves execution state, baseline, QUBO, QAOA, & metrics |
| `GET` | `/api/results/{run_id}/download/{report_type}` | Downloads CSV/JSON reports (`final_schedule`, `baseline_schedule`, `qaoa_candidates`, `validation_report`, `comparison_metrics`, `run_metadata`) |

---

## 7. Sample Data Specification

### `trips.csv`
```csv
trip_id,route_id,start_min,duration_min,passenger_demand,priority,operating_cost
T001,R1,480,30,42,1.0,500
T002,R2,480,40,35,1.2,600
T003,R3,495,25,22,0.8,350
T004,R1,540,30,28,1.0,500
T005,R2,540,40,38,1.2,600
T006,R3,540,25,18,0.8,350
```

### `buses.csv`
```csv
bus_id,capacity,available_from_min,available_to_min
B001,50,420,720
B002,40,420,720
B003,30,420,720
```

---

## 8. Exported Reports Description

Each optimization execution produces 6 audit reports in `backend/runs/{run_id}/`:
1. **`final_schedule.csv`**: Contains selected trip-bus assignments with passenger demand, bus capacity, operating cost, assignment source, and validation status.
2. **`baseline_schedule.csv`**: The deterministic heuristic schedule, including operational explanations for any unassigned trips.
3. **`qaoa_candidates.csv`**: Every measured bitstring, measurement count, probability, QUBO energy, passenger demand served, total utility, and independent constraint violations count.
4. **`validation_report.csv`**: Independent rule-by-rule verification log covering trip existence, bus existence, single assignment, capacity limits, availability windows, and schedule overlap.
5. **`comparison_metrics.csv`**: Side-by-side performance table evaluating Trips Served, Passenger Demand Served, Operating Cost, Coverage Rate, Passenger-Demand Coverage, Fleet Utilization, Constraint Violations, and Solver Wall-Clock Runtime.
6. **`run_metadata.json`**: Audit trail recording timestamp, random seed, solver settings, penalty weights, normalization maxima, and software environment metadata.

---

## 9. Hackathon Demonstration Checklist

When presenting this prototype:
1. **Load Sample Dataset**: Click **"⚡ Load Sample Dataset"** in the top navigation bar.
2. **Inspect CSV Validation**: Review the row-level verification table showing 6 valid trips, 3 buses, 14 eligible assignment variables, and zero schema errors.
3. **Configure Optimization**: Show the `cost_weight` slider (default 0.20), QAOA circuit depth $p=1$, 512 shots, and penalty weights ($P_{\text{duplicate}}=2.0$, $P_{\text{overlap}}=2.0$).
4. **Execute Optimization**: Click **"Execute Full Optimization Pipeline"** and observe the live stage tracker progress through validation, baseline, QUBO, QAOA simulation, independent validation, and comparison.
5. **Explore Visual Timeline**: Inspect the visual Gantt timeline showing buses on the vertical axis and scheduled trips on the time axis without overlaps.
6. **Review Fair Comparison**: Point out the side-by-side comparison table where both classical baseline and QAOA were evaluated using the identical objective and verified by the independent classical validator.
7. **Inspect QAOA Candidates**: Show the distribution of measured bitstrings, their corresponding QUBO energy, and how infeasible candidates are rejected by the validator.
8. **Download Reports**: Click any of the export cards to download the verified CSV and JSON run artifacts.

