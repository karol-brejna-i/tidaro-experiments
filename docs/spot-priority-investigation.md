# Spot Priority Investigation

**Date**: 2026-02-14  
**Symptom**: Spot 06 is sometimes booked even though 07 (higher priority) appears to be free.  
**Config**: `SPOT_NAMES=07,06` — meaning "prefer 07, fall back to 06."

## Code Analysis

### Booking Flow (traced end-to-end)

1. **CLI** (`tictl.py` → `book_free` command) builds payload with `spot_name: ["07", "06"]` from config
2. **`BookFreeSpots.do()`** fetches all upcoming days with free spots, filters out weekends / already-booked / no-free-spots days, then for each remaining day calls `BookSpot.do_for_payload()`
3. **`BookSpot.do_for_payload()`**:
   - Calls `get_spots_state(zone_id, date)` to get live free/taken status from API
   - Calls `_expand_spot_selection()` to filter to only free spots, **preserving preference order**
   - Iterates the result calling `take_spot()` — stops at first success

### Verdict: Preference order is correctly preserved in the code

No sorting or shuffling occurs. The list `["07", "06"]` flows through unchanged — 07 is always attempted first, 06 only if 07 is unavailable or if the booking attempt for 07 fails.

## Identified Issues

### 1. Silent skip on unexpected API response (MOST LIKELY CAUSE)

In `BookSpot.do_for_payload()`, the old code had:

```python
response = self.session.take_spot(zone_id, spot_id, p['for_date'])
if 'status' in response:          # if False → silent skip!
    if response['status'] == 'Reserved':
        ...
        break
    else:
        failures.append(...)
# ← no logging, no failure recorded, just moves to next spot
```

If the Tidaro API returns a response **without a `status` key** (network glitch, unexpected format, rate limiting), the code **silently skips spot 07** and proceeds to book 06. No failure is logged, no exception raised.

### 2. API may assign a different spot than requested

The API field is `parkingSpotIdOrNull` — the "or null" suggests Tidaro may treat it as a *preference*, not a strict requirement. The code reads the *actual* reserved spot from `response['receivedParkingSpotOrNull']['name']`, which could differ from what was requested. No validation was in place.

### 3. Race condition between state check and booking

`get_spots_state()` sees 07 as free, but by the time `take_spot()` executes, another user might have grabbed it. The API returns something other than `'Reserved'`, so the loop moves on to 06. This is normal but was invisible due to lack of logging.

### 4. Stale Docker image

The Docker image is built at `docker build` time and does not mount source code. If the image hasn't been rebuilt recently, it may contain older code.

## Changes Applied

### Enhanced logging in `book_spot.py`

- **`_expand_spot_selection()`**: Now logs preferences, available spots, taken spots, and final selection order
- **`do_for_payload()`**: Logs each attempt by name+ID, full API response (DEBUG), outcome
- **New WARNING** when API response has no `status` key (was a silent skip)
- **New WARNING** when API reserves a different spot than requested (mismatch detection)
- **Exception logging** now includes `exc_info=True` for full tracebacks

### Weekend inclusion setting

Added `INCLUDE_WEEKENDS` env var (default: `false`) to allow booking on weekends for testing purposes, since weekend spots are more reliably free.

## Validation Plan

| Step | Action | Purpose |
|------|--------|---------|
| **1** | Rebuild Docker image: `docker build -t tidarator:latest .` | Deploy latest code with new logging |
| **2** | Set `INCLUDE_WEEKENDS=true` in `.env` | Enable weekend testing where both 07 and 06 are likely free |
| **3** | Run `show-spots -d <weekend-date>` | Verify API sees both 07 and 06 as free |
| **4** | Cross-check on tidaro.com UI | Confirm spot states match |
| **5** | Run `book-free -f <weekend-date>` | Trigger booking and collect logs |
| **6** | Inspect `application.log` | New logs will show exactly: which spot was attempted, API response, mismatch if any |
| **7** | If 06 was booked, check log for WARNING about 07 | Root cause will be visible (missing `status`, race condition, or API reassignment) |
| **8** | Release the weekend spot after testing | Clean up test bookings |

### Running from IDE (alternative to Docker)

```bash
cd /path/to/tidaro-experiments
pip install -e .
export $(grep -v '^#' .env | xargs)
export INCLUDE_WEEKENDS=true
tidarator show-spots -d 2026-02-15
tidarator book-free -f 2026-02-15
```

This guarantees the exact repo code is running.

## Expected Outcomes

After the next occurrence (or a deliberate weekend test), the logs will show one of:

1. **Missing `status` key** → API returning unexpected response for spot 07 (now logged as WARNING)
2. **Race condition** → 07 was already taken between state check and booking (now logged with status detail)
3. **API reassignment** → asked for 07, got 06 (now logged as MISMATCH WARNING)
4. **07 was actually taken** → correctly fell back to 06 (now clearly logged)
