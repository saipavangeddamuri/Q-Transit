from typing import List, Tuple
from schemas import TripRecord, BusRecord, DataValidationResult, ValidationIssue


def preprocess_data(
    data: DataValidationResult, cost_weight: float = 0.20
) -> DataValidationResult:
    if not data.is_valid:
        return data

    trips = data.trips
    buses = data.buses

    # 1. Calculate service value
    for t in trips:
        t.end_min = t.start_min + t.duration_min
        t.service_value = float(t.passenger_demand * t.priority)

    # 2. Normalization values
    max_service = max((t.service_value for t in trips), default=0.0)
    max_cost = max((t.operating_cost for t in trips), default=0.0)

    data.max_service_value = max_service
    data.max_operating_cost = max_cost

    # 3. Compute normalized values and trip utility
    for t in trips:
        norm_srv = (
            (t.service_value / max_service)
            if max_service > 0 and t.service_value is not None
            else 0.0
        )
        norm_cst = (
            (t.operating_cost / max_cost)
            if max_cost > 0 and t.operating_cost is not None
            else 0.0
        )
        t.normalized_service = norm_srv
        t.normalized_cost = norm_cst
        t.utility = (1.0 - cost_weight) * norm_srv - cost_weight * norm_cst

    # 4. Determine bus eligibility for each trip
    unassignable = []
    total_eligible_assignments = 0

    for t in trips:
        eligible = []
        assert t.end_min is not None
        for b in buses:
            # Capacity check
            fits_capacity = t.passenger_demand <= b.capacity
            # Availability interval check
            fits_availability = (
                t.start_min >= b.available_from_min and t.end_min <= b.available_to_min
            )
            if fits_capacity and fits_availability:
                eligible.append(b.bus_id)

        # Sort eligible buses deterministically
        eligible.sort()
        t.eligible_buses = eligible
        total_eligible_assignments += len(eligible)

        if not eligible:
            unassignable.append(t.trip_id)
            data.issues.append(
                ValidationIssue(
                    file="trips.csv",
                    column="trip_id",
                    level="WARNING",
                    reason=f"Trip '{t.trip_id}' has no eligible bus (exceeds all bus capacities or falls outside availability windows). It will be recorded as unassignable.",
                )
            )

    data.unassignable_trips = unassignable
    data.eligible_assignments_count = total_eligible_assignments
    return data

