import time
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import minimize

import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from schemas import (
    TripRecord,
    BusRecord,
    SimulationConfig,
    QAOACandidate,
    AssignmentItem,
)
from qubo_builder import QUBOModel
from decoder import decode_bitstring
from validator import IndependentValidator


def build_qaoa_circuit(
    n_qubits: int,
    p: int,
    gamma: List[float],
    beta: List[float],
    h_vec: np.ndarray,
    J_mat: np.ndarray,
) -> QuantumCircuit:
    """
    Builds the parameterized QAOA circuit:
    - Layer 0: Hadamards on all qubits
    - For layer s in 0..p-1:
        - Cost unitary e^{-i gamma_s H_C}:
            Rz(2 * gamma_s * h_k) on qubit k
            Rzz(2 * gamma_s * J_{k,l}) between k and l
        - Mixer unitary e^{-i beta_s H_M}:
            Rx(2 * beta_s) on qubit k
    """
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))

    for s in range(p):
        g = gamma[s]
        b = beta[s]

        # 1. Cost unitary
        for k in range(n_qubits):
            if abs(h_vec[k]) > 1e-9:
                qc.rz(2.0 * g * h_vec[k], k)

        for k in range(n_qubits):
            for l in range(k + 1, n_qubits):
                if abs(J_mat[k, l]) > 1e-9:
                    qc.rzz(2.0 * g * J_mat[k, l], k, l)

        # 2. Mixer unitary
        for k in range(n_qubits):
            qc.rx(2.0 * b, k)

    return qc


