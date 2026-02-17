"""
Dynamic diagram classes discovery.
This module introspects the installed diagrams library to extract all available
node classes, which can then be included in LLM prompts for accurate code generation.
"""
import importlib
import pkgutil
from typing import Dict, List, Set
from functools import lru_cache


# Major providers to introspect
PROVIDERS = [
    "diagrams.aws",
    "diagrams.azure", 
    "diagrams.gcp",
    "diagrams.k8s",
    "diagrams.onprem",
    "diagrams.generic",
]

# Common categories within providers
COMMON_CATEGORIES = [
    "compute", "database", "network", "storage", "security",
    "analytics", "integration", "ml", "iot", "containers",
    "client", "queue", "inmemory", "monitoring", "devtools",
    "general", "web", "mobile", "identity", "management",
]


def get_module_classes(module_path: str) -> List[str]:
    """Get all public class names from a module."""
    try:
        module = importlib.import_module(module_path)
        classes = []
        for name in dir(module):
            if not name.startswith('_'):
                obj = getattr(module, name)
                if isinstance(obj, type):
                    classes.append(name)
        return classes
    except (ImportError, ModuleNotFoundError):
        return []


def get_provider_submodules(provider: str) -> List[str]:
    """Get all submodules of a provider package."""
    try:
        package = importlib.import_module(provider)
        submodules = []
        if hasattr(package, '__path__'):
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                submodules.append(f"{provider}.{modname}")
        return submodules
    except (ImportError, ModuleNotFoundError):
        return []


@lru_cache(maxsize=1)
def discover_all_diagram_classes() -> Dict[str, Dict[str, List[str]]]:
    """
    Discover all available diagram classes from the installed library.
    Returns a nested dict: {provider: {category: [class_names]}}
    
    This is cached so it only runs once at startup.
    """
    result = {}
    
    for provider in PROVIDERS:
        provider_name = provider.split(".")[-1]  # e.g., "aws", "azure"
        result[provider_name] = {}
        
        submodules = get_provider_submodules(provider)
        for submodule in submodules:
            category = submodule.split(".")[-1]
            classes = get_module_classes(submodule)
            if classes:
                result[provider_name][category] = classes
    
    return result


@lru_cache(maxsize=1)
def get_diagram_classes_reference() -> str:
    """
    Generate a formatted reference string of all available diagram classes
    for inclusion in LLM prompts.
    """
    all_classes = discover_all_diagram_classes()
    
    lines = ["AVAILABLE DIAGRAM CLASSES (use EXACTLY these names):"]
    lines.append("=" * 60)
    
    for provider, categories in all_classes.items():
        lines.append(f"\n## diagrams.{provider}")
        
        # Prioritize common categories
        sorted_cats = sorted(categories.keys(), 
            key=lambda x: (x not in COMMON_CATEGORIES, x))
        
        for category in sorted_cats:
            classes = categories[category]
            if classes:
                # Format: diagrams.azure.compute: AKS, VirtualMachine, FunctionApps, ...
                class_list = ", ".join(sorted(classes)[:15])  # Limit to 15 most important
                if len(classes) > 15:
                    class_list += f"... (+{len(classes) - 15} more)"
                lines.append(f"  - diagrams.{provider}.{category}: {class_list}")
    
    lines.append("\n" + "=" * 60)
    lines.append("IMPORTANT NOTES:")
    lines.append("- Azure Kubernetes: Use 'AKS' or 'KubernetesServices' (NOT ContainerService)")
    lines.append("- User icons: Use 'User' from 'diagrams.onprem.client' (NOT onprem.user)")
    lines.append("- Always verify import paths match exactly as shown above")
    
    return "\n".join(lines)


# Pre-warm the cache on module import
_reference = None

def get_cached_reference() -> str:
    """Get the cached diagram classes reference."""
    global _reference
    if _reference is None:
        _reference = get_diagram_classes_reference()
    return _reference


if __name__ == "__main__":
    # Test the discovery
    print(get_diagram_classes_reference())
