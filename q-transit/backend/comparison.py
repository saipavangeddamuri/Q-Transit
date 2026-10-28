from typing import List, Dict, Any, Optional
from schemas import (
    TripRecord,
    BusRecord,
    AssignmentItem,
    ComparisonMetrics,
    ScheduleValidationResult,
)


def compute_metrics(
    schedule: List[AssignmentItem],
    trips: List[TripRecord],
    buses: List[BusRecord],
    validation_res: ScheduleValidationResult,
    runtime_seconds: float,
) -> ComparisonMetrics:
    """
    Computes fair comparison metrics per Section 11.1 and 21.3.
    """
    # Active assignments
    assigned_items = [item for item in schedule if item.bus_id is not None]
    trips_served = len(set(item.trip_id for item in assigned_items))

    demand_served = sum(item.passenger_demand for item in assigned_items)
    cost = sum(item.operating_cost for item in assigned_items)

    trip_map = {t.trip_id: t for t in trips}
    weighted_service = sum(
        (trip_map[item.trip_id].service_value or 0.0)
        for item in assigned_items
        if item.trip_id in trip_map
    )
    total_utility = sum(
        (trip_map[item.trip_id].utility or 0.0)
        for item in assigned_items
        if item.trip_id in trip_map
    )

    # Eligible trips: valid trips with at least one eligible bus
    eligible_trips = [t for t in trips if len(t.eligible_buses) > 0]
    total_eligible_trips_count = len(eligible_trips)
    total_eligible_demand = sum(t.passenger_demand for t in eligible_trips)

    # Coverage rate: eligible-trip selection rate
    if total_eligible_trips_count > 0:
        coverage_rate = f"{(trips_served / total_eligible_trips_count) * 100:.1f}%"
    else:
        coverage_rate = "N/A"

    # Passenger-demand coverage
    if total_eligible_demand > 0:
        demand_coverage = f"{(demand_served / total_eligible_demand) * 100:.1f}%"
    else:
        demand_coverage = "N/A"

    # Fleet utilization: assigned trip minutes / total bus availability minutes
    assigned_trip_minutes = sum(
        (item.end_min - item.start_min) for item in assigned_items
    )
    total_bus_availability_minutes = sum(
        (b.total_available_minutes or (b.available_to_min - b.available_from_min))
        for b in buses
    )

    if total_bus_availability_minutes > 0:
        fleet_utilization = f"{(assigned_trip_minutes / total_bus_availability_minutes) * 100:.1f}%"
    else:
        fleet_utilization = "N/A"

    return ComparisonMetrics(
        trips_served=trips_served,
        passenger_demand_served=demand_served,
        weighted_service_value=round(weighted_service, 2),
        operating_cost=round(cost, 2),
        trip_utility=round(total_utility, 4),
        coverage_rate=coverage_rate,
        passenger_demand_coverage=demand_coverage,
        fleet_utilization=fleet_utilization,
        constraint_violations=validation_res.total_violations,
        runtime_seconds=round(runtime_seconds, 4),
        feasible="Yes" if validation_res.is_feasible else "No",
    )

