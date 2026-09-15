import pandas as pd

BOOKING_WINDOW_DAYS = {"T+1": 1, "T+7": 7, "T+15": 15, "T+30": 30, "T+45": 45}
ALLOWED_STATUSES = {"observed", "sold_out", "scrape_failed", "parse_error"} # scrape statuses 
PRICE_COMPONENTS = ["base_fare", "fuel_surcharge", "taxes_fees", "gst_amount", "convenience_fee"]

class QualityIssue:
    def __init__(self, row_key, flag_type, reason):
        self.row_key = row_key
        self.flag_type = flag_type
        self.reason = reason

# Summarize the dataset shape, columns, missing values, and status distribution.
def profile_data(frame: pd.DataFrame) -> dict:
    """Return concise raw-data profiling metrics."""
    profile = {
        "row_count": len(frame),
        "columns": list(frame.columns),
        "missing_values": frame.isna().sum().to_dict(),
        "unique_values": frame.nunique(dropna=True).to_dict(),
    }

    if "scrape_status" in frame.columns:
        profile["scrape_status_counts"] = frame["scrape_status"].value_counts(dropna=False).to_dict()
    else:
        profile["scrape_status_counts"] = {}

    return profile


# Create a standard quality issue record.
def _issue(row, flag_type, reason):
    return QualityIssue(row.get("observation_id", row.name), flag_type, reason)


# Convert raw input fields to analytical types and flag invalid values.
def validate_types(frame: pd.DataFrame):
    """Coerce analytical types and flag input values that cannot be converted."""
    result = frame.copy()
    issues = []
    integer_columns = ["route_id", "source_id", "stops", "lead_time_days"]

    for column in integer_columns:
        if column not in result.columns:
            continue 
        original = result[column] 
        result[column] = pd.to_numeric(original, errors="coerce").astype("Int64") # errors='coerce' converts invalid parsing like alphabets or anything other than a number to Nan 
        invalid_rows = result[original.notna() & result[column].isna()]  # this takes the rows where originally special characters were present in place of numbers and also selects the rows where the special characters became Nan from the result of the previous line. 
        for _, row in invalid_rows.iterrows():
            issues.append(_issue(row, "confirmed_error", f"{column} is not an integer"))

    price_columns = ["raw_price_displayed", *PRICE_COMPONENTS]
    for column in price_columns:
        if column not in result.columns:
            continue
        original = result[column]
        result[column] = pd.to_numeric(original, errors="coerce")
        invalid_rows = result[original.notna() & result[column].isna()]
        for _, row in invalid_rows.iterrows():
            issues.append(_issue(row, "confirmed_error", f"{column} is not numeric"))

    if "flight_number" in result.columns:
        invalid_fn = (
            result["flight_number"].isna()
            | (result["flight_number"].astype(str).str.strip() == "")
            | (result["flight_number"].astype(str).str.strip().str.lower().isin(["nan", "none", "<na>"]))
        )
        for _, row in result[invalid_fn].iterrows():
            issues.append(_issue(row, "confirmed_error", "flight_number is missing or invalid"))

    for column in ["scrape_timestamp", "created_at"]:
        if column in result.columns:
            result[column] = pd.to_datetime(result[column], errors="coerce", utc=True)

    if "departure_date" in result.columns:
        result["departure_date"] = pd.to_datetime(result["departure_date"], errors="coerce").dt.date

    if "departure_time" in result.columns:
        original = result["departure_time"]
        result["departure_time"] = pd.to_datetime(original, format="%H:%M:%S", errors="coerce").dt.time
        invalid_rows = result[original.notna() & result["departure_time"].isna()]
        for _, row in invalid_rows.iterrows():
            issues.append(_issue(row, "confirmed_error", "departure_time is invalid"))

    return result, issues


# Standardize text fields and selected categorical values.
def normalize_categories(frame: pd.DataFrame) -> pd.DataFrame:
    """Trim and case-normalize only categories whose meaning is unchanged."""
    result = frame.copy()
    text_columns = ["airline_name", "cabin_class", "fare_family", "scrape_status", "data_provenance"]

    for column in text_columns:
        if column in result.columns:
            result[column] = result[column].astype("string").str.strip().str.lower()

    if "airline_name" in result.columns:
        from .cleaned_table import AIRLINE_CODE_MAP

        canonical_by_key = {
            "".join(name.casefold().split()): name
            for name in AIRLINE_CODE_MAP
        }
        airline_keys = result["airline_name"].str.replace(r"\s+", "", regex=True)
        result["airline_name"] = airline_keys.map(canonical_by_key).fillna(result["airline_name"])

    if "currency" in result.columns:
        result["currency"] = result["currency"].astype("string").str.strip().replace({"₹": "INR"}).str.upper()

    if "advance_booking_window" in result.columns:
        result["advance_booking_window"] = result["advance_booking_window"].astype("string").str.strip().str.upper()

    return result


