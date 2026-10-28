import time
from typing import List, Dict, Tuple
from schemas import TripRecord, BusRecord, AssignmentItem


def run_greedy_baseline(
    trips: List[TripRecord],
    buses: List[BusRecord],
) -> Tuple[List[AssignmentItem], float]:
    """
    Deterministic classical greedy baseline per Section 21.1:
    1. Filter out trips with utility <= 0.
    2. Sort candidate trips by utility descending, then by trip_id ascending.
    3. Iterate through trips: assign to first eligible, conflict-free bus_id in ascending order.
    4. Intervals are half-open [start_min, end_min).
    5. Returns (assignments, runtime_seconds).
    """
    start_time = time.perf_counter()

    bus_map = {b.bus_id: b for b in buses}
    # Track occupied intervals for each bus: list of (start_min, end_min, trip_id)
    bus_schedule: Dict[str, List[Tuple[int, int, str]]] = {
        b.bus_id: [] for b in buses
    }

    # Separate eligible trips vs trips with utility <= 0 or no eligible buses
    assignable_trips = [t for t in trips if t.eligible_buses and (t.utility or 0.0) > 0.0]

    # Sort: utility descending, tie-break by trip_id ascending
    sorted_trips = sorted(
        assignable_trips, key=lambda t: (-(t.utility or 0.0), t.trip_id)
    )

    assigned_trip_ids = set()
    result_items: List[AssignmentItem] = []

    for trip in sorted_trips:
        assert trip.end_min is not None
        assigned_bus_id = None
        # Check eligible buses sorted in ascending order
        for bus_id in sorted(trip.eligible_buses):
            intervals = bus_schedule[bus_id]
            # Check overlap: trip [t_start, t_end) overlaps with [s_start, s_end) iff
            # t_start < s_end and s_start < t_end
            has_conflict = False
            for s_start, s_end, other_trip_id in intervals:
                if trip.start_min < s_end and s_start < trip.end_min:
                    has_conflict = True
                    break

            if not has_conflict:
                assigned_bus_id = bus_id
                bus_schedule[bus_id].append(
                    (trip.start_min, trip.end_min, trip.trip_id)
                )
                break

        if assigned_bus_id is not None:
            assigned_trip_ids.add(trip.trip_id)
            result_items.append(
                AssignmentItem(
                    trip_id=trip.trip_id,
                    route_id=trip.route_id,
                    bus_id=assigned_bus_id,
                    start_min=trip.start_min,
                    end_min=trip.end_min,
                    passenger_demand=trip.passenger_demand,
                    capacity=bus_map[assigned_bus_id].capacity,
                    operating_cost=trip.operating_cost,
                    assignment_source="BASELINE",
                    validation_status="FEASIBLE",
                    utility=trip.utility or 0.0,
                    selection_reason=f"Assigned to {assigned_bus_id}: highest priority/utility without schedule conflict.",
                )
            )
        else:
            result_items.append(
                AssignmentItem(
                    trip_id=trip.trip_id,
                    route_id=trip.route_id,
                    bus_id=None,
                    start_min=trip.start_min,
                    end_min=trip.end_min,
                    passenger_demand=trip.passenger_demand,
                    capacity=None,
                    operating_cost=trip.operating_cost,
                    assignment_source="BASELINE",
                    validation_status="UNASSIGNED",
                    utility=trip.utility or 0.0,
                    selection_reason="All eligible buses have conflicting overlapping trip assignments.",
                )
            )

    # Handle remaining trips not in sorted_trips (no eligible bus or utility <= 0)
    for trip in trips:
        if trip.trip_id in assigned_trip_ids or any(
            item.trip_id == trip.trip_id for item in result_items
        ):
            continue
        assert trip.end_min is not None

        reason = ""
        if not trip.eligible_buses:
            reason = "No bus with sufficient capacity or availability."
        elif (trip.utility or 0.0) <= 0.0:
            reason = f"Utility is non-positive ({trip.utility:.4f} <= 0). Operating cost exceeds weighted service reward."

        result_items.append(
            AssignmentItem(
                trip_id=trip.trip_id,
                route_id=trip.route_id,
                bus_id=None,
                start_min=trip.start_min,
                end_min=trip.end_min,
                passenger_demand=trip.passenger_demand,
                capacity=None,
                operating_cost=trip.operating_cost,
                assignment_source="BASELINE",
                validation_status="UNASSIGNED",
                utility=trip.utility or 0.0,
                selection_reason=reason,
            )
        )

    # Sort result items by trip_id for clear display
    result_items.sort(key=lambda item: item.trip_id)

    runtime_seconds = time.perf_counter() - start_time
    return result_items, runtime_seconds

