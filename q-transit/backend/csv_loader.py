import csv
import io
from typing import Tuple, List, Optional
from schemas import TripRecord, BusRecord, ValidationIssue, DataValidationResult


TRIP_REQUIRED_COLUMNS = [
    "trip_id",
    "route_id",
    "start_min",
    "duration_min",
    "passenger_demand",
    "priority",
    "operating_cost",
]

BUS_REQUIRED_COLUMNS = [
    "bus_id",
    "capacity",
    "available_from_min",
    "available_to_min",
]


def load_and_validate_csvs(
    trips_content: str, buses_content: str
) -> DataValidationResult:
    issues: List[ValidationIssue] = []
    parsed_trips: List[TripRecord] = []
    parsed_buses: List[BusRecord] = []

    # 1. Parse trips CSV
    if not trips_content or not trips_content.strip():
        issues.append(
            ValidationIssue(
                file="trips.csv",
                level="ERROR",
                reason="File is empty or contains only whitespace.",
            )
        )
    else:
        try:
            reader = csv.DictReader(io.StringIO(trips_content.strip()))
            if not reader.fieldnames:
                issues.append(
                    ValidationIssue(
                        file="trips.csv",
                        level="ERROR",
                        reason="CSV header missing or unreadable.",
                    )
                )
            else:
                cleaned_headers = [h.strip() for h in reader.fieldnames if h]
                missing_cols = [
                    col for col in TRIP_REQUIRED_COLUMNS if col not in cleaned_headers
                ]
                if missing_cols:
                    issues.append(
                        ValidationIssue(
                            file="trips.csv",
                            column=", ".join(missing_cols),
                            level="ERROR",
                            reason=f"Missing required column(s): {', '.join(missing_cols)}",
                        )
                    )
                else:
                    seen_trip_ids = set()
                    row_idx = 1  # 1-based data row (row 1 after header)
                    for raw_row in reader:
                        row_idx += 1
                        row = {
                            k.strip(): (v.strip() if v is not None else "")
                            for k, v in raw_row.items()
                            if k
                        }
                        trip_id = row.get("trip_id", "")
                        route_id = row.get("route_id", "")

                        if not trip_id:
                            issues.append(
                                ValidationIssue(
                                    file="trips.csv",
                                    row=row_idx,
                                    column="trip_id",
                                    level="ERROR",
                                    reason="Blank or missing trip_id.",
                                )
                            )
                            continue

                        if trip_id in seen_trip_ids:
                            issues.append(
                                ValidationIssue(
                                    file="trips.csv",
                                    row=row_idx,
                                    column="trip_id",
                                    level="ERROR",
                                    reason=f"Duplicate trip_id '{trip_id}'.",
                                )
                            )
                        seen_trip_ids.add(trip_id)

                        if not route_id:
                            issues.append(
                                ValidationIssue(
                                    file="trips.csv",
                                    row=row_idx,
                                    column="route_id",
                                    level="ERROR",
                                    reason="Blank or missing route_id.",
                                )
                            )

                        # Numeric validation
                        row_has_error = False

                        def parse_int(
                            col_name: str, min_val: int, can_equal_min: bool = True
                        ) -> Optional[int]:
                            val_str = row.get(col_name, "")
                            try:
                                val = int(float(val_str))
                                if can_equal_min and val < min_val:
                                    issues.append(
                                        ValidationIssue(
                                            file="trips.csv",
                                            row=row_idx,
                                            column=col_name,
                                            level="ERROR",
                                            reason=f"{col_name} must be >= {min_val}, got {val}.",
                                        )
                                    )
                                    return None
                                elif not can_equal_min and val <= min_val:
                                    issues.append(
                                        ValidationIssue(
                                            file="trips.csv",
                                            row=row_idx,
                                            column=col_name,
                                            level="ERROR",
                                            reason=f"{col_name} must be > {min_val}, got {val}.",
                                        )
                                    )
                                    return None
                                return val
                            except (ValueError, TypeError):
                                issues.append(
                                    ValidationIssue(
                                        file="trips.csv",
                                        row=row_idx,
                                        column=col_name,
                                        level="ERROR",
                                        reason=f"Invalid integer value '{val_str}' for {col_name}.",
                                    )
                                )
                                return None

                        def parse_float(
                            col_name: str, min_val: float
                        ) -> Optional[float]:
                            val_str = row.get(col_name, "")
                            try:
                                val = float(val_str)
                                if val < min_val:
                                    issues.append(
                                        ValidationIssue(
                                            file="trips.csv",
                                            row=row_idx,
                                            column=col_name,
                                            level="ERROR",
                                            reason=f"{col_name} must be >= {min_val}, got {val}.",
                                        )
                                    )
                                    return None
                                return val
                            except (ValueError, TypeError):
                                issues.append(
                                    ValidationIssue(
                                        file="trips.csv",
                                        row=row_idx,
                                        column=col_name,
                                        level="ERROR",
                                        reason=f"Invalid numeric value '{val_str}' for {col_name}.",
                                    )
                                )
                                return None

                        start_min = parse_int("start_min", 0, True)
                        duration_min = parse_int("duration_min", 0, False)
                        demand = parse_int("passenger_demand", 0, True)
                        priority = parse_float("priority", 0.0)
                        cost = parse_float("operating_cost", 0.0)

                        if None in (
                            start_min,
                            duration_min,
                            demand,
                            priority,
                            cost,
                        ) or not route_id:
                            row_has_error = True

                        if start_min is not None and duration_min is not None:
                            end_min = start_min + duration_min
                            if end_min > 1440:
                                issues.append(
                                    ValidationIssue(
                                        file="trips.csv",
                                        row=row_idx,
                                        column="duration_min",
                                        level="ERROR",
                                        reason=f"Trip ends at minute {end_min} (> 1440). Overnight schedules not supported in v1.",
                                    )
                                )
                                row_has_error = True

                        if not row_has_error:
                            parsed_trips.append(
                                TripRecord(
                                    trip_id=trip_id,
                                    route_id=route_id,
                                    start_min=start_min,  # type: ignore
                                    duration_min=duration_min,  # type: ignore
                                    passenger_demand=demand,  # type: ignore
                                    priority=priority,  # type: ignore
                                    operating_cost=cost,  # type: ignore
                                    end_min=start_min + duration_min,  # type: ignore
                                )
                            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    file="trips.csv",
                    level="ERROR",
                    reason=f"CSV parsing exception: {str(e)}",
                )
            )

    # 2. Parse buses CSV
    if not buses_content or not buses_content.strip():
        issues.append(
            ValidationIssue(
                file="buses.csv",
                level="ERROR",
                reason="File is empty or contains only whitespace.",
            )
        )
    else:
        try:
            reader = csv.DictReader(io.StringIO(buses_content.strip()))
            if not reader.fieldnames:
                issues.append(
                    ValidationIssue(
                        file="buses.csv",
                        level="ERROR",
                        reason="CSV header missing or unreadable.",
                    )
                )
            else:
                cleaned_headers = [h.strip() for h in reader.fieldnames if h]
                missing_cols = [
                    col for col in BUS_REQUIRED_COLUMNS if col not in cleaned_headers
                ]
                if missing_cols:
                    issues.append(
                        ValidationIssue(
                            file="buses.csv",
                            column=", ".join(missing_cols),
                            level="ERROR",
                            reason=f"Missing required column(s): {', '.join(missing_cols)}",
                        )
                    )
                else:
                    seen_bus_ids = set()
                    row_idx = 1
                    for raw_row in reader:
                        row_idx += 1
                        row = {
                            k.strip(): (v.strip() if v is not None else "")
                            for k, v in raw_row.items()
                            if k
                        }
                        bus_id = row.get("bus_id", "")

                        if not bus_id:
                            issues.append(
                                ValidationIssue(
                                    file="buses.csv",
                                    row=row_idx,
                                    column="bus_id",
                                    level="ERROR",
                                    reason="Blank or missing bus_id.",
                                )
                            )
                            continue

                        if bus_id in seen_bus_ids:
                            issues.append(
                                ValidationIssue(
                                    file="buses.csv",
                                    row=row_idx,
                                    column="bus_id",
                                    level="ERROR",
                                    reason=f"Duplicate bus_id '{bus_id}'.",
                                )
                            )
                        seen_bus_ids.add(bus_id)

                        row_has_error = False

                        def parse_bus_int(
                            col_name: str, min_val: int, can_equal_min: bool = True
                        ) -> Optional[int]:
                            val_str = row.get(col_name, "")
                            try:
                                val = int(float(val_str))
                                if can_equal_min and val < min_val:
                                    issues.append(
                                        ValidationIssue(
                                            file="buses.csv",
                                            row=row_idx,
                                            column=col_name,
                                            level="ERROR",
                                            reason=f"{col_name} must be >= {min_val}, got {val}.",
                                        )
                                    )
                                    return None
                                elif not can_equal_min and val <= min_val:
                                    issues.append(
                                        ValidationIssue(
                                            file="buses.csv",
                                            row=row_idx,
                                            column=col_name,
                                            level="ERROR",
                                            reason=f"{col_name} must be > {min_val}, got {val}.",
                                        )
                                    )
                                    return None
                                return val
                            except (ValueError, TypeError):
                                issues.append(
                                    ValidationIssue(
                                        file="buses.csv",
                                        row=row_idx,
                                        column=col_name,
                                        level="ERROR",
                                        reason=f"Invalid integer value '{val_str}' for {col_name}.",
                                    )
                                )
                                return None

                        cap = parse_bus_int("capacity", 0, False)
                        from_min = parse_bus_int("available_from_min", 0, True)
                        to_min = parse_bus_int("available_to_min", 0, False)

                        if None in (cap, from_min, to_min):
                            row_has_error = True
                        else:
                            if from_min >= to_min:  # type: ignore
                                issues.append(
                                    ValidationIssue(
                                        file="buses.csv",
                                        row=row_idx,
                                        column="available_to_min",
                                        level="ERROR",
                                        reason=f"available_to_min ({to_min}) must be strictly greater than available_from_min ({from_min}).",
                                    )
                                )
                                row_has_error = True

                        if not row_has_error:
                            total_avail = to_min - from_min  # type: ignore
                            parsed_buses.append(
                                BusRecord(
                                    bus_id=bus_id,
                                    capacity=cap,  # type: ignore
                                    available_from_min=from_min,  # type: ignore
                                    available_to_min=to_min,  # type: ignore
                                    total_available_minutes=total_avail,
                                )
                            )
        except Exception as e:
            issues.append(
                ValidationIssue(
                    file="buses.csv",
                    level="ERROR",
                    reason=f"CSV parsing exception: {str(e)}",
                )
            )

    has_errors = any(i.level == "ERROR" for i in issues)
    is_valid = not has_errors and len(parsed_trips) > 0 and len(parsed_buses) > 0

    if not has_errors and (len(parsed_trips) == 0 or len(parsed_buses) == 0):
        issues.append(
            ValidationIssue(
                file="input",
                level="ERROR",
                reason="Must have at least one valid trip and one valid bus.",
            )
        )
        is_valid = False

    return DataValidationResult(
        is_valid=is_valid,
        trips_received=len(parsed_trips),
        buses_received=len(parsed_buses),
        valid_trips_count=len(parsed_trips) if is_valid else 0,
        unassignable_trips=[],
        issues=issues,
        trips=parsed_trips if is_valid else [],
        buses=parsed_buses if is_valid else [],
        eligible_assignments_count=0,
    )

