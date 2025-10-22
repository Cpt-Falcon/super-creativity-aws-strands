"""
Global state manager for graph execution.

Since AWS Strands' invocation_state is read-only and not propagated between
node executions, we use a global state manager that all nodes can access
to read/write iteration and other execution context outside the graph.
"""

import threading

# Thread-safe state storage
_state_lock = threading.Lock()
_global_state = {
    'current_iteration': 0,
    'max_iterations': 1,
    'run_id': 'unknown'
}


def initialize_state(max_iterations: int, run_id: str):
    """Initialize the global execution state."""
    global _global_state
    with _state_lock:
        _global_state = {
            'current_iteration': 0,
            'max_iterations': max_iterations,
            'run_id': run_id
        }


def get_current_iteration() -> int:
    """Get the current iteration number."""
    with _state_lock:
        return _global_state['current_iteration']


def set_current_iteration(iteration: int):
    """Set the current iteration number."""
    with _state_lock:
        _global_state['current_iteration'] = iteration


def increment_iteration() -> int:
    """Increment the iteration counter and return new value."""
    with _state_lock:
        if _global_state['current_iteration'] < _global_state['max_iterations']:
            _global_state['current_iteration'] += 1
        return _global_state['current_iteration']


def get_max_iterations() -> int:
    """Get max iterations."""
    with _state_lock:
        return _global_state['max_iterations']


def get_global_state() -> dict:
    """Get a copy of the global state."""
    with _state_lock:
        return _global_state.copy()


def reset_state():
    """Reset the global state."""
    with _state_lock:
        _global_state = {
            'current_iteration': 0,
            'max_iterations': 1,
            'run_id': 'unknown'
        }
