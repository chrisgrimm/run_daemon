import jax
import sys


def _is_in_debug_mode() -> bool:
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is None:
        raise Exception('Failed to check if debug mode is active.')
    elif gettrace():
        return True
    else:
        return False


def turn_off_jit_if_debug_mode() -> None:
    if _is_in_debug_mode():
        jax.config.update('jax_disable_jit', True)