"""VOX Function Modules — Phase 2 auto-discovery.

Each module in this package uses @vox_registry.register() to add new functions.
discover_functions() imports all modules to trigger registration.
"""
import importlib
import pkgutil
import pathlib


def discover_functions():
    """Import all function modules to trigger @vox_registry.register() decorators."""
    package_dir = pathlib.Path(__file__).parent
    for _, name, _ in pkgutil.iter_modules([str(package_dir)]):
        if name != "__init__":
            importlib.import_module(f".{name}", __package__)
