from typing import List, Dict, Tuple, Any
import numpy as np
from schemas import TripRecord, BusRecord, QUBOSummary


class QUBOModel:
    def __init__(
        self,
        trips: List[TripRecord],
        buses: List[BusRecord],
        p_duplicate: float = 2.0,
        p_overlap: float = 2.0,
    ):
        self.trips = trips
        self.buses = buses
        self.p_duplicate = p_duplicate
        self.p_overlap = p_overlap

        # 1. Collect all eligible (trip, bus) pairs
        self.var_list: List[Tuple[str, str]] = []
        for t in sorted(trips, key=lambda x: x.trip_id):
            for b_id in sorted(t.eligible_buses):
                self.var_list.append((t.trip_id, b_id))

        self.n_vars = len(self.var_list)
        self.var_to_idx: Dict[Tuple[str, str], int] = {
            pair: i for i, pair in enumerate(self.var_list)
        }
        self.var_names: List[str] = [
            f"x_{pair[0]}_{pair[1]}" for pair in self.var_list
        ]

        # 2. Build N x N upper-triangular matrix Q
        self.Q = np.zeros((self.n_vars, self.n_vars), dtype=float)
        self.linear_breakdown: List[Dict[str, Any]] = []
        self.quadratic_breakdown: List[Dict[str, Any]] = []

        self._build_model()

    def _build_model(self):
        trip_map = {t.trip_id: t for t in self.trips}

        # Diagonal terms: -utility_i
        for idx, (trip_id, bus_id) in enumerate(self.var_list):
            t = trip_map[trip_id]
            util = t.utility or 0.0
            coeff = -float(util)
            self.Q[idx, idx] += coeff
            self.linear_breakdown.append(
                {
                    "index": idx,
                    "variable": self.var_names[idx],
                    "trip_id": trip_id,
                    "bus_id": bus_id,
                    "utility": util,
                    "linear_coeff": coeff,
                    "explanation": f"Service-cost reward: -utility({util:.4f})",
                }
            )

        # Constraint A: Duplicate assignment penalty
        # For the same trip i, bus b != c: P_duplicate * x_{i,b} * x_{i,c}
        for t in self.trips:
            eligible = sorted(t.eligible_buses)
            for i_b in range(len(eligible)):
                for i_c in range(i_b + 1, len(eligible)):
                    b = eligible[i_b]
                    c = eligible[i_c]
                    k = self.var_to_idx[(t.trip_id, b)]
                    l = self.var_to_idx[(t.trip_id, c)]
                    idx1, idx2 = min(k, l), max(k, l)
                    self.Q[idx1, idx2] += self.p_duplicate
                    self.quadratic_breakdown.append(
                        {
                            "var1": self.var_names[idx1],
                            "var2": self.var_names[idx2],
                            "type": "DUPLICATE_TRIP_PENALTY",
                            "penalty": self.p_duplicate,
                            "explanation": f"Constraint A: Duplicate assignment of trip {t.trip_id} to both {b} and {c}.",
                        }
                    )

        # Constraint B: Overlapping trips assigned to the same bus
        # Two trips i and j overlap iff: start_i < end_j and start_j < end_i
        # If both are assigned to the same bus b: P_overlap * x_{i,b} * x_{j,b}
        n_trips = len(self.trips)
        for i in range(n_trips):
            for j in range(i + 1, n_trips):
                t1 = self.trips[i]
                t2 = self.trips[j]
                assert t1.end_min is not None and t2.end_min is not None

                overlaps = (t1.start_min < t2.end_min) and (t2.start_min < t1.end_min)
                if overlaps:
                    common_buses = set(t1.eligible_buses).intersection(
                        set(t2.eligible_buses)
                    )
                    for bus_id in sorted(common_buses):
                        k = self.var_to_idx[(t1.trip_id, bus_id)]
                        l = self.var_to_idx[(t2.trip_id, bus_id)]
                        idx1, idx2 = min(k, l), max(k, l)
                        self.Q[idx1, idx2] += self.p_overlap
                        self.quadratic_breakdown.append(
                            {
                                "var1": self.var_names[idx1],
                                "var2": self.var_names[idx2],
                                "type": "OVERLAP_SCHEDULE_PENALTY",
                                "penalty": self.p_overlap,
                                "explanation": f"Constraint B: Overlap conflict on bus {bus_id} between {t1.trip_id} [{t1.start_min}-{t1.end_min}) and {t2.trip_id} [{t2.start_min}-{t2.end_min}).",
                            }
                        )

    def evaluate_energy(self, bitstring: str) -> float:
        """
        Evaluate QUBO energy E(x) = sum_k Q_kk x_k + sum_{k<l} Q_kl x_k x_l
        bitstring is a string of '0' and '1' of length self.n_vars.
        """
        if len(bitstring) != self.n_vars:
            raise ValueError(
                f"Bitstring length {len(bitstring)} does not match number of variables {self.n_vars}"
            )
        x = np.array([int(c) for c in bitstring], dtype=float)
        # For upper triangular Q: x^T Q x
        energy = float(x @ self.Q @ x)
        return energy

    def to_summary(self) -> QUBOSummary:
        return QUBOSummary(
            num_variables=self.n_vars,
            variable_names=self.var_names,
            linear_terms=self.linear_breakdown,
            quadratic_terms_count=len(self.quadratic_breakdown),
            quadratic_terms_preview=self.quadratic_breakdown[:20],
            matrix_size=self.n_vars,
            penalty_duplicate=self.p_duplicate,
            penalty_overlap=self.p_overlap,
        )

