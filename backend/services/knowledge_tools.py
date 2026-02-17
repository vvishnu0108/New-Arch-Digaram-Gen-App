"""
Knowledge tools for the diagram generation agent.
These tools provide on-demand access to architecture knowledge.
"""
import json
import os
from typing import Optional
from langchain_core.tools import tool

# Get the directory where this file is located
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")


def _load_json(filename: str) -> dict:
    """Load a JSON file from the knowledge directory."""
    filepath = os.path.join(KNOWLEDGE_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}



@tool
def get_lenovo_product_info(product_series: str) -> str:
    """
    Get Lenovo ThinkAgile product specifications and recommended diagram components.
    
    Use this tool when the user mentions:
    - Lenovo, ThinkAgile, or ThinkSystem products
    - Hybrid cloud or on-premises infrastructure
    - MX, HX, or VX series nodes
    - XClarity management
    
    Args:
        product_series: The product series to get info for. Options:
            - "MX" for ThinkAgile MX (Azure Stack HCI)
            - "HX" for ThinkAgile HX (Nutanix)
            - "VX" for ThinkAgile VX (VMware vSAN)
            - "networking" for Lenovo switches and network components
            - "storage" for ThinkSystem storage options
            - "management" for XClarity and management tools
            - "all" for a complete overview
    
    Returns:
        JSON string with product specifications, use cases, and diagram representation info.
    """
    data = _load_json("lenovo_products.json")
    
    if not data:
        return "Error: Lenovo product knowledge base not found."
    
    product_series = product_series.upper() if product_series else "ALL"
    
    if product_series == "ALL":
        # Return a summary of all products
        summary = {
            "available_products": list(data.keys()),
            "MX": {
                "name": data.get("MX", {}).get("name", ""),
                "platform": data.get("MX", {}).get("platform", ""),
                "best_for": data.get("MX", {}).get("best_for", [])
            },
            "HX": {
                "name": data.get("HX", {}).get("name", ""),
                "platform": data.get("HX", {}).get("platform", ""),
                "best_for": data.get("HX", {}).get("best_for", [])
            },
            "VX": {
                "name": data.get("VX", {}).get("name", ""),
                "platform": data.get("VX", {}).get("platform", ""),
                "best_for": data.get("VX", {}).get("best_for", [])
            }
        }
        return json.dumps(summary, indent=2)
    
    if product_series in data:
        return json.dumps(data[product_series], indent=2)
    
    return f"Product series '{product_series}' not found. Available options: MX, HX, VX, networking, storage, management, all"


@tool
def get_architecture_pattern(pattern_type: str) -> str:
    """
    Get best practices and component recommendations for an architecture pattern.
    
    Use this tool when designing:
    - Data pipelines (ETL, streaming, batch processing)
    - Microservices architectures
    - Hybrid cloud deployments
    - Three-tier web applications
    
    Args:
        pattern_type: The architecture pattern. Options:
            - "data_pipeline" for ETL/streaming architectures
            - "microservices" for distributed service architectures
            - "hybrid_cloud" for on-prem + cloud architectures
            - "three_tier" for presentation/app/data layer architectures
            - "all" for a list of available patterns
    
    Returns:
        JSON string with pattern description, layers, components per cloud provider, and best practices.
    """
    data = _load_json("architecture_patterns.json")
    
    if not data:
        return "Error: Architecture patterns knowledge base not found."
    
    pattern_type = pattern_type.lower().replace(" ", "_").replace("-", "_")
    
    if pattern_type == "all":
        patterns = []
        for key, value in data.items():
            patterns.append({
                "id": key,
                "name": value.get("name", ""),
                "description": value.get("description", "")
            })
        return json.dumps({"available_patterns": patterns}, indent=2)
    
    if pattern_type in data:
        return json.dumps(data[pattern_type], indent=2)
    
    return f"Pattern '{pattern_type}' not found. Available options: data_pipeline, microservices, hybrid_cloud, three_tier, all"



@tool
def get_architecture_framework(user_request: str) -> str:
    """
    Determine whether a governing architecture framework
    (e.g., Azure Landing Zone) must be applied.

    This tool MUST be called before selecting workload patterns
    if a cloud provider is mentioned.
    """
    data = _load_json("architecture_frameworks.json")

    if not data:
        return json.dumps({
            "framework_applied": False,
            "reason": "Framework knowledge base not found"
        })

    request_lower = user_request.lower()

    frameworks = data.get("frameworks", {})

    for framework in frameworks.values():
        triggers = framework.get("apply_when", {}).get("any_of", [])
        if any(trigger in request_lower for trigger in triggers):
            return json.dumps({
                "framework_applied": True,
                "framework": framework
            })

    return json.dumps({
        "framework_applied": False,
        "reason": "No framework matched. Proceed with original architecture logic."
    })




