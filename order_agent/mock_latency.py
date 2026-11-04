"""Simulated waiting time for teaching mocks; never a model performance estimate."""
import random
import time

DEFAULTS = {
    'model_delay_seconds': [0.3, 0.9],
    'tool_delay_seconds': [0.05, 0.2],
}
_settings = dict(DEFAULTS)

def validate_settings(settings):
    result = {**DEFAULTS, **settings}
    for name, bounds in result.items():
        if name not in DEFAULTS:
            raise ValueError('Unknown mock setting: ' + name)
        if (not isinstance(bounds, (list, tuple)) or len(bounds) != 2
                or any(type(v) not in (int, float) for v in bounds)
                or not 0 <= bounds[0] <= bounds[1] < float('inf')):
            raise ValueError(name + ' must be [min, max] with 0 <= min <= max')
    return result

def configure(settings):
    global _settings
    _settings = validate_settings(settings)

def simulate_latency(kind):
    low, high = _settings[kind + '_delay_seconds']
    time.sleep(random.uniform(low, high))
