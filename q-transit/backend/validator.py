from typing import List, Dict, Tuple
from schemas import (
    TripRecord,
    BusRecord,
    AssignmentItem,
    ConstraintViolation,
    ScheduleValidationResult,
)


class IndependentValidator:
    def __init__(self, trips: List[TripRecord], buses: List[BusRecord]):
        self.trips = trips
        self.buses = buses
        self.trip_dict: Dict[str, TripRecord] = {t.trip_id: t for t in trips}
        self.bus_dict: Dict[str, BusRecord] = {b.bus_id: b for b in buses}

    def validate_schedule(
        self, schedule: List[AssignmentItem]
    ) -> ScheduleValidationResult:
        violations: List[ConstraintViolation] = []

        # Filter only active assignments (where bus_id is present)
        active_assignments = [item for item in schedule if item.bus_id is not None]

        # 1. Existence checks: trip exists in trips.csv
        missing_trip_violations = []
        for item in active_assignments:
            if item.trip_id not in self.trip_dict:
                missing_trip_violations.append(
                    f"Trip {item.trip_id} assigned to {item.bus_id} does not exist in trips.csv"
                )
        if missing_trip_violations:
            violations.append(
                ConstraintViolation(
                    constraint_name="TRIP_EXISTENCE",
                    violation_count=len(missing_trip_violations),
                    affected_ids=[item.trip_id for item in active_assignments if item.trip_id not in self.trip_dict],
                    explanation="One or more assigned trips do not exist in the uploaded trips dataset.",
                )
            )

        # 2. Existence checks: bus exists in buses.csv
        missing_bus_violations = []
        for item in active_assignments:
            if item.bus_id not in self.bus_dict:
                missing_bus_violations.append(
                    f"Bus {item.bus_id} assigned to trip {item.trip_id} does not exist in buses.csv"
                )
        if missing_bus_violations:
            violations.append(
                ConstraintViolation(
                    constraint_name="BUS_EXISTENCE",
                    violation_count=len(missing_bus_violations),
                    affected_ids=[item.bus_id for item in active_assignments if item.bus_id not in self.bus_dict],
                    explanation="One or more assigned buses do not exist in the uploaded buses dataset.",
                )
            )

        # 3. Duplicate assignment check: each trip is assigned at most once
        trip_assignment_counts: Dict[str, List[str]] = {}
        for item in active_assignments:
            trip_assignment_counts.setdefault(item.trip_id, []).append(item.bus_id)

        duplicate_trips = [
            t_id
            for t_id, b_list in trip_assignment_counts.items()
            if len(b_list) > 1
        ]
        if duplicate_trips:
            explanations = [
                f"Trip {t_id} is assigned {len(trip_assignment_counts[t_id])} times to buses: {', '.join(trip_assignment_counts[t_id])}"
                for t_id in duplicate_trips
            ]
            violations.append(
                ConstraintViolation(
                    constraint_name="NO_DUPLICATE_ASSIGNMENT",
                    violation_count=len(duplicate_trips),
                    affected_ids=duplicate_trips,
                    explanation="; ".join(explanations),
                )
            )

        # 4. Bus capacity check: passenger demand <= bus capacity
        capacity_violations = []
        for item in active_assignments:
            if item.bus_id in self.bus_dict and item.trip_id in self.trip_dict:
                bus = self.bus_dict[item.bus_id]
                trip = self.trip_dict[item.trip_id]
                if trip.passenger_demand > bus.capacity:
                    capacity_violations.append(
                        f"Trip {trip.trip_id} (demand: {trip.passenger_demand}) exceeds Bus {bus.bus_id} capacity ({bus.capacity})"
                    )
        if capacity_violations:
            violations.append(
                ConstraintViolation(
                    constraint_name="BUS_CAPACITY",
                    violation_count=len(capacity_violations),
                    affected_ids=[v.split()[1] for v in capacity_violations],
                    explanation="; ".join(capacity_violations),
                )
            )

        # 5. Bus availability window check: trip start >= bus from and trip end <= bus to
        availability_violations = []
        for item in active_assignments:
            if item.bus_id in self.bus_dict and item.trip_id in self.trip_dict:
                bus = self.bus_dict[item.bus_id]
                trip = self.trip_dict[item.trip_id]
                assert trip.end_min is not None
                if (
                    trip.start_min < bus.available_from_min
                    or trip.end_min > bus.available_to_min
                ):
                    availability_violations.append(
                        f"Trip {trip.trip_id} [{trip.start_min}-{trip.end_min}) lies outside Bus {bus.bus_id} availability window [{bus.available_from_min}-{bus.available_to_min})"
                    )
        if availability_violations:
            violations.append(
                ConstraintViolation(
                    constraint_name="BUS_AVAILABILITY_WINDOW",
                    violation_count=len(availability_violations),
                    affected_ids=[v.split()[1] for v in availability_violations],
                    explanation="; ".join(availability_violations),
                )
            )

        # 6. Overlap check on same bus: half-open interval [start, end)
        # Two trips i, j on same bus overlap iff start_i < end_j and start_j < end_i
        bus_assigned_items: Dict[str, List[AssignmentItem]] = {}
        for item in active_assignments:
            bus_assigned_items.setdefault(item.bus_id, []).append(item)

        overlap_violations = []
        overlap_affected = []
        for bus_id, items in bus_assigned_items.items():
            n = len(items)
            for i in range(n):
                for j in range(i + 1, n):
                    t1 = items[i]
                    t2 = items[j]
                    if (t1.start_min < t2.end_min) and (t2.start_min < t1.end_min):
                        overlap_violations.append(
                            f"Bus {bus_id} has overlapping trips: {t1.trip_id} [{t1.start_min}-{t1.end_min}) and {t2.trip_id} [{t2.start_min}-{t2.end_min})"
                        )
                        overlap_affected.extend([f"{bus_id}:{t1.trip_id}", f"{bus_id}:{t2.trip_id}"])

        if overlap_violations:
            violations.append(
                ConstraintViolation(
                    constraint_name="NO_BUS_OVERLAP",
                    violation_count=len(overlap_violations),
                    affected_ids=list(set(overlap_affected)),
                    explanation="; ".join(overlap_violations),
                )
            )

        total_violations = sum(v.violation_count for v in violations)
        is_feasible = (total_violations == 0)

        summary_msg = (
            "Schedule is 100% FEASIBLE. Passed all independent operational constraints."
            if is_feasible
            else f"Schedule is INFEASIBLE. Detected {total_violations} constraint violation(s) across {len(violations)} rule(s)."
        )

        return ScheduleValidationResult(
            is_feasible=is_feasible,
            total_violations=total_violations,
            violations=violations,
            summary_message=summary_msg,
        )