@tool
def get_infrastructure_recommendations(layer: str, platform: str = "all") -> str:
    """
    Get recommended infrastructure components for a specific layer and platform.
    
    Use this tool when:
    - Adding networking, security, monitoring, or storage components
    - Need to know the correct diagram icons for a cloud provider
    - Expanding a layer with complete components
    
    Args:
        layer: The infrastructure layer. Options:
            - "networking" for VPC, firewalls, load balancers, DNS
            - "security" for IAM, KMS, secrets management
            - "monitoring" for metrics, logging, tracing
            - "storage" for object, block, and file storage
            - "compute" for VMs, containers, serverless
        platform: The cloud platform. Options:
            - "gcp" for Google Cloud Platform
            - "aws" for Amazon Web Services  
            - "azure" for Microsoft Azure
            - "onprem" for on-premises/Lenovo infrastructure
            - "all" for all platforms (default)
    
    Returns:
        JSON string with component names, diagram icons, and purposes.
    """
    data = _load_json("infrastructure_components.json")
    
    if not data:
        return "Error: Infrastructure components knowledge base not found."
    
    layer = layer.lower()
    platform = platform.lower()
    
    if layer not in data:
        available = list(data.keys())
        return f"Layer '{layer}' not found. Available layers: {', '.join(available)}"
    
    layer_data = data[layer]
    
    if platform == "all":
        return json.dumps(layer_data, indent=2)
    
    if platform in layer_data:
        return json.dumps({platform: layer_data[platform]}, indent=2)
    
    available_platforms = list(layer_data.keys())
    return f"Platform '{platform}' not found for layer '{layer}'. Available platforms: {', '.join(available_platforms)}"


@tool  
def get_diagram_classes(provider: str, category: str = "all") -> str:
    """
    Get available diagram classes/icons for a specific cloud provider.
    
    Use this tool before writing import statements to ensure you use valid class names.
    
    Args:
        provider: The cloud/infrastructure provider. Options:
            - "gcp" for Google Cloud Platform icons
            - "aws" for Amazon Web Services icons
            - "azure" for Microsoft Azure icons
            - "onprem" for on-premises infrastructure icons
            - "k8s" for Kubernetes icons
            - "generic" for generic/custom icons
        category: Optional category to filter. Options vary by provider but include:
            - "compute", "network", "database", "storage", "security", "analytics", etc.
            - "all" for all categories (default)
    
    Returns:
        JSON string with available diagram class imports and their usage.
    """
    # This leverages the existing diagram_classes module
    from services.diagram_classes import get_cached_reference
    
    reference = get_cached_reference()
    
    provider = provider.lower()
    category = category.lower() if category else "all"
    
    # Filter the reference based on provider
    lines = reference.split("\n")
    filtered_lines = []
    
    provider_mapping = {
        "gcp": "diagrams.gcp",
        "aws": "diagrams.aws",
        "azure": "diagrams.azure",
        "onprem": "diagrams.onprem",
        "k8s": "diagrams.k8s",
        "generic": "diagrams.generic"
    }
    
    if provider not in provider_mapping:
        return f"Provider '{provider}' not found. Available: gcp, aws, azure, onprem, k8s, generic"
    
    prefix = provider_mapping[provider]
    
    for line in lines:
        if prefix in line:
            if category == "all" or category in line.lower():
                filtered_lines.append(line.strip())
    
    if not filtered_lines:
        return f"No diagram classes found for provider '{provider}' with category '{category}'"
    
    return f"Available diagram classes for {provider}:\n" + "\n".join(filtered_lines[:50])  # Limit to 50 entries

@tool
def get_architecture_capabilities(services: Optional[list] = None) -> str:
    """
    Get service-level architectural capabilities and constraints.

    This tool defines WHAT a service can and cannot do architecturally,
    such as:
    - Whether it can live inside a VNet
    - Whether it requires Private Endpoints
    - Whether it supports VNet Integration
    - Forbidden placement patterns

    Use this tool:
    - BEFORE placing services into VNets or subnets
    - When deciding networking paths and boundaries
    - To prevent invalid architecture diagrams

    Args:
        services: Optional list of service identifiers (e.g. ["app_service", "azure_sql_database"]).
                  If omitted, returns all known capabilities.

    Returns:
        JSON string with capability rules.
    """
    data = _load_json("architecture_capabilities.json")

    if not data:
        return json.dumps({
            "error": "Architecture capabilities knowledge base not found"
        })

    capabilities = data.get("service_capabilities", {})

    if not services:
        # Return all capabilities (used when model is still exploring)
        return json.dumps(capabilities, indent=2)

    result = {}
    for service in services:
        if service in capabilities:
            result[service] = capabilities[service]

    return json.dumps(result, indent=2)



# Export all tools
ARCHITECTURE_TOOLS = [
    get_architecture_framework,
    get_architecture_capabilities,
    get_lenovo_product_info,
    get_architecture_pattern,
    get_infrastructure_recommendations,
    get_diagram_classes
]