def run_qaoa_simulation(
    qubo_model: QUBOModel,
    trips: List[TripRecord],
    buses: List[BusRecord],
    validator: IndependentValidator,
    config: SimulationConfig,
) -> Tuple[List[QAOACandidate], Optional[QAOACandidate], float, Optional[str]]:
    """
    Executes QAOA on quantum simulator per Section 9 and 21.4.
    Returns:
      (candidates_list, best_feasible_candidate, runtime_seconds, skip_or_fail_reason)
    """
    start_time = time.perf_counter()
    n_vars = qubo_model.n_vars

    # Check variable cap
    if n_vars > config.variable_cap:
        reason = (
            f"Variable count ({n_vars}) exceeds laptop demonstration cap of {config.variable_cap}. "
            f"QAOA was skipped to maintain responsiveness."
        )
        return [], None, 0.0, reason

    if n_vars == 0:
        return [], None, 0.0, "No eligible assignment variables in QUBO model."

    # 1. Map QUBO to Ising Hamiltonian:
    # x_k = (1 - Z_k) / 2
    # E(x) = sum_k Q_kk x_k + sum_{k<l} Q_kl x_k x_l
    Q = qubo_model.Q
    h_vec = np.zeros(n_vars, dtype=float)
    J_mat = np.zeros((n_vars, n_vars), dtype=float)

    for k in range(n_vars):
        # Contribution from diagonal Q_kk: - Q_kk / 2
        h_vec[k] -= Q[k, k] / 2.0
        # Contribution from off-diagonals Q_kl and Q_lk: - Q_kl / 4
        for l in range(k + 1, n_vars):
            h_vec[k] -= Q[k, l] / 4.0
        for l in range(0, k):
            h_vec[k] -= Q[l, k] / 4.0

    for k in range(n_vars):
        for l in range(k + 1, n_vars):
            J_mat[k, l] = Q[k, l] / 4.0

    # Precompute basis energies for fast expectation evaluation using vectorized NumPy
    m_vals = np.arange(2**n_vars, dtype=np.int32)[:, None]
    bit_shifts = np.arange(n_vars, dtype=np.int32)
    X = ((m_vals >> bit_shifts) & 1).astype(float)  # Shape: (2^N, N)
    # Energy is (X @ Q * X).sum(axis=1)
    basis_energies = np.sum((X @ Q) * X, axis=1)

    p = config.qaoa_p

    # Classical optimization of (gamma, beta)
    def objective_fn(params: np.ndarray) -> float:
        if (time.perf_counter() - start_time) > config.wall_time_limit_sec:
            return 0.0
        gamma = params[:p]
        beta = params[p:]
        qc = build_qaoa_circuit(n_vars, p, gamma, beta, h_vec, J_mat)
        sv = Statevector.from_instruction(qc)
        probs = sv.probabilities()
        exp_val = float(np.dot(probs, basis_energies))
        return exp_val

    # Initial guess for gamma, beta
    rng = np.random.default_rng(config.seed)
    initial_params = np.concatenate([
        rng.uniform(0.1, np.pi / 2, size=p),
        rng.uniform(0.1, np.pi / 4, size=p),
    ])

    opt_res = minimize(
        objective_fn,
        initial_params,
        method="COBYLA",
        options={"maxiter": config.max_iter, "rhobeg": 0.5},
    )

    opt_gamma = opt_res.x[:p]
    opt_beta = opt_res.x[p:]

    # Check timeout
    elapsed = time.perf_counter() - start_time
    if elapsed > config.wall_time_limit_sec:
        return [], None, elapsed, f"QAOA exceeded configured wall-time limit of {config.wall_time_limit_sec}s."

    # Build measurement circuit with optimal parameters
    opt_qc = build_qaoa_circuit(n_vars, p, opt_gamma, opt_beta, h_vec, J_mat)
    opt_qc.measure_all()

    # Simulate shots on AerSimulator
    try:
        sim = AerSimulator(seed_simulator=config.seed)
        job = sim.run(opt_qc, shots=config.shots)
        counts = job.result().get_counts()
    except Exception as e:
        # Fallback to statevector sampling if Aer encounters an issue
        qc_no_meas = build_qaoa_circuit(n_vars, p, opt_gamma, opt_beta, h_vec, J_mat)
        sv = Statevector.from_instruction(qc_no_meas)
        probs = sv.probabilities()
        sample_indices = rng.choice(2**n_vars, size=config.shots, p=probs)
        counts = {}
        for idx in sample_indices:
            # Qiskit endianness key: qubit n-1 at position 0, qubit 0 at end
            raw_key = "".join(str((idx >> k) & 1) for k in reversed(range(n_vars)))
            counts[raw_key] = counts.get(raw_key, 0) + 1

    # Convert measured counts into Candidates
    # Remember: Qiskit Aer key has qubit 0 at key[-1].
    # So bstring[k] = key[-(k + 1)], which is key[::-1].
    total_shots = sum(counts.values())
    candidate_list: List[QAOACandidate] = []

    # Sort bitstrings by frequency descending
    sorted_items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)

    cand_id = 1
    for raw_key, count in sorted_items:
        # Standard bitstring where index k corresponds to variable k (qubo_model.var_list[k])
        bstring = raw_key[::-1]
        energy = qubo_model.evaluate_energy(bstring)
        prob = float(count / total_shots)

        items, stats = decode_bitstring(
            bstring, qubo_model.var_list, trips, buses, source="RAW_QAOA"
        )
        val_res = validator.validate_schedule(items)

        # Update items validation status based on check
        for itm in items:
            if itm.bus_id is not None:
                itm.validation_status = "FEASIBLE" if val_res.is_feasible else "INFEASIBLE"

        candidate_list.append(
            QAOACandidate(
                candidate_id=cand_id,
                bitstring=bstring,
                count=count,
                probability=round(prob, 4),
                qubo_energy=round(energy, 4),
                trips_served_count=stats["trips_served_count"],
                passenger_demand_served=int(stats["passenger_demand_served"]),
                operating_cost=round(stats["operating_cost"], 2),
                service_value=round(stats["service_value"], 2),
                total_utility=round(stats["total_utility"], 4),
                is_feasible=val_res.is_feasible,
                violations_count=val_res.total_violations,
                validation_summary=val_res.summary_message,
                assignments=items,
            )
        )
        cand_id += 1

    # Select best feasible candidate:
    # Section 21.1: "After independent validation, choose the feasible candidate with the highest total utility;
    # break ties by the lexicographically smallest bitstring."
    feasible_cands = [c for c in candidate_list if c.is_feasible]
    best_feasible: Optional[QAOACandidate] = None
    if feasible_cands:
        feasible_cands.sort(key=lambda c: (-c.total_utility, c.bitstring))
        best_feasible = feasible_cands[0]

    runtime = time.perf_counter() - start_time
    return candidate_list, best_feasible, runtime, None
