from typing import List, Dict, Tuple
from schemas import TripRecord, BusRecord, AssignmentItem


def decode_bitstring(
    bitstring: str,
    var_list: List[Tuple[str, str]],
    trips: List[TripRecord],
    buses: List[BusRecord],
    source: str = "RAW_QAOA",
) -> Tuple[List[AssignmentItem], Dict[str, float]]:
    """
    Decodes bitstring of length len(var_list) to AssignmentItems.
    Returns:
      (items, stats_dict)
    """
    trip_map = {t.trip_id: t for t in trips}
    bus_map = {b.bus_id: b for b in buses}

    # Group assignments by trip_id: trip_id -> list of assigned bus_ids
    trip_assignments: Dict[str, List[str]] = {t.trip_id: [] for t in trips}

    for bit_char, (trip_id, bus_id) in zip(bitstring, var_list):
        if bit_char == "1":
            trip_assignments[trip_id].append(bus_id)

    items: List[AssignmentItem] = []
    served_trips = set()
    total_demand = 0
    total_cost = 0.0
    total_service = 0.0
    total_utility = 0.0

    for trip in sorted(trips, key=lambda x: x.trip_id):
        assigned_buses = trip_assignments[trip.trip_id]
        assert trip.end_min is not None

        if not assigned_buses:
            items.append(
                AssignmentItem(
                    trip_id=trip.trip_id,
                    route_id=trip.route_id,
                    bus_id=None,
                    start_min=trip.start_min,
                    end_min=trip.end_min,
                    passenger_demand=trip.passenger_demand,
                    capacity=None,
                    operating_cost=trip.operating_cost,
                    assignment_source=source,
                    validation_status="UNASSIGNED",
                    utility=trip.utility or 0.0,
                    selection_reason="Trip assignment bit(s) not activated by solver.",
                )
            )
        else:
            served_trips.add(trip.trip_id)
            total_demand += trip.passenger_demand
            total_cost += trip.operating_cost
            total_service += trip.service_value or 0.0
            total_utility += trip.utility or 0.0

            # If assigned to 1 bus
            if len(assigned_buses) == 1:
                b_id = assigned_buses[0]
                cap = bus_map[b_id].capacity if b_id in bus_map else None
                items.append(
                    AssignmentItem(
                        trip_id=trip.trip_id,
                        route_id=trip.route_id,
                        bus_id=b_id,
                        start_min=trip.start_min,
                        end_min=trip.end_min,
                        passenger_demand=trip.passenger_demand,
                        capacity=cap,
                        operating_cost=trip.operating_cost,
                        assignment_source=source,
                        validation_status="FEASIBLE",  # Candidate status will be checked by independent validator
                        utility=trip.utility or 0.0,
                        selection_reason=f"Assigned to {b_id} by candidate bitstring.",
                    )
                )
            else:
                # Duplicate assignment: create an item per assigned bus so validator can detect duplicate
                for b_id in assigned_buses:
                    cap = bus_map[b_id].capacity if b_id in bus_map else None
                    items.append(
                        AssignmentItem(
                            trip_id=trip.trip_id,
                            route_id=trip.route_id,
                            bus_id=b_id,
                            start_min=trip.start_min,
                            end_min=trip.end_min,
                            passenger_demand=trip.passenger_demand,
                            capacity=cap,
                            operating_cost=trip.operating_cost,
                            assignment_source=source,
                            validation_status="INFEASIBLE",
                            utility=trip.utility or 0.0,
                            selection_reason=f"Candidate assigned trip to multiple buses: {', '.join(assigned_buses)}.",
                        )
                    )

    stats = {
        "trips_served_count": len(served_trips),
        "passenger_demand_served": total_demand,
        "operating_cost": total_cost,
        "service_value": total_service,
        "total_utility": total_utility,
    }
    return items, stats

