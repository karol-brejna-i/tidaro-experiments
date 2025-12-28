# Tidarator Project Improvement Suggestions

This document outlines recommendations for improving usability, functionality, code quality, and project sustainability.

---

## Table of Contents

1. [Usability Improvements](#usability-improvements)
2. [Functional Improvements](#functional-improvements)
3. [Code Quality & Readability](#code-quality--readability)
4. [Project Sustainability](#project-sustainability)

---

## Usability Improvements

### 1. Missing `--version` CLI Option

**Current State:**
The CLI does not provide a `--version` flag to display the current application version.

**Why It's Not Great:**
Users cannot quickly check which version of the tool they are running, making debugging and support harder.

**What Should Be Changed:**
Add a `--version` option to the main CLI group using Click's built-in functionality:
```python
@click.group()
@click.version_option(version="0.1.2", prog_name="tidarator")
@click.pass_context
def cli(ctx):
    ...
```

**Benefits:**
- Standard CLI behavior users expect
- Easier troubleshooting and version tracking
- Version can be pulled dynamically from `importlib.metadata`

---

### 2. Inconsistent Error Output Formatting

**Current State:**
Errors are output using multiple methods: `click.echo()` to stderr, `logger.error()`, and plain `print()` statements scattered throughout the codebase.

**Why It's Not Great:**
- Inconsistent user experience
- Hard to distinguish between operational messages and errors
- `print()` statements in `log_config.py` bypass the logging system

**What Should Be Changed:**
- Standardize all user-facing errors through `click.echo(..., err=True)` with consistent formatting
- Remove all raw `print()` statements; use the logging system instead
- Consider using `click.style()` for colored error output

**Benefits:**
- Consistent error presentation
- Better separation between stdout (results) and stderr (errors)
- Professional CLI appearance

---

### 3. Silent Failures When Zone/Spot Not Found

**Current State:**
```python
zone = self.zone_manager.get_by_name(p['zone_name'])
zone_id = zone.get('id') if zone else None
```
If a zone is not found, `zone_id` becomes `None`, and the code proceeds with potentially undefined behavior.

**Why It's Not Great:**
Users get cryptic errors or unexpected behavior when they misconfigure zone/spot names.

**What Should Be Changed:**
- Validate zone and spot names early
- Provide clear error messages like: `Error: Zone 'XYZ' not found. Available zones: A, B, C`
- Add a `list-zones` command to help users discover valid zone names

**Benefits:**
- Better user guidance
- Faster troubleshooting
- Self-documenting CLI

---

### 4. Date Validation & User-Friendly Messages

**Current State:**
Dates are validated by Click's `DateTime` type, but there's no validation for logical constraints (e.g., booking past dates).

**Why It's Not Great:**
Users can attempt to book spots for dates in the past, only to receive confusing API errors.

**What Should Be Changed:**
Add validation callbacks for date options:
```python
def validate_future_date(ctx, param, value):
    if value.date() < datetime.today().date():
        raise click.BadParameter("Cannot book spots for past dates")
    return value
```

**Benefits:**
- Immediate, clear feedback
- Prevent wasted API calls
- Better user experience

---

### 5. Output Format Options (JSON/Table/Plain)

**Current State:**
Results are always formatted as plain text via `format_results()`.

**Why It's Not Great:**
- Not suitable for scripting/automation
- No structured output for programmatic consumption

**What Should Be Changed:**
Add `--output` / `-o` option with choices: `plain`, `json`, `table`:
```python
@click.option('-o', '--output', type=click.Choice(['plain', 'json', 'table']), default='plain')
```

**Benefits:**
- Better integration with scripts and automation tools
- Machine-readable output for CI/CD pipelines
- Flexibility for different use cases

---

## Functional Improvements

### 6. No `--dry-run` Mode

**Current State:**
All commands immediately execute actions against the API.

**Why It's Not Great:**
Users cannot preview what actions would be taken without actually performing them.

**What Should Be Changed:**
Add a `--dry-run` flag that shows what would happen without making API calls:
```
$ tidarator book-free --dry-run
Would book the following spots:
  - 2025-01-06: spot 25
  - 2025-01-07: spot 08
```

**Benefits:**
- Safer operation
- Useful for testing configurations
- Better understanding of tool behavior

---

### 7. Missing Confirmation for Destructive Actions

**Current State:**
`release-spot` immediately releases a spot without confirmation.

**Why It's Not Great:**
Accidental command execution could release an important booking.

**What Should Be Changed:**
Add confirmation prompt (with `--yes`/`-y` flag to bypass):
```python
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
def release_spot(ctx, date, yes):
    if not yes:
        click.confirm(f'Release spot for {date}?', abort=True)
```

**Benefits:**
- Protection against accidental data loss
- Standard CLI safety pattern
- Still scriptable with `--yes` flag

---

### 8. Hardcoded Wheel Version in Dockerfile

**Current State:**
```dockerfile
RUN pip install --no-cache-dir /dist/tidarator-0.1.2-py3-none-any.whl
```

**Why It's Not Great:**
Every version bump requires manual Dockerfile update; easy to forget.

**What Should Be Changed:**
Use wildcard or dynamic version:
```dockerfile
RUN pip install --no-cache-dir /dist/tidarator-*.whl
```

**Benefits:**
- Dockerfile stays version-agnostic
- Reduces maintenance burden
- Eliminates version mismatch bugs

---

### 9. No Retry Logic for API Calls

**Current State:**
API calls fail immediately on network errors without retry attempts.

**Why It's Not Great:**
Transient network issues cause failures that could be automatically recovered.

**What Should Be Changed:**
Implement retry logic with exponential backoff using `tenacity` or `urllib3.util.retry`:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def _post(self, url, payload=None):
    ...
```

**Benefits:**
- More resilient to network issues
- Better suited for automated/scheduled runs
- Reduces manual intervention needs

---

### 10. Session Secrets Stored with Pickle (Security Risk)

**Current State:**
Session tokens are stored using `pickle.dump()` in a plain file.

**Why It's Not Great:**
- Pickle files are a known security risk (arbitrary code execution)
- Tokens stored in plain text
- No encryption or access control

**What Should Be Changed:**
- Use JSON for token storage (safer, human-readable)
- Consider encrypting tokens at rest
- Set restrictive file permissions (0600)
- Add token expiration handling

**Benefits:**
- Improved security posture
- Reduced attack surface
- Better credential management

---

### 11. No Test Suite

**Current State:**
The `tests/` directory is empty.

**Why It's Not Great:**
- No automated verification of functionality
- Refactoring is risky
- Regression bugs go undetected

**What Should Be Changed:**
- Add unit tests for core logic (spot selection, date handling, config parsing)
- Add integration tests with mocked API responses
- Set up pytest with fixtures
- Consider adding test coverage requirements

**Benefits:**
- Confidence in code changes
- Documentation through tests
- Easier onboarding for contributors

---

## Code Quality & Readability

### 12. Unused Import in `tictl.py`

**Current State:**
```python
from calendar import c  # Line 1
```

**Why It's Not Great:**
Unused imports clutter the code and can cause confusion.

**What Should Be Changed:**
Remove the unused import.

**Benefits:**
- Cleaner code
- Faster imports
- No misleading dependencies

---

### 13. Inconsistent Logging vs `logging` Module

**Current State:**
The codebase mixes `logger.info()` (custom logger) and `logging.info()` (module-level):
```python
# In tictl.py
logging.info("run_book_spot")  # Module-level
logger.info(...)               # Instance logger
```

**Why It's Not Great:**
- Inconsistent log output formatting
- Some logs may not use configured handlers
- Confusing for maintainers

**What Should Be Changed:**
Always use the custom `get_logger(__name__)` pattern throughout:
```python
logger = get_logger(__name__)
logger.info("run_book_spot")
```

**Benefits:**
- Consistent logging behavior
- All logs go through configured handlers
- Proper log hierarchy

---

### 14. Dead Code: `_construct_request_payload()` Methods

**Current State:**
Multiple classes have `_construct_request_payload()` methods marked with `# TODO XXX looks like this is not used....`

**Why It's Not Great:**
- Dead code increases cognitive load
- Unclear if it should be used or removed
- Maintenance burden

**What Should Be Changed:**
Either:
- Remove the dead code if truly unused, or
- Implement and use it to follow the template method pattern properly

**Benefits:**
- Cleaner codebase
- Clear intent
- Reduced confusion

---

### 15. Broad Exception Catching

**Current State:**
```python
except Exception as e:
    self.notify_listeners('error', {'error': str(e)})
```

**Why It's Not Great:**
- Catches all exceptions including programming errors
- Makes debugging harder
- Hides root causes

**What Should Be Changed:**
Catch specific exceptions:
```python
except requests.RequestException as e:
    # Handle API errors
except ValueError as e:
    # Handle validation errors
```

**Benefits:**
- Better error handling
- Easier debugging
- Unexpected errors bubble up properly

---

### 16. Magic Strings Throughout Codebase

**Current State:**
Strings like `'success'`, `'failure'`, `'error'`, `'book_spot'` are repeated as literals.

**Why It's Not Great:**
- Typos cause silent bugs
- Harder to refactor
- No IDE autocomplete support

**What Should Be Changed:**
Use enums or constants:
```python
class EventType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"

class ActionType(Enum):
    BOOK_SPOT = "book_spot"
    RELEASE_SPOT = "release_spot"
    ...
```

**Benefits:**
- Type safety
- IDE support and autocomplete
- Single source of truth

---

### 17. Type Hints Incomplete

**Current State:**
Some methods have type hints, others don't. Return types are often missing.

**Why It's Not Great:**
- Inconsistent documentation
- Limited IDE support
- Harder to understand method contracts

**What Should Be Changed:**
Add comprehensive type hints:
```python
def get_by_name(self, zone_id: str, name: str) -> dict[str, str] | None:
    ...

def do(self) -> dict[str, Any]:
    ...
```

**Benefits:**
- Better IDE support
- Self-documenting code
- Catch type errors with mypy

---

### 18. Docstrings Missing or Incomplete

**Current State:**
Some classes have docstrings, many methods don't. Some docstrings are outdated.

**Why It's Not Great:**
- Inconsistent documentation
- Harder onboarding
- Help text not available via `help()`

**What Should Be Changed:**
Add/update docstrings following Google or NumPy style:
```python
def take_spot(self, zone_id: str, spot_id: str, day: datetime | str) -> dict:
    """Reserve a parking spot for a specific date.
    
    Args:
        zone_id: The unique identifier of the parking zone.
        spot_id: The unique identifier of the spot to reserve.
        day: The date for the reservation.
        
    Returns:
        API response containing reservation status.
        
    Raises:
        requests.RequestException: If API call fails.
    """
```

**Benefits:**
- Better documentation
- IDE hover information
- Easier maintenance

---

## Project Sustainability

### 19. No Linting/Formatting Configuration

**Current State:**
No configuration for linters (ruff, flake8) or formatters (black, ruff format).

**Why It's Not Great:**
- Inconsistent code style
- Easy to introduce style violations
- Code review overhead

**What Should Be Changed:**
Add `pyproject.toml` configuration:
```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "UP"]

[tool.ruff.format]
quote-style = "double"
```

Add pre-commit hooks.

**Benefits:**
- Consistent code style
- Automated enforcement
- Reduced review cycles

---

### 20. No CI/CD Pipeline

**Current State:**
No GitHub Actions, GitLab CI, or other CI configuration.

**Why It's Not Great:**
- Tests (when added) won't run automatically
- No automated quality checks
- Manual release process

**What Should Be Changed:**
Add CI pipeline (e.g., `.github/workflows/ci.yml`):
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e .[dev]
      - run: pytest
      - run: ruff check .
```

**Benefits:**
- Automated testing
- Consistent quality gates
- Faster feedback loop

---

### 21. Version Not Derived from Single Source

**Current State:**
Version `0.1.2` appears in multiple places:
- `pyproject.toml`
- `Dockerfile`
- (potentially more)

**Why It's Not Great:**
- Easy to get out of sync
- Manual updates required in multiple places

**What Should Be Changed:**
Use `importlib.metadata` to get version at runtime:
```python
from importlib.metadata import version
__version__ = version("tidarator")
```

And in CLI:
```python
@click.version_option(version=__version__)
```

**Benefits:**
- Single source of truth
- Automatic version sync
- Standard Python practice

---

### 22. No Development Dependencies Section

**Current State:**
Only runtime dependencies in `pyproject.toml`. No dev dependencies defined.

**Why It's Not Great:**
- Unclear what tools developers need
- No testing framework specified
- Inconsistent dev environments

**What Should Be Changed:**
Add optional dependency group:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "ruff",
    "mypy",
]
```

**Benefits:**
- Clear development requirements
- Easy setup: `pip install -e .[dev]`
- Reproducible dev environments

---

### 23. Log File Location Not Configurable via CLI

**Current State:**
Log file path is set via environment variable or defaults to package directory.

**Why It's Not Great:**
- Not discoverable via `--help`
- Inconsistent with CLI-first approach
- Hard to override for single runs

**What Should Be Changed:**
Add `--log-file` option to CLI:
```python
@click.group()
@click.option('--log-file', type=click.Path(), envvar='LOG_FILE', help='Path to log file')
```

**Benefits:**
- Discoverable configuration
- Easy override for debugging
- Better CLI completeness

---

### 24. No Health Check in Docker Container

**Current State:**
Dockerfile doesn't define a HEALTHCHECK instruction.

**Why It's Not Great:**
- Docker/orchestrators can't monitor container health
- Harder to debug container issues

**What Should Be Changed:**
Add healthcheck (even a simple one):
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD tidarator --help > /dev/null || exit 1
```

**Benefits:**
- Container orchestration support
- Better monitoring
- Automatic restart on failures

---

### 25. Requirements.txt Lacks Version Pinning

**Current State:**
```
click
python-dotenv
requests
yagmail
```

**Why It's Not Great:**
- Builds are not reproducible
- Breaking changes in dependencies cause failures
- Different environments may have different versions

**What Should Be Changed:**
Pin versions or use version ranges:
```
click>=8.0,<9.0
python-dotenv>=1.0
requests>=2.28,<3.0
yagmail>=0.15
```

Or generate `requirements.lock` for exact pinning.

**Benefits:**
- Reproducible builds
- Protection from breaking changes
- Predictable behavior

---

---

## CLI Output & Logging Architecture

This section addresses the interaction between user-facing CLI output and developer/operations logging.

### 26. Report Format Lacks Decision Transparency

**Current State:**
The `book_free` report output looks like this:
```
I was looking for free spots from 2025-11-28 00:00:00 and tried to book spots ['07', '06'].

Bookings:
2026-01-21 | 07 |

https://share.parkanizer.com/reservations-list
```

Or when nothing is booked:
```
I was looking for free spots from 2025-11-28 00:00:00 and tried to book spots ['07', '06'].

No free spots found.
```

**Why It's Not Great:**
- **No visibility into the decision process**: Which days were considered? Which were skipped (weekend, already booked, no free spots)?
- **No information about spot priority**: Did it book '07' because it was preferred, or because '06' wasn't available?
- **Raw datetime object in output**: `2025-11-28 00:00:00` looks unprofessional
- **Confusing "No free spots found"**: Does this mean no days had free spots, or preferred spots weren't available?
- **Python list syntax in output**: `['07', '06']` is not user-friendly
- **No summary statistics**: How many days processed? How many successful?
- **Inconsistent table formatting**: Uses `|` separators but no headers or alignment

**What Should Be Changed:**

1. **Enrich the result data structure** in `BookSpot.do_for_payload()` to capture the decision trail:
```python
result['result'] = {
    'zone': zone['name'],
    'spot': reservation['name'],
    'for_date': p['for_date'],
    'status': 'success',
    'spots_tried': ['07'],           # NEW: which spots were attempted
    'spots_unavailable': ['06'],     # NEW: were in preference list but not free
}
```

2. **Capture filtering decisions** in `BookFreeSpots.do()`:
```python
result = {
    'action': 'book_free',
    'request': {...},
    'summary': {                      # NEW
        'days_in_range': 14,
        'days_skipped_weekend': 4,
        'days_skipped_already_booked': 2,
        'days_skipped_no_free_spots': 1,
        'days_attempted': 7,
        'days_successful': 5,
    },
    'result': attempts
}
```

3. **Improve the CLI report format** in `format_results()`:
```
BOOKING REPORT
══════════════════════════════════════════════════════════

Period:     2025-11-28 → 2025-12-15
Zone:       Parking-A
Preference: 07 → 06 (priority order)

  Date       │ Result │ Spot │ Notes
 ────────────┼────────┼──────┼─────────────────────────
  2025-12-02 │   ✓    │  07  │ 
  2025-12-03 │   ✓    │  06  │ 07 was taken
  2025-12-04 │   ✗    │  -   │ 07, 06 unavailable
  2025-12-05 │   ·    │  -   │ Already booked
  2025-12-06 │   ·    │  -   │ Weekend
  2025-12-09 │   ✓    │  07  │ 

──────────────────────────────────────────────────────────
Summary: 3 booked │ 1 failed │ 2 skipped (of 6 days)
══════════════════════════════════════════════════════════

https://share.parkanizer.com/reservations-list
```

4. **For email notifications**, use a cleaner text format:
```
TIDARATOR BOOKING REPORT
========================

Period: 2025-11-28 to 2025-12-15
Zone: Parking-A  
Spot preference: 07, 06

RESULTS:
  ✓ 2025-12-02: Booked spot 07
  ✓ 2025-12-03: Booked spot 06 (07 was taken)
  ✗ 2025-12-04: Failed - preferred spots unavailable
  · 2025-12-05: Skipped - already have a booking
  
SUMMARY: 2 booked, 1 failed, 1 skipped

https://share.parkanizer.com/reservations-list
```

5. **Format the date properly** - use `strftime` to format datetime objects:
```python
look_from = data['request']['look_from']
if isinstance(look_from, datetime):
    look_from = look_from.strftime('%Y-%m-%d')
```

**Benefits:**
- Complete transparency into the booking process
- Users understand *why* certain spots were booked over others
- Easy to verify the tool is working correctly
- Professional, readable output
- Actionable information (know which days need manual attention)
- Consistent formatting across all output types

---

### 27. Logging and CLI Output Are Interleaved on stdout

**Current State:**
```toml
# logging.toml
[handlers.console]
stream = "ext://sys.stdout"  # Logs go to stdout
```
```python
# tictl.py
click.echo(text)  # CLI output also goes to stdout
```

Both logging messages and CLI results go to stdout, creating interleaved output:
```
INFO:tidarator.spots.book_spot:Payload: {'for_date': '2025-01-06', ...}
INFO:tidarator.api.session_spot:Taking Spot 25 for 2025-01-06
Spot 25 in Zone-A was booked for 2025-01-06.
```

**Why It's Not Great:**
- User-facing output is polluted with debug information
- Can't pipe clean results to other commands
- Parsing output programmatically is unreliable
- Confusing for end users

**What Should Be Changed:**
Separate the streams by purpose:

1. **CLI output → stdout** (user-facing results only)
2. **Logging → stderr** (debug/diagnostic information)
3. **Errors → stderr** (error messages)

Update `logging.toml`:
```toml
[handlers.console]
class = "logging.StreamHandler"
formatter = "brief"
stream = "ext://sys.stderr"  # Changed from stdout
level = "WARNING"            # Only warnings+ to console by default
```

**Benefits:**
- Clean, pipeable stdout: `tidarator show-bookings | grep 2025-01`
- Debug info separate from results
- Standard Unix convention (stdout=data, stderr=diagnostics)

---

### 28. No `--quiet` / `--verbose` CLI Flags

**Current State:**
Log verbosity is controlled only via environment variable `LOG_LEVEL` or config file.

**Why It's Not Great:**
- Not discoverable (not in `--help`)
- Can't easily switch verbosity per-command
- Automation scripts can't suppress output easily

**What Should Be Changed:**
Add global flags to the CLI group:
```python
@click.group()
@click.option('-v', '--verbose', count=True, help='Increase verbosity (-v, -vv, -vvv)')
@click.option('-q', '--quiet', is_flag=True, help='Suppress non-essential output')
@click.pass_context
def cli(ctx, verbose, quiet):
    ctx.ensure_object(dict)
    
    # Map verbosity to log levels
    if quiet:
        log_level = logging.ERROR
    elif verbose == 0:
        log_level = logging.WARNING
    elif verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    
    logging.getLogger().setLevel(log_level)
```

Usage:
```bash
tidarator -q book-spot          # Silent except errors
tidarator -v show-bookings      # Info level
tidarator -vvv book-free        # Debug level for troubleshooting
```

**Benefits:**
- Standard CLI pattern users expect
- Discoverable via `--help`
- Easy per-invocation control
- Great for scripting (`-q`) and debugging (`-vvv`)

---

### 29. Dual Logging Systems Create Confusion

**Current State:**
```python
# tictl.py uses both:
import logging
logger = get_logger(__name__)

# Then mixes them:
logging.info("run_book_spot")      # Module-level logging
logger.info(...)                    # Instance logger

# Plus a listener that logs:
def log_message(event_type, data):
    logging.info(f"{event_type}, {data}")
```

**Why It's Not Great:**
- Three different logging mechanisms for the same purpose
- `logging.info()` bypasses module hierarchy
- Listener pattern duplicates logging responsibility
- Hard to understand which logs come from where

**What Should Be Changed:**

1. **Always use module logger:**
```python
logger = get_logger(__name__)
logger.info("run_book_spot")  # Not logging.info()
```

2. **Remove the log_message listener or make it optional:**
The observer pattern is for notifications (email, etc.), not logging. Logging should be internal to each action class.

3. **Action classes should log their own operations:**
```python
class BookSpot(ParkanizerActionBase):
    def do(self):
        logger.info(f"Booking spot: {self.payload}")
        # ... do work ...
        logger.debug(f"API response: {response}")
```

**Benefits:**
- Single, clear logging path
- Proper log hierarchy (`tidarator.spots.book_spot`)
- Easier to filter logs by module
- Observer pattern reserved for actual notifications

---

### 30. Interactive vs Headless Mode Not Distinguished

**Current State:**
The tool behaves identically whether run interactively or in automation (cron, CI, etc.).

**Why It's Not Great:**
- Interactive users want concise, formatted output
- Automation wants structured data (JSON) and detailed logs
- Can't optimize for both use cases

**What Should Be Changed:**
Detect or allow specifying the mode:

```python
@click.group()
@click.option('--batch', is_flag=True, envvar='TIDARATOR_BATCH', 
              help='Run in batch/automation mode')
@click.pass_context
def cli(ctx, batch):
    ctx.obj['batch_mode'] = batch or not sys.stdout.isatty()
```

Behavior differences:

| Aspect | Interactive | Batch/Headless |
|--------|-------------|----------------|
| Output format | Human-readable table | JSON |
| Colors | Yes (if terminal supports) | No |
| Progress indicators | Spinner/dots | None |
| Prompts | Yes (confirmations) | Auto-confirm or fail |
| Log level default | WARNING | INFO |

**Benefits:**
- Optimized UX for each use case
- Better automation support
- Standard practice for CLI tools

---

### 31. CLI Commands Could Be More Concise

**Current State:**
Commands use verbose names with hyphens:
```bash
tidarator book-spot --date 2025-01-06 --spot 25
tidarator release-spot --date 2025-01-06
tidarator show-bookings
tidarator show-spots --date 2025-01-06
tidarator book-free --start-from 2025-01-06
```

**Why It's Not Great:**
- Verbose for frequent use
- Inconsistent naming (`show-bookings` vs `show-spots`)
- No command aliases

**What Should Be Changed:**

1. **Add short aliases:**
```python
@cli.command(name='book', aliases=['b'])
@cli.command(name='release', aliases=['r']) 
@cli.command(name='bookings', aliases=['ls', 'list'])
@cli.command(name='spots', aliases=['status', 'st'])
@cli.command(name='auto', aliases=['book-free', 'a'])
```

2. **Shorter option names already exist, document them better:**
```bash
# Current (works but not prominent)
tidarator book-spot -d 2025-01-06 -s 25

# With aliases
tidarator b -d 2025-01-06 -s 25
tidarator ls              # list bookings
tidarator st              # spots status
tidarator r -d 2025-01-06 # release
```

3. **Consider positional arguments for common cases:**
```python
@click.argument('date', default='today', required=False)
# tidarator book 25           # book spot 25 for today
# tidarator book 25 2025-01-06  # book spot 25 for specific date
```

**Benefits:**
- Faster typing for power users
- Muscle memory friendly
- Still supports verbose forms for clarity/scripts

---

### 32. No Progress Indication for Long Operations

**Current State:**
`book-free` can take significant time (multiple API calls), with no feedback until completion.

**Why It's Not Great:**
- User doesn't know if it's working or hung
- No way to estimate completion time
- Poor UX for interactive use

**What Should Be Changed:**
Add progress indication using Click's utilities:

```python
from click import progressbar

def do(self):
    bookings_to_process = [...]
    
    with click.progressbar(bookings_to_process, 
                          label='Booking spots',
                          show_pos=True) as bar:
        for booking in bar:
            result = self._book_single(booking)
            # ...
```

Or for simpler cases, echo status:
```python
click.echo(f"Processing {len(bookings)} days...", err=True)
for i, booking in enumerate(bookings, 1):
    click.echo(f"  [{i}/{len(bookings)}] {booking['day']}...", err=True, nl=False)
    result = book(booking)
    click.echo(" ✓" if result else " ✗", err=True)
```

**Benefits:**
- User knows the tool is working
- Better UX for long operations
- Professional CLI feel

---

### 33. Success/Failure Not Reflected in Exit Codes

**Current State:**
Commands always exit with code 0 (success), even when operations fail:
```python
result = action.do()
print_result(result)  # Prints failure but exits 0
```

**Why It's Not Great:**
- Scripts can't detect failures: `tidarator book-spot && echo "booked"`
- CI/CD pipelines won't catch errors
- Breaks Unix conventions

**What Should Be Changed:**
Set appropriate exit codes:
```python
@cli.command()
@click.pass_context
def book_spot(ctx, date, spot):
    # ... do work ...
    result = action.do()
    print_result(result)
    
    if result.get('result', {}).get('status') != 'success':
        ctx.exit(1)  # Non-zero exit code for failure
```

Exit code conventions:
- 0: Success
- 1: Operation failed (couldn't book, no spots available)
- 2: Configuration error (missing env vars)
- 3: Authentication error
- 4: Network/API error

**Benefits:**
- Proper shell integration
- Reliable scripting: `tidarator book-spot || notify-admin`
- CI/CD pipeline support

---

### 34. Help Text Could Be More Informative

**Current State:**
```
$ tidarator --help
Commands:
  book-free      Automatically book free spots within your configured parameters.
  book-spot      Book a parking spot for a specific date.
  ...
```

**Why It's Not Great:**
- No examples in help
- No indication of required configuration
- Commands not grouped logically

**What Should Be Changed:**

1. **Add epilog with examples:**
```python
@click.group(epilog="""
Examples:
  tidarator book-spot -s 25              Book spot 25 for today
  tidarator book-spot -s 25 -s '*'       Try 25, then any available
  tidarator show-bookings                List your reservations
  tidarator book-free -l 7               Auto-book starting in 7 days

Configuration:
  Set TIDARO_USER, TIDARO_PASSWORD, SPOT_ZONE, SPOT_NAMES
  Or create a .env file. See README.md for details.
""")
def cli(ctx):
    ...
```

2. **Group related commands:**
```python
@cli.group(cls=click.Group)
def booking():
    """Commands for managing bookings."""
    
@booking.command(name='create')  # tidarator booking create
@booking.command(name='release') # tidarator booking release
@booking.command(name='list')    # tidarator booking list
```

**Benefits:**
- Self-documenting CLI
- Faster onboarding
- Less need to consult README

---

## Summary Priority Matrix

| Priority | Improvement | Impact | Effort |
|----------|-------------|--------|--------|
| High | Add tests (#11) | High | Medium |
| High | Fix security: pickle → JSON (#10) | High | Low |
| High | Add CI/CD (#20) | High | Low |
| High | Pin dependencies (#25) | High | Low |
| High | Improve report format (#26) | High | Medium |
| High | Separate logging to stderr (#27) | High | Low |
| High | Exit codes for failures (#33) | High | Low |
| Medium | Add --version (#1) | Medium | Low |
| Medium | Add --dry-run (#6) | Medium | Medium |
| Medium | Fix logging consistency (#13, #29) | Medium | Low |
| Medium | Add -q/-v flags (#28) | Medium | Low |
| Medium | Remove dead code (#14) | Low | Low |
| Medium | Add type hints (#17) | Medium | Medium |
| Medium | Better help text (#34) | Medium | Low |
| Low | Add output formats (#5) | Medium | Medium |
| Low | Add health check (#24) | Low | Low |
| Low | Use enums (#16) | Low | Medium |
| Low | Command aliases (#31) | Low | Low |
| Low | Progress indicators (#32) | Low | Medium |
| Low | Interactive/batch mode (#30) | Medium | Medium |

---