# Verify that currency is valid and supported for domestic index calculation.
def validate_currency(frame: pd.DataFrame):
    issues = []
    if "currency" not in frame.columns:
        return issues
    for _, row in frame.iterrows():
        curr = row.get("currency")
        if pd.isna(curr) or str(curr).strip() == "":
            issues.append(_issue(row, "confirmed_error", "currency is missing"))
        elif str(curr).strip().upper() != "INR":
            issues.append(_issue(row, "confirmed_error", f"unsupported currency {curr} (only INR is supported)"))
    return issues


# Check whether important timestamps are present and valid.
def validate_timestamps(frame: pd.DataFrame):
    issues = []
    for _, row in frame.iterrows():
        if pd.isna(row.get("scrape_timestamp")): # this checks if the scrape_timestamp is Nan or not. If it is Nan then it will append the issue to the issues list.
            issues.append(_issue(row, "confirmed_error", "scrape_timestamp is missing or invalid"))
        if pd.isna(row.get("departure_date")):
            issues.append(_issue(row, "confirmed_error", "departure_date is missing or invalid"))
    return issues


# Recompute lead time in Indian Standard Time.
def recalculate_lead_time(frame: pd.DataFrame):
    result = frame.copy()
    issues = []
    scrape_dates = result["scrape_timestamp"].dt.tz_convert("Asia/Kolkata").dt.date
    departure_dates = pd.to_datetime(result["departure_date"], errors="coerce").dt.date
    result["calculated_lead_time_days"] = (pd.to_datetime(departure_dates) - pd.to_datetime(scrape_dates)).dt.days.astype("Int64")

    mismatches = (
        result["lead_time_days"].notna()
        & result["calculated_lead_time_days"].notna()
        & (result["lead_time_days"] != result["calculated_lead_time_days"])
    )

    for _, row in result[mismatches].iterrows():
        reason = f"raw lead time {row['lead_time_days']} differs from IST-calculated {row['calculated_lead_time_days']}"
        issues.append(_issue(row, "confirmed_error", reason))

    return result, issues


# Verify that each booking window matches the expected number of lead days.
def validate_booking_window(frame: pd.DataFrame):
    issues = []
    for _, row in frame.iterrows():
        window = row.get("advance_booking_window")
        if pd.isna(window) or window == "other":
            continue

        expected = BOOKING_WINDOW_DAYS.get(window)
        if expected is None:
            issues.append(_issue(row, "confirmed_error", f"unsupported booking window {window}"))
        elif pd.isna(row.get("calculated_lead_time_days")):
            issues.append(_issue(row, "confirmed_error", "booking window cannot be checked without a valid calculated lead time"))
        elif row.get("calculated_lead_time_days") != expected:
            actual = row.get("calculated_lead_time_days")
            reason = f"booking window {window} does not match IST-calculated lead time {actual}"
            issues.append(_issue(row, "confirmed_error", reason))
    return issues


# Compare displayed fares with their component totals and validate index readiness.
def validate_prices(frame: pd.DataFrame, tolerance: float = 1.0):
    issues = []
    for _, row in frame.iterrows():
        is_observed = row.get("scrape_status") == "observed"
        displayed = row.get("raw_price_displayed")
        base = row.get("base_fare")

        if is_observed:
            if pd.isna(displayed):
                issues.append(_issue(row, "confirmed_error", "observed record has no displayed price"))
            elif displayed <= 0:
                issues.append(_issue(row, "confirmed_error", "displayed price must be greater than zero"))

            if pd.isna(base):
                issues.append(_issue(row, "confirmed_error", "observed record has no base fare"))
            elif base <= 0:
                issues.append(_issue(row, "confirmed_error", "base fare must be greater than zero"))
            elif pd.notna(displayed) and base > (displayed + tolerance):
                issues.append(_issue(row, "confirmed_error", "base fare cannot exceed displayed price"))

        available = [value for component in PRICE_COMPONENTS if pd.notna(value := row.get(component))]

        if pd.notna(displayed) and len(available) == len(PRICE_COMPONENTS):
            component_total = sum(available)
            if abs(displayed - component_total) > tolerance:
                issues.append(_issue(row, "confirmed_error", "displayed price differs from complete fare-component total"))
    return issues


