import importlib
import logging
import pkgutil

from monitordb.integrations.base import Integration


def discover() -> list[Integration]:

    integrations = []

    for module_record in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if not module_record.ispkg:
            continue

        module = importlib.import_module(f"{__name__}.{module_record.name}")

        integration = getattr(module, "INTEGRATION", None)

        if integration is None:
            raise RuntimeError()
        if not isinstance(integration, Integration):
            raise TypeError()

        integrations.append(integration)

        return integrations
