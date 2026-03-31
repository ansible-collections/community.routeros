"""Hardware detection functions for community.routeros.

Each function takes an API connection object, queries the device,
and returns a string variant key.
"""

# Cache: keyed by (detector_name, connection_id) to support
# multiple connections in the same process (unlikely but safe).
_detection_cache = {}


def _cache_key(detector_name, api):
    """Build a cache key from the detector name and connection identity."""
    # Use id(api) as a proxy for connection identity within one process run.
    # This is safe because module runs are short-lived.
    return (detector_name, id(api))


def get_cached_or_detect(detector_name, api):
    """Return cached result or run detection and cache it."""
    key = _cache_key(detector_name, api)
    if key not in _detection_cache:
        detector = HARDWARE_DETECTORS[detector_name]
        _detection_cache[key] = detector(api)
    return _detection_cache[key]


def clear_cache():
    """Clear detection cache. Useful for testing."""
    _detection_cache.clear()


# --- Individual detector implementations ---

def detect_switch_chip_type(api):
    """Determine whether the switch chip uses single-entry or multi-entry semantics.

    CRS1xx/2xx (e.g. QCA8519 chip):
        /interface/ethernet/switch returns one entry, no meaningful .id,
        no per-port sub-entries in switch port-isolation.

    CRS3xx/5xx and others (e.g. MT7621, 88E6393X):
        /interface/ethernet/switch returns entries with .id and name,
        port-isolation has per-port entries keyed by name.

    Returns:
        'single_entry_switch' or 'multi_entry_switch'
    """
    try:
        result = list(api.path('/interface/ethernet/switch'))

        # Heuristic: CRS1xx/2xx have exactly one switch entry
        # and port-isolation entries do NOT have a 'name' field
        # CRS3xx/5xx: port-isolation entries HAVE a 'name' field
        if len(result) == 1:
            entry = result[0]
            try:
                pi_result = list(api.path('/interface/ethernet/switch/port-isolation'))
                # Check if port-isolation entries have 'name' field
                has_name_field = any('name' in e for e in pi_result)
                if has_name_field:
                    return 'multi_entry_switch'
                else:
                    return 'single_entry_switch'
            except Exception:
                pass

        return 'multi_entry_switch'

    except Exception:
        # If detection fails, default to multi-entry (modern/common hardware)
        return 'multi_entry_switch'


# --- Detector registry ---

HARDWARE_DETECTORS = {
    'switch_chip_type': detect_switch_chip_type,
}