# Detect repeated observations that share the same identity keys.
def detect_duplicates(frame: pd.DataFrame):
    keys = ["route_id", "source_id", "flight_number", "departure_date", "scrape_timestamp"]
    duplicates = frame.duplicated(keys, keep=False)
    issues = [_issue(row, "duplicate_suspected", "duplicate observation identity") for _, row in frame[duplicates].iterrows()]
    return issues

# Flag fares outside the expected range for route, booking window, and cabin based on IQR method.
def detect_outliers(frame: pd.DataFrame):
    issues = []
    eligible = frame[(frame["scrape_status"] == "observed") & frame["raw_price_displayed"].notna()]

    for _, group in eligible.groupby(["route_id", "advance_booking_window", "cabin_class"], dropna=False):
        if len(group) < 4: # for a comparable iqr outlier detection atleast 4 obs are needed. 
            continue

        quartiles = group["raw_price_displayed"].quantile([0.25, 0.75])
        q1, q3 = quartiles[0.25], quartiles[0.75]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        for _, row in group.iterrows():
            price = row["raw_price_displayed"]
            if price < lower_bound:
                issues.append(_issue(row, "outlier_low", "fare is below the group IQR bound"))
            elif price > upper_bound:
                issues.append(_issue(row, "outlier_high", "fare is above the group IQR bound"))

    return issues


# Identify fare values that deviate materially from comparable sources.
def detect_cross_source_mismatches(frame: pd.DataFrame, relative_threshold: float = 0.35):
    keys = ["route_id", "flight_number", "departure_date", "advance_booking_window", "cabin_class"]
    issues = []
    eligible = frame[(frame["scrape_status"] == "observed") & frame["raw_price_displayed"].notna()]

    for _, group in eligible.groupby(keys, dropna=False):
        if group["source_id"].nunique() < 2:
            continue

        median = group["raw_price_displayed"].median()
        if median <= 0:
            continue

        for _, row in group.iterrows():
            relative_difference = abs(row["raw_price_displayed"] - median) / median
            if relative_difference > relative_threshold:
                issues.append(_issue(row, "cross_source_mismatch", "fare differs materially from comparable-source median"))
    return issues 


# Convert all detected issues into a reviewable DataFrame.
def generate_quality_flags(issue_groups) -> pd.DataFrame:
    issues = [issue for group in issue_groups for issue in group]
    flag_rows = [{
        "row_key": issue.row_key,
        "flag_type": issue.flag_type,
        "detected_by": "rule_based",
        "flag_reason": issue.reason,
        "reviewed_status": "pending",
    } for issue in issues]
    flags = pd.DataFrame(flag_rows)
    return flags.drop_duplicates() if not flags.empty else flags


# Return only observations that are valid sellable fares, excluding bad data, duplicates, and outliers.
def build_cleaned_observations(
    frame: pd.DataFrame,
    quality_flags: pd.DataFrame | None = None,
    excluded_flag_types: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Return eligible observed fares, excluding confirmed errors and duplicates."""
    eligible = frame[(frame["scrape_status"] == "observed") & frame["raw_price_displayed"].notna()].copy()
    if "base_fare" in eligible.columns:
        eligible = eligible[eligible["base_fare"].notna() & (eligible["base_fare"] > 0)]

    if quality_flags is not None and not quality_flags.empty:
        if excluded_flag_types is None:
            excluded_flag_types = ("confirmed_error", "duplicate_suspected")
        flagged_keys = quality_flags.loc[
            quality_flags["flag_type"].isin(excluded_flag_types), "row_key"
        ]
        excluded_keys_str = {str(k) for k in flagged_keys}
        if "observation_id" in eligible.columns:
            eligible = eligible[~eligible["observation_id"].astype(str).isin(excluded_keys_str)]
        else:
            eligible = eligible[~eligible.index.astype(str).isin(excluded_keys_str)]

    return eligible
