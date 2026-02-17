"""
Diagram generation agent service with conversation history support and tool calling
"""
import os
import re
import json
from typing import Tuple, List, Optional, Generator, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv

from core.logging import get_logger
from utils import execute_generated_code, get_latest_files, read_drawio_xml
from services.sessions import session_manager
from services.diagram_classes import get_cached_reference
from services.knowledge_tools import ARCHITECTURE_TOOLS
from services.knowledge_tools import get_architecture_framework
from services.knowledge_tools import get_architecture_capabilities
from services.knowledge_tools import get_azure_reference_architecture

# ENHANCED OUTPUT FEATURES
from services.enhanced_output import (
    extract_architectural_reasoning,
    generate_architecture_explanation,
    validate_code_quality,
    format_enhanced_response,
    create_enhanced_system_prompt_addition,
    enhance_streaming_message,
    improve_error_message
)


load_dotenv()

# Initialize logger for this module
logger = get_logger("agent")



# Initialize LLM
llm = ChatOpenAI(
    api_key=os.getenv("llm_api_key", None),
    base_url=os.getenv("llm_api_base_url", "http://localhost:8080/v1"),
    model=os.getenv("llm_model_name", "meta/llama-3.3-70b-instruct"),
    streaming=os.getenv("llm_stream_usage", "false").lower() == "true",
    temperature=float(os.getenv("llm_temperature", "0")),
    max_tokens=int(os.getenv("llm_max_tokens", "4096")),
    timeout=float(os.getenv("llm_timeout", "120")) if os.getenv("llm_timeout") else None,
    max_retries=int(os.getenv("llm_max_retries", "3")),
)

# Create tool-enabled LLM for architecture knowledge lookups
llm_with_tools = llm.bind_tools(ARCHITECTURE_TOOLS)


def invoke_with_tools(messages: List, max_tool_iterations: int = 3) -> str:
    """
    Invoke the LLM with tool support, handling tool calls automatically.
    Returns the final response after all tool calls are processed.
    """
    current_messages = list(messages)
    
    for iteration in range(max_tool_iterations):
        response = llm_with_tools.invoke(current_messages)
        current_messages.append(response)
        
        # Check if there are tool calls to process
        if not response.tool_calls:
            # No more tool calls, return the content
            return response.content
        
        # Process each tool call
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find and execute the tool
            tool_result = None
            for tool in ARCHITECTURE_TOOLS:
                if tool.name == tool_name:
                    try:
                        tool_result = tool.invoke(tool_args)
                    except Exception as e:
                        tool_result = f"Error calling tool: {str(e)}"
                    break
            
            if tool_result is None:
                tool_result = f"Tool '{tool_name}' not found"
            
            # Add tool result to messages
            current_messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            )
    
    # If we've exhausted iterations, get final response
    final_response = llm.invoke(current_messages)
    return final_response.content


def get_tool_based_system_prompt() -> str:
    """
    Build a concise system prompt that instructs the LLM to use tools for architecture knowledge.
    This is much shorter than the full prompt and relies on tool calls for domain knowledge.
    """
    return """
You are a SENIOR INFRASTRUCTURE SOLUTIONS ARCHITECT and expert Python developer for the 'diagrams' library.
Your goal is to DESIGN a complete, production-ready infrastructure-first architecture and generate Python code to visualize it.

## NON-NEGOTIABLE INFRASTRUCTURE RULES

When Azure Landing Zone concepts are active:

1. Infrastructure primitives (management groups, subscriptions, VNets)
   MUST be designed BEFORE any workload services.

2. A workload MUST NOT create or define VNets.
   - One workload = one Spoke VNet.
   - Application tiers are subnets, NOT VNets.

3. Connectivity controls ingress and egress.
   - Front Door, Application Gateway, Firewall belong to Connectivity.
   - Workloads receive traffic; they do not manage entry.

4. Platform services enforce governance.
   - Identity, monitoring, and security are authoritative, not optional.
   - They apply constraints to workloads.

5. If a workload pattern conflicts with infrastructure rules,
   the infrastructure rules MUST override the pattern.

6. Every Azure Landing Zone diagram MUST explicitly show:
   - Management Subscription
   - Connectivity Subscription
   - One or more Workload Subscriptions

Resources MUST NOT cross subscription boundaries incorrectly.

7. All inbound traffic MUST visibly traverse:
   User → Front Door → Firewall → Application Gateway → Spoke VNet
Direct workload exposure is forbidden.

Violating any of the above is considered an architectural error. You MUST use tools to check for architecture patterns and infrastructure best practices.

## PRODUCTION-READINESS REQUIREMENTS (CRITICAL)

For **microservices architectures**, you MUST include ALL of these layers (minimum 20 components):

**MANDATORY Infrastructure Layers:**
1. **Identity & Access**: Azure AD, Managed Identity
2. **Security**: Azure Defender, Security Center, Policy
3. **Global Connectivity**: Front Door, CDN, DNS
4. **Network Security**: Firewall, NSG, DDoS Protection
5. **Application Gateway**: App Gateway with WAF
6. **Network**: Hub VNet, Spoke VNet(s), Private Endpoints
7. **Container Infrastructure**: ACR, AKS with node pools
8. **API Management**: Azure API Management (MUST include for microservices)

**MANDATORY Application Layers:**
9. **Microservices**: At least 5-6 individual services (Auth, User, Order, Payment, Notification, etc.)
10. **Service Discovery**: Kubernetes DNS, health checks
11. **Messaging**: Service Bus OR Event Hubs (REQUIRED for microservices)

**MANDATORY Data Layer:**
12. **Database**: Cosmos DB OR SQL Database
13. **Caching**: Redis Cache (REQUIRED for performance)
14. **Storage**: Blob Storage for artifacts

**MANDATORY Secrets & Config:**
15. **Secrets Management**: Key Vault (REQUIRED, never hardcode secrets)

**MANDATORY Observability (NOT OPTIONAL):**
16. **Monitoring**: Azure Monitor + Application Insights
17. **Logging**: Log Analytics Workspace
18. **Tracing**: Application Insights Distributed Tracing
19. **Alerting**: Azure Monitor Alerts + Action Groups

**MANDATORY DevOps:**
20. **CI/CD**: Azure DevOps OR GitHub Actions pipeline

**Resilience Patterns (MUST mention in code comments):**
- Health checks (readiness/liveness probes)
- Circuit breakers
- Retry policies
- Auto-scaling (HPA)

If ANY of these layers are missing, the architecture is INCOMPLETE and NOT production-ready.

## AVAILABLE TOOLS

You have access to the following tools for architecture knowledge. USE THEM:

1. **get_lenovo_product_info**: Get Lenovo ThinkAgile product specs (MX, HX, VX nodes)
   - Call when: User mentions Lenovo, ThinkAgile, hybrid cloud, on-premises
   
2. **get_architecture_pattern**: Get best practices for architecture patterns
   - Call when: Designing data pipelines, microservices, hybrid cloud, three-tier apps
   
3. **get_infrastructure_recommendations**: Get components for a layer (networking, security, monitoring, storage, compute)
   - Call when: Adding infrastructure layers to the design

4. **get_azure_reference_architecture**: Get Azure production reference packets (mandatory layers/components)
   - Call when: User asks for Azure architectures and you need a complete baseline

5. **get_diagram_classes**: Get valid diagram icon imports for a cloud provider
   - Call when: Need to verify import statements are correct

6. **get_architecture_framework**: Determine if architecture framework (e.g., Azure Landing Zone) applies
    - Call when: Starting a new architecture design


## WORKFLOW

1.      First, determine the governing architecture framework
    a.  Call get_architecture_framework at the very beginning.
    b.  Decide whether a framework (for example, Azure Landing Zone) applies.
    c.  If a framework is applied:
        i.      Treat its rules as mandatory.
        ii.     Framework constraints override workload patterns and user preferences.
        iii.    Layer ownership, ordering, and forbidden patterns are fixed at this stage.
2.      Then, gather supporting architecture knowledge
    a.  Use get_architecture_pattern to refine the workload design.
    b.  Use get_infrastructure_recommendations to fully expand each required layer.
    c.  Abstract requests must be expanded into complete, production-ready layers.
3.      Validate architectural correctness before coding
    a.  Ensure infrastructure is defined before workloads.
    b.  Ensure connectivity controls ingress and egress.
    c.  Ensure platform services enforce identity, security, and monitoring.
    d.  Ensure no forbidden patterns from the framework or references are present.
4.      Finally, generate the Python diagram code
    a.  Generate production-ready Python code using the diagrams library.
    b.  Reflect enforced layers and ownership using clusters.
    c.  Convert the output to draw.io format as required.



## CODE GENERATION RULES

1. **Imports**: Only use valid class names from the diagrams library
2. **Output format**: `with Diagram("filename", show=False, outformat=["png", "dot"]):`
3. **draw.io Conversion**: MUST include at the end of code:
   ```
   import subprocess
   subprocess.run(["graphviz2drawio", "filename.dot", "-o", "filename.drawio"], check=True)
   ```
4. **Clustering**: Use `with Cluster("Name"):` to group components. Minimum 3 clusters.
5. **Components**: Minimum 6-8 components for simple, 10-15 for medium architectures
6. **Connections**: Use `>>` for data flow

## ENHANCED OUTPUT (REQUIRED)

Your response MUST include architectural reasoning to help users understand your design decisions.

**Response Structure:**

1. **Architectural Reasoning** (2-4 sentences):
   - Start with "Architectural Reasoning:" followed by your explanation
   - Explain key design decisions and why you chose specific components
   - Address how the architecture meets requirements and follows framework rules
   - Mention any important trade-offs or design principles applied

2. **Python Code**:
   - Complete, production-ready code following all rules above

**Example Format:**
```
Architectural Reasoning: This design follows Azure Landing Zone principles with clear separation 
between platform and workload concerns. The Connectivity subscription manages all ingress through 
Front Door and Application Gateway, while the Workload spoke VNet contains application tiers as 
subnets. Identity and monitoring are enforced by platform services to ensure governance compliance.

[Your Python code here]
```

Return your response in this exact format: reasoning first, then code.
"""


def get_system_prompt() -> str:
    """Build the system prompt with dynamically discovered diagram classes."""
    diagram_classes_reference = get_cached_reference()

    
    return f"""
You are a SENIOR INFRASTRUCTURE SOLUTIONS ARCHITECT and expert Python developer for the 'diagrams' library.
Your goal is to DESIGN a complete, production-ready infrastructure-first architecture and generate Python code to visualize it.

## NON-NEGOTIABLE INFRASTRUCTURE RULES (ALZ MODE)

When Azure Landing Zone concepts are active:

1. Infrastructure primitives (management groups, subscriptions, VNets)
   MUST be designed BEFORE any workload services.

2. A workload MUST NOT create or define VNets.
   - One workload = one Spoke VNet.
   - Application tiers are subnets, NOT VNets.

3. Connectivity controls ingress and egress.
   - Front Door, Application Gateway, Firewall belong to Connectivity.
   - Workloads receive traffic; they do not manage entry.

4. Platform services enforce governance.
   - Identity, monitoring, and security are authoritative, not optional.
   - They apply constraints to workloads.

5. If a workload pattern conflicts with infrastructure rules,
   the infrastructure rules MUST override the pattern.

6. Every Azure Landing Zone diagram MUST explicitly show:
   - Management Subscription
   - Connectivity Subscription
   - One or more Workload Subscriptions

Resources MUST NOT cross subscription boundaries incorrectly.

7. All inbound traffic MUST visibly traverse:
   User → Front Door → Firewall → Application Gateway → Spoke VNet
Direct workload exposure is forbidden.

Violating any of the above is considered an architectural error. You MUST use tools to check for architecture patterns and infrastructure best practices.

## ARCHITECT'S MINDSET - THINK BEFORE YOU CODE

Before writing any code, reason through the architecture like a human infrastructure architect:

### Step 1: Understand the Core Requirements
- What is the primary workload? (data pipeline, web application, ML platform, etc.)
- What are the key services explicitly mentioned?
- What cloud provider should be used?

### Step 2: Identify ALL Required Layers
A production architecture typically needs ALL of these layers. Include them unless explicitly told otherwise:

1. **INGESTION/ENTRY LAYER**: How does data/traffic enter the system?
   - API Gateway, Load Balancer, CDN, Cloud Functions, Pub/Sub, etc.

2. **NETWORKING/SECURITY LAYER**: How is traffic routed and secured?
   - VPC, Subnets, Firewalls, Cloud Armor, IAM, Private Endpoints
   - For GCP: VPC, CloudNAT, CloudDNS, Firewall
   - For AWS: VPC, SecurityGroups, PrivateLink, Route53
   - For Azure: VirtualNetwork, ApplicationGateway, Firewall

3. **COMPUTE/PROCESSING LAYER**: Where does computation happen?
   - VMs, Containers, Kubernetes, Serverless functions
   - Data processing: Dataflow, EMR, Databricks, Glue

4. **STORAGE LAYER**: Where is data stored?
   - Object storage: GCS, S3, BlobStorage
   - Databases: BigQuery, RDS, CosmosDB
   - Caching: Redis, Memcached

5. **ORCHESTRATION LAYER**: How are workflows coordinated?
   - Cloud Composer, Airflow, Step Functions, Logic Apps

6. **MONITORING/OBSERVABILITY LAYER**: How is the system observed?
   - Cloud Monitoring, CloudWatch, Azure Monitor
   - Logging: Cloud Logging, CloudWatch Logs
   - Alerting and dashboards

### Step 3: Design Data Flows
- Trace the path of data from ingestion to final destination
- Identify all transformations and handoffs
- Ensure connections make logical sense

### Step 4: Apply Best Practices
- High availability: Use multiple zones/regions where appropriate
- Security: Ensure proper network isolation and access control
- Scalability: Use managed services that auto-scale
- Cost: Consider appropriate service tiers

## EXAMPLE REASONING

User request: "GCP data pipeline with BigQuery and Dataflow"

WRONG approach (too minimal):
- Just add GCS, BigQuery, Dataflow icons
- Result: 3 icons with arrows

RIGHT approach (think like an architect):
1. Data enters via Pub/Sub or GCS (ingestion)
2. Needs VPC for network security
3. Dataflow jobs run in a subnet with proper IAM
4. Data lands in GCS staging bucket
5. Transformed data goes to BigQuery
6. Cloud Composer orchestrates the pipeline
7. Cloud Monitoring watches everything
8. Cloud Logging captures all logs

Result: 10+ components organized into logical clusters

## LENOVO HYBRID CLOUD EXPERTISE

You are also an expert in Lenovo's Hybrid Cloud infrastructure solutions. When the user mentions Lenovo, ThinkAgile, hybrid cloud, on-premises, or private cloud, think from this perspective:

### Lenovo ThinkAgile Product Knowledge

1. **ThinkAgile MX Series** (Microsoft Azure Stack HCI)
   - Hyperconverged infrastructure certified for Azure Stack HCI
   - Best for: Windows-centric workloads, Azure hybrid scenarios, Hyper-V virtualization
   - Use cases: SQL Server, Virtual Desktop Infrastructure (VDI), Azure Arc integration
   - Represent with: Server/VM icons labeled as "MX Node" + Azure integration components

2. **ThinkAgile HX Series** (Nutanix)
   - Hyperconverged infrastructure powered by Nutanix
   - Best for: Multi-hypervisor environments, AHV/ESXi/Hyper-V workloads
   - Use cases: Enterprise applications, databases, private cloud, disaster recovery
   - Represent with: Server icons labeled as "HX Node" + Nutanix Prism management layer

3. **ThinkAgile VX Series** (VMware vSAN)
   - Hyperconverged infrastructure certified for VMware vSAN
   - Best for: VMware-centric environments, vSphere workloads
   - Use cases: VM consolidation, software-defined storage, VCF deployments
   - Represent with: Server icons labeled as "VX Node" + VMware vCenter/vSAN components

### Lenovo Infrastructure Components

When designing Lenovo hybrid cloud architectures, ALWAYS include:

1. **Compute Layer (ThinkAgile Nodes)**:
   - MX, HX, or VX nodes based on hypervisor requirements
   - Use `diagrams.onprem.compute.Server` with labels like "ThinkAgile MX Node"
   - Include multiple nodes for HA (minimum 3-4 nodes per cluster)

2. **Networking Layer (Lenovo Switches)**:
   - Top-of-Rack (ToR) switches for north-south traffic
   - Spine switches for east-west traffic in larger deployments
   - Network management (XClarity, CNOS)
   - Use `diagrams.onprem.network.Consul` or `diagrams.generic.network.Switch` with Lenovo labels

3. **Storage Layer**:
   - Integrated SDS (vSAN, Nutanix, S2D) within HCI nodes
   - Optional external storage (ThinkSystem DM/DE Series) for backup/archive
   - Use `diagrams.onprem.storage` icons with appropriate labels

4. **Management Layer**:
   - Lenovo XClarity Administrator for hardware lifecycle management
   - Hypervisor-specific management (vCenter, Prism, Windows Admin Center)
   - Use `diagrams.onprem.compute` icons for management servers

5. **Hybrid Cloud Connectivity**:
   - Azure Arc, VMware Cloud on AWS, Nutanix NC2
   - VPN/ExpressRoute/DirectConnect for cloud connectivity
   - Include cloud landing zone components

### Example: Lenovo Hybrid Cloud Architecture

User request: "Lenovo-based private cloud with Azure hybrid connectivity"

Components to include:
- Multiple ThinkAgile MX Nodes (3-4 for HA)
- ToR Switches (2 for redundancy)
- XClarity Administrator for management
- Azure Stack HCI cluster
- Azure Arc for hybrid management
- ExpressRoute/VPN for Azure connectivity
- Windows Admin Center
- Backup solution (ThinkSystem DM or Azure Backup)
- Monitoring (Azure Monitor + XClarity)

{diagram_classes_reference}

## CODE GENERATION RULES

1. **Imports**: You MUST use ONLY the class names listed above. Do NOT invent class names.
   - Always check the reference above before using any import.
   - If a class doesn't exist in the list above, find an alternative that DOES exist.
   
2. **Syntax - CRITICAL**:
   - You MUST use the `outformat` parameter in the Diagram object.
   - CORRECT: `with Diagram("filename", show=False, outformat=["png", "dot"]):`
   - Note: The first argument "filename" is the output name. Keep it simple (no spaces).

3. **draw.io Conversion - MANDATORY**:
   - You MUST include subprocess import and graphviz2drawio conversion at the END of your code.
   - This is NOT optional. Every script MUST end with this conversion.
   
   REQUIRED CODE TEMPLATE:
   ```
   import subprocess
   from diagrams import Diagram, Cluster
   # ... other imports ...
   
   with Diagram("filename", show=False, outformat=["png", "dot"]):
       # ... diagram code ...
   
   # MANDATORY: Convert to draw.io format
   subprocess.run(["graphviz2drawio", "filename.dot", "-o", "filename.drawio"], check=True)
   ```
   
   NOTE: Replace "filename" with your actual diagram name (lowercase, no spaces).
   The subprocess.run line MUST appear AFTER the Diagram context block closes.

4. **Component Selection**:
   - For databases, use the appropriate database icons (e.g., RDS for AWS, SQLDatabases for Azure).
   - For compute, use EC2 for AWS, VirtualMachine or VM for Azure, ComputeEngine for GCP.
   - For Kubernetes: use EKS for AWS, AKS for Azure, GKE for GCP.
   - For networking, use classes from the network category.
   - ALWAYS include networking, security, and monitoring components.
   
5. **Data Flow**:
   - Use `>>` for connections.
   - Connections should follow logical data/traffic flow.
   - Label connections if helpful using Edge() with label parameter.

6. **Clustering (MANDATORY)**: 
   - Use `with Cluster("Cluster Name"):` to group related components. 
   - Create clusters for each logical layer: "Ingestion", "Processing", "Storage", "Networking", "Monitoring"
   - Indent components inside the cluster block.
   - MINIMUM 3 clusters for any non-trivial architecture.

7. **Minimum Components**:
   - Simple architectures: At least 6-8 components
   - Medium architectures: At least 10-15 components
   - Complex architectures: 15+ components
   - NEVER create diagrams with only 3-4 components unless explicitly asked for minimal diagram.

8. **Output**: Return ONLY raw Python code. No markdown formatting. No explanations.

If I give you an error message, fix the specific import or attribute that failed.
"""


# Keep SYSTEM_PROMPT for backward compatibility, but it will be rebuilt dynamically
SYSTEM_PROMPT = get_system_prompt()


def get_update_system_prompt() -> str:
    """Build the update system prompt with dynamically discovered diagram classes."""
    diagram_classes_reference = get_cached_reference()
    
    return f"""
You are a SENIOR INFRASTRUCTURE SOLUTIONS ARCHITECT and expert Python developer for the 'diagrams' library.
Your goal is to DESIGN a complete, production-ready infrastructure-first architecture and generate Python code to visualize it.

## NON-NEGOTIABLE INFRASTRUCTURE RULES (ALZ MODE)

When Azure Landing Zone concepts are active:

1. Infrastructure primitives (management groups, subscriptions, VNets)
   MUST be designed BEFORE any workload services.

2. A workload MUST NOT create or define VNets.
   - One workload = one Spoke VNet.
   - Application tiers are subnets, NOT VNets.

3. Connectivity controls ingress and egress.
   - Front Door, Application Gateway, Firewall belong to Connectivity.
   - Workloads receive traffic; they do not manage entry.

4. Platform services enforce governance.
   - Identity, monitoring, and security are authoritative, not optional.
   - They apply constraints to workloads.

5. If a workload pattern conflicts with infrastructure rules,
   the infrastructure rules MUST override the pattern.

6. Every Azure Landing Zone diagram MUST explicitly show:
   - Management Subscription
   - Connectivity Subscription
   - One or more Workload Subscriptions

Resources MUST NOT cross subscription boundaries incorrectly.

7. All inbound traffic MUST visibly traverse:
   User → Front Door → Firewall → Application Gateway → Spoke VNet
Direct workload exposure is forbidden.


Violating any of the above is considered an architectural error. You MUST use tools to check for architecture patterns and infrastructure best practices.

## ARCHITECT'S MINDSET FOR MODIFICATIONS

When the user asks for changes, THINK like an architect, not a code editor:

### Interpretation Guidelines

1. **Abstract concepts → Concrete implementations**
   - User says "add networking" → Add VPC, Subnets, NAT Gateway, Firewall, DNS, Load Balancer
   - User says "add security" → Add IAM, KMS, Secrets Manager, Cloud Armor, WAF
   - User says "add monitoring" → Add Cloud Monitoring, Logging, Alerting, Dashboards
   - User says "add caching" → Add Redis/Memcached, CDN if applicable

2. **Layer additions should be complete**
   - If adding a "networking layer", include ALL networking components (not just one icon)
   - If adding "storage", consider what types: object storage, database, cache, archive

3. **Connection updates**
   - When adding new components, think about how they connect to existing ones
   - Networking components should wrap/contain other components or connect logically
   - Security components (firewalls, etc.) should be positioned between entry points and services

### Examples of GOOD vs BAD modifications

User says: "Add a networking layer"

BAD (too minimal):
```python
# Just adds: networking = Networking("Network")
```

GOOD (architect thinking):
```python
with Cluster("Networking"):
    vpc = VPC("Main VPC")
    firewall = Firewall("Cloud Firewall") 
    nat = NAT("NAT Gateway")
    dns = DNS("Cloud DNS")
    # Position these to wrap the processing components
```

User says: "Add monitoring"

BAD: Just adds one Monitoring icon

GOOD: Adds Monitoring, Logging, Alerting in a Monitoring cluster, connected to all services

### Lenovo Hybrid Cloud Modifications

When modifying Lenovo/ThinkAgile/on-premises architectures:

1. **"Add more nodes"** → Add ThinkAgile nodes with proper labels (MX/HX/VX based on existing architecture)
2. **"Add networking"** → Add ToR switches, spine switches, network management (XClarity)
3. **"Add storage"** → Consider SDS within nodes vs external ThinkSystem storage
4. **"Add management"** → Add XClarity Administrator, hypervisor management consoles
5. **"Add hybrid connectivity"** → Add Azure Arc/VMware Cloud/ExpressRoute based on platform
6. **"Add backup"** → Add backup appliance or cloud backup integration

{diagram_classes_reference}

## CONTEXT

The user has an existing diagram and wants to make changes to it.
You will receive:
1. The previous diagram code
2. The user's modification request

## YOUR TASK

Generate UPDATED Python code that:
1. INTERPRETS the user's request architecturally (expand abstract concepts)
2. Incorporates changes while maintaining existing components
3. Ensures the architecture remains production-ready

## CODE GENERATION RULES

1. **Imports**: You MUST use ONLY the class names listed above. Do NOT invent class names.
   - Always check the reference above before using any import.
   - If a class doesn't exist in the list above, find an alternative that DOES exist.

2. Keep the same filename as the original diagram

3. Preserve existing components unless told to remove them

4. **EXPAND abstract requests**: 
   - "Add networking" = Add multiple networking components (VPC, Firewall, NAT, DNS, etc.)
   - "Add security" = Add multiple security components (IAM, KMS, Firewall, etc.)
   - "Add monitoring" = Add monitoring + logging + alerting
   - NEVER add just a single icon for a complete layer

5. Update connections to integrate new components logically

6. Create new clusters for new layers being added

7. **draw.io Conversion - MANDATORY**:
   - You MUST include subprocess import at the top
   - You MUST add graphviz2drawio conversion at the END of your code
   - Example: `subprocess.run(["graphviz2drawio", "filename.dot", "-o", "filename.drawio"], check=True)`
   - This line MUST appear AFTER the Diagram context block closes

8. **Minimum additions for layer requests**:
   - Adding a "layer" or "component category" = At least 3-5 new components
   - Adding a specific service = That service plus any logically required supporting services

Return ONLY raw Python code. No markdown formatting. No explanations.

If I give you an error message, fix the specific import or attribute that failed.
"""


# Keep for backward compatibility
UPDATE_SYSTEM_PROMPT = get_update_system_prompt()

def build_framework_context(framework_result: str) -> str:
    """
    Convert framework JSON into strict architectural constraints
    to be injected into the system prompt.
    """
    data = json.loads(framework_result)
    framework = data.get("framework", {})

    lines = [
        "ARCHITECTURE FRAMEWORK ENFORCEMENT (STEP 0)",
        f"Framework: {framework.get('name', 'Unknown')}",
        "",
        "MANDATORY CONSTRAINTS:"
    ]

    for layer in framework.get("mandatory_platform_layers", []):
        lines.append(
            f"- MUST include platform layer: {layer['name']} ({layer['purpose']})"
        )

    placement_rules = framework.get("workload_placement_rules", {})
    for rule in placement_rules.values():
        lines.append(f"- {rule}")

    diagram_rules = framework.get("diagram_enforcement_rules", {})
    if diagram_rules.get("require_hub_spoke_visualization"):
        lines.append("- Networking MUST follow hub-spoke topology")

    if diagram_rules.get("require_platform_vs_workload_separation"):
        lines.append("- Platform components MUST be separated from workloads")

    return "\n".join(lines)



def extract_filename_from_code(code: str) -> Optional[str]:
    """Extract the diagram filename from generated code"""
    # Look for patterns like: with Diagram("filename", ...)
    match = re.search(r'with\s+Diagram\s*\(\s*["\']([^"\']+)["\']', code)
    if match:
        return match.group(1).lower().replace(" ", "_")
    return None


def parse_error_for_llm(error_output: str) -> str:
    """
    Parse error output and create an enhanced error message for the LLM.
    Extracts 'Did you mean' suggestions and provides clear correction instructions.
    """
    lines = error_output.strip().split('\n')
    
    # Extract the main error message
    error_type = ""
    error_detail = ""
    suggestion = ""
    failed_import = ""
    
    for line in lines:
        # Look for ImportError or ModuleNotFoundError
        if "ImportError:" in line or "ModuleNotFoundError:" in line:
            error_detail = line.split(":", 1)[-1].strip() if ":" in line else line
            
            # Extract the failed import name
            if "cannot import name" in line:
                match = re.search(r"cannot import name '(\w+)'", line)
                if match:
                    failed_import = match.group(1)
        
        # Look for "Did you mean" suggestions
        if "Did you mean:" in line:
            match = re.search(r"Did you mean: '?(\w+)'?", line)
            if match:
                suggestion = match.group(1)
    
    # Build enhanced error message
    enhanced_message = [
        "CODE EXECUTION FAILED",
        "=" * 40,
        f"Error: {error_detail}" if error_detail else f"Error:\n{error_output}",
    ]
    
    if failed_import and suggestion:
        enhanced_message.extend([
            "",
            "⚠️ CRITICAL FIX REQUIRED:",
            f"   Replace '{failed_import}' with '{suggestion}'",
            "",
            "The class name you used does NOT exist. Use the suggested alternative.",
        ])
    elif failed_import:
        enhanced_message.extend([
            "",
            "⚠️ FIX REQUIRED:",
            f"   The class '{failed_import}' does not exist in this module.",
            "   Check the AVAILABLE DIAGRAM CLASSES list at the top of this conversation.",
            "   Use ONLY class names that are listed there.",
        ])
    
    enhanced_message.extend([
        "",
        "Instructions:",
        "1. Analyze the error carefully",
        "2. Fix ONLY the problematic import/code",
        "3. Return the COMPLETE corrected Python code",
        "4. Do NOT add explanations, return ONLY code",
    ])
    
    return "\n".join(enhanced_message)


def generate_diagram_code_with_tools(
    user_request: str,
    session_id: Optional[str] = None,
    max_retries: int = 10,
    use_tools: bool = True
) -> Tuple[str, str, bool, str, str]:
    """
    Generates code using tool-calling for architecture knowledge.
    Falls back to traditional approach if tools aren't supported.
    Returns: (final_code, status_message, success, session_id, base_filename)
    """
    # Get or create session
    session = session_manager.get_or_create_session(session_id)
    
    # Add user message to history
    session_manager.add_message(session.session_id, "user", user_request)
    
    code = ""
    base_filename = ""
    last_error = ""
    
    # Phase 1: Architecture Framework Detection (e.g., Azure Landing Zone)
    framework_context = ""

    try:
        framework_result = get_architecture_framework.invoke({
            "user_request": user_request
        })
        framework_data = json.loads(framework_result)

        if framework_data.get("framework_applied"):
            framework_context = build_framework_context(framework_result)
            logger.info("Phase 1: Architecture framework applied")
        else:
            logger.info("Phase 1: No architecture framework applied")

    except Exception as e:
        logger.warning(f"Phase 1: Framework detection failed, continuing normally: {e}")

    # Phase 2: Service Capability Resolution
    capability_context = ""
    azure_reference_context = ""

    if "azure" in user_request.lower():
        try:
            azure_reference_context = get_azure_reference_architecture.invoke({
                "workload_type": "microservices"
            })
            logger.info("Phase 2a: Azure reference architecture packet loaded")
        except Exception as e:
            logger.warning(f"Phase 2a: Azure reference packet loading failed: {e}")

    try:
        # Ask LLM what services it intends to use
        service_probe_prompt = [
            SystemMessage(content="List the Azure services required for this architecture."),
            HumanMessage(content=user_request)
        ]

        planned_services = llm.invoke(service_probe_prompt).content
        planned_services = re.findall(r"\b[a-z_]+", planned_services.lower())

        capability_result = get_architecture_capabilities.invoke({
            "services": planned_services
        })

        if capability_result and capability_result != "{}":
            capability_context = f"""
            SERVICE CAPABILITY CONSTRAINTS (NON-NEGOTIABLE)

            The following service constraints MUST be enforced
            when placing components in the diagram:

            {capability_result}

            Violating these constraints is an architectural error.
            """
            logger.info("Phase 2: Capability resolution succeeded")

    except Exception as e:

        logger.warning(f"Phase 2: Capability resolution failed: {e}")


    # Phase 3: Use tools to gather architecture knowledge
    if use_tools:
        logger.info("Phase 3: Gathering architecture knowledge with tools")
        try:
            # Build messages for tool-based knowledge gathering
            system_prompt = get_tool_based_system_prompt()

            # Inject framework constraints ONLY if applicable
            if framework_context:
                user_request = f"""
                ARCHITECTURE MODE:INFRA-FIRST

                You MUST first resolve the platform topology (management, connectivity, monitoring).
                Only after that, place the workload into the approved spoke.

                User workload request:{user_request}"""
                system_prompt += "\n\n" + framework_context

            if capability_context:
                system_prompt += "\n\n" + capability_context

            if azure_reference_context and "Error:" not in azure_reference_context:
                system_prompt += f"""

                AZURE PRODUCTION REFERENCE PACKET (HIGH PRIORITY)

                Use this as a completeness checklist for Azure designs:
                {azure_reference_context}

                If the user asks for a simplified diagram, keep layer intent but reduce node count.
                """

            tool_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"""
            I need to create an architecture diagram for: {user_request}

            Please:
            1. Apply the architecture framework rules if provided
            2. Select the appropriate workload pattern
            3. Expand all required infrastructure layers
            4. Generate production-ready Python diagram code
            """)
            ]

            
            # Invoke with tools - this handles the tool calling loop
            code = invoke_with_tools(tool_messages, max_tool_iterations=5)
            code = code.replace("```python", "").replace("```", "").strip()
            
            # Extract filename and try to execute
            base_filename = extract_filename_from_code(code) or f"diagram_{session.session_id}"
            
            logger.info("Tool-based code generated, attempting execution")
            success, output = execute_generated_code(code)
            
            if success:
                session_manager.add_message(session.session_id, "assistant", f"Generated diagram: {base_filename}")
                files = get_latest_files(base_filename)
                diagram_xml = ""
                if "drawio" in files:
                    diagram_xml = read_drawio_xml(files["drawio"])
                
                session_manager.update_diagram(
                    session.session_id,
                    diagram_xml,
                    base_filename,
                    user_request,
                    code
                )
                return code, "Success (tool-based)", True, session.session_id, base_filename
            else:
                logger.warning(f"Tool-based code failed: {output}")
                last_error = output
                # Fall through to retry loop
                
        except Exception as e:
            logger.error(f"Tool-based generation failed: {e}")
            last_error = str(e)
            # Fall through to traditional approach
    
    # Phase 4: Self-correction loop (same as traditional approach)
    logger.info("Phase 4: Self-correction loop")
    history = [(("system", SYSTEM_PROMPT))]
    
    if code:
        # Start with the tool-generated code that failed
        history.append(("human", f"Create a diagram for: {user_request}"))
        history.append(("ai", code))
        history.append(("human", parse_error_for_llm(last_error)))
    else:
        history.append(("human", f"Create a diagram for: {user_request}"))
    
    for attempt in range(max_retries):
        logger.debug(f"Correction attempt {attempt + 1}")
        
        try:
            prompt = ChatPromptTemplate.from_messages(history)
            chain = prompt | llm
            response = chain.invoke({})
            
            code = response.content.replace("```python", "").replace("```", "").strip()
            base_filename = extract_filename_from_code(code) or f"diagram_{session.session_id}"
            
            success, output = execute_generated_code(code)
            
            if success:
                session_manager.add_message(session.session_id, "assistant", f"Generated diagram: {base_filename}")
                files = get_latest_files(base_filename)
                diagram_xml = ""
                if "drawio" in files:
                    diagram_xml = read_drawio_xml(files["drawio"])
                
                session_manager.update_diagram(
                    session.session_id,
                    diagram_xml,
                    base_filename,
                    user_request,
                    code
                )
                return code, "Success", True, session.session_id, base_filename
            else:
                enhanced_error = parse_error_for_llm(output)
                last_error = output
                logger.warning(f"Error on attempt {attempt+1}: {output}")
                
                history.append(("ai", code))
                history.append(("human", enhanced_error))
                
        except Exception as e:
            last_error = f"LLM call failed: {str(e)}"
            logger.error(f"Exception on attempt {attempt+1}: {last_error}")
            
            if attempt < max_retries - 1:
                history.append(("human", f"There was an error. Please try again: {str(e)}"))
                continue
    
    return code, f"Failed after {max_retries} attempts. Last error: {last_error}", False, session.session_id, base_filename


def generate_diagram_code(
    user_request: str,
    session_id: Optional[str] = None,
    max_retries: int = 10
) -> Tuple[str, str, bool, str, str]:
    """
    Generates code, attempts to run it, and self-corrects if it fails.
    Returns: (final_code, status_message, success, session_id, base_filename)
    """
    # Get or create session
    session = session_manager.get_or_create_session(session_id)
    
    # Add user message to history
    session_manager.add_message(session.session_id, "user", user_request)
    
    # Build conversation history
    history = [("system", SYSTEM_PROMPT)]
    
    # Add previous conversation context if exists
    prev_messages = session_manager.get_conversation_for_llm(session.session_id)
    if len(prev_messages) > 1:  # More than just the current message
        history.extend(prev_messages[:-1])  # Exclude current message
    
    history.append(("human", f"Create a diagram for: {user_request}"))
    
    code = ""
    base_filename = ""
    last_error = ""
    
    for attempt in range(max_retries):
        logger.debug(f"Generation attempt {attempt + 1}")
        
        try:
            # Generate Code
            prompt = ChatPromptTemplate.from_messages(history)
            chain = prompt | llm
            response = chain.invoke({})
            
            # Clean the output
            code = response.content.replace("```python", "").replace("```", "").strip()
            
            # Extract filename from code
            base_filename = extract_filename_from_code(code) or f"diagram_{session.session_id}"
            
            # Execute Code
            success, output = execute_generated_code(code)
            
            if success:
                # Add assistant response to history
                session_manager.add_message(session.session_id, "assistant", f"Generated diagram: {base_filename}")
                
                # Get the generated drawio XML
                files = get_latest_files(base_filename)
                diagram_xml = ""
                if "drawio" in files:
                    diagram_xml = read_drawio_xml(files["drawio"])
                
                # Update session with diagram info and store the code
                session_manager.update_diagram(
                    session.session_id,
                    diagram_xml,
                    base_filename,
                    user_request,
                    code  # Store the successful code for future updates
                )
                
                return code, "Success", True, session.session_id, base_filename
            else:
                # Parse and enhance the error message for better LLM understanding
                enhanced_error = parse_error_for_llm(output)
                last_error = output
                logger.warning(f"Error on attempt {attempt+1}: {output}")
                
                history.append(("ai", code))
                history.append(("human", enhanced_error))
                
        except Exception as e:
            # Handle LLM call failures gracefully - continue to next attempt
            last_error = f"LLM call failed: {str(e)}"
            logger.error(f"Exception on attempt {attempt+1}: {last_error}")
            
            # If we have code from a previous attempt, try to continue
            if attempt < max_retries - 1:
                history.append(("human", f"There was an error generating code. Please try again: {str(e)}"))
                continue
    
    return code, f"Failed after {max_retries} attempts. Last error: {last_error}", False, session.session_id, base_filename


def update_diagram_code(
    session_id: str,
    update_request: str,
    max_retries: int = 10
) -> Tuple[str, str, bool, str]:
    """
    Updates an existing diagram based on user feedback.
    Returns: (final_code, status_message, success, base_filename)
    """
    session = session_manager.get_session(session_id)
    if not session:
        return "", "Session not found", False, ""
    
    # Add user message
    session_manager.add_message(session_id, "user", update_request)
    
    # Get previous code from session (stored when diagram was generated)
    previous_code = session.last_generated_code
    
    # Build update prompt
    history = [("system", UPDATE_SYSTEM_PROMPT)]
    
    if previous_code:
        history.append(("human", f"Previous diagram code:\n```python\n{previous_code}\n```"))
        history.append(("ai", "I understand the current diagram structure."))
    
    # Add context about previous diagram
    if session.diagram_description:
        history.append(("human", f"The current diagram shows: {session.diagram_description}"))
    
    history.append(("human", f"Please modify the diagram: {update_request}"))
    
    code = ""
    base_filename = session.current_base_filename or f"diagram_{session_id}"
    last_error = ""
    
    for attempt in range(max_retries):
        logger.debug(f"Update attempt {attempt + 1}")
        
        try:
            prompt = ChatPromptTemplate.from_messages(history)
            chain = prompt | llm
            response = chain.invoke({})
            
            code = response.content.replace("```python", "").replace("```", "").strip()
            
            # Keep the same filename if possible
            extracted_filename = extract_filename_from_code(code)
            if extracted_filename:
                base_filename = extracted_filename
            
            success, output = execute_generated_code(code)
            
            if success:
                session_manager.add_message(session_id, "assistant", f"Updated diagram: {update_request}")
                
                files = get_latest_files(base_filename)
                diagram_xml = ""
                if "drawio" in files:
                    diagram_xml = read_drawio_xml(files["drawio"])
                
                # Update session with new diagram info and code
                session_manager.update_diagram(
                    session_id,
                    diagram_xml,
                    base_filename,
                    f"{session.diagram_description}; {update_request}" if session.diagram_description else update_request,
                    code  # Store the updated code for future updates
                )
                
                return code, "Success", True, base_filename
            else:
                # Parse and enhance the error message for better LLM understanding
                enhanced_error = parse_error_for_llm(output)
                last_error = output
                logger.warning(f"Error on attempt {attempt+1}: {output}")
                
                history.append(("ai", code))
                history.append(("human", enhanced_error))
                
        except Exception as e:
            # Handle LLM call failures gracefully - continue to next attempt
            last_error = f"LLM call failed: {str(e)}"
            logger.error(f"Exception on attempt {attempt+1}: {last_error}")
            
            if attempt < max_retries - 1:
                history.append(("human", f"There was an error. Please try again: {str(e)}"))
                continue
    
    return code, f"Failed after {max_retries} attempts. Last error: {last_error}", False, base_filename


def generate_diagram_code_streaming(
    user_request: str,
    session_id: Optional[str] = None,
    max_retries: int = 10
) -> Generator[str, None, None]:
    """
    Streaming version of generate_diagram_code that yields status updates.
    Yields SSE-formatted messages with status updates.
    """
    def sse_message(event: str, data: Dict[str, Any]) -> str:
        """Format a message for SSE"""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
    
    # Get or create session
    yield sse_message("status", {"message": "📝 Analyzing your request...", "step": "init"})
    
    session = session_manager.get_or_create_session(session_id)
    session_manager.add_message(session.session_id, "user", user_request)
    
    # Build conversation history
    history = [("system", SYSTEM_PROMPT)]
    prev_messages = session_manager.get_conversation_for_llm(session.session_id)
    if len(prev_messages) > 1:
        history.extend(prev_messages[:-1])
    history.append(("human", f"Create a diagram for: {user_request}"))
    
    code = ""
    base_filename = ""
    last_error = ""
    
    for attempt in range(max_retries):
        yield sse_message("status", {
            "message": f"🔧 Attempt {attempt + 1}: Generating diagram code...",
            "step": "generating",
            "attempt": attempt + 1,
            "max_retries": max_retries
        })
        
        try:
            # Generate Code
            prompt = ChatPromptTemplate.from_messages(history)
            chain = prompt | llm
            response = chain.invoke({})
            
            code = response.content.replace("```python", "").replace("```", "").strip()
            base_filename = extract_filename_from_code(code) or f"diagram_{session.session_id}"
            
            yield sse_message("status", {
                "message": f"▶️ Attempt {attempt + 1}: Executing code...",
                "step": "executing",
                "attempt": attempt + 1
            })
            
            # Execute Code
            success, output = execute_generated_code(code)
            
            if success:
                yield sse_message("status", {
                    "message": "✅ Success! Loading diagram...",
                    "step": "success"
                })
                
                session_manager.add_message(session.session_id, "assistant", f"Generated diagram: {base_filename}")
                
                files_dict = get_latest_files(base_filename)
                diagram_xml = ""
                if "drawio" in files_dict:
                    diagram_xml = read_drawio_xml(files_dict["drawio"])
                
                # Format files as array with URLs (matching non-streaming endpoint)
                files_list = []
                for fmt, filepath in files_dict.items():
                    import os
                    files_list.append({
                        "format": fmt,
                        "filename": os.path.basename(filepath),
                        "url": f"/api/diagrams/files/{base_filename}.{fmt}"
                    })
                
                session_manager.update_diagram(
                    session.session_id,
                    diagram_xml,
                    base_filename,
                    user_request,
                    code
                )
                
                # Final result
                yield sse_message("complete", {
                    "success": True,
                    "code": code,
                    "message": "Success",
                    "session_id": session.session_id,
                    "base_filename": base_filename,
                    "diagram_xml": diagram_xml,
                    "files": files_list
                })
                return
            else:
                enhanced_error = parse_error_for_llm(output)
                last_error = output
                
                yield sse_message("status", {
                    "message": f"⚠️ Attempt {attempt + 1} failed. Analyzing error...",
                    "step": "error",
                    "attempt": attempt + 1,
                    "error": output[:200]  # Truncate for display
                })
                
                history.append(("ai", code))
                history.append(("human", enhanced_error))
                
        except Exception as e:
            last_error = f"LLM call failed: {str(e)}"
            
            yield sse_message("status", {
                "message": f"⚠️ Attempt {attempt + 1} exception. Retrying...",
                "step": "exception",
                "attempt": attempt + 1,
                "error": str(e)[:200]
            })
            
            if attempt < max_retries - 1:
                history.append(("human", f"There was an error generating code. Please try again: {str(e)}"))
                continue
    
    # Failed after all retries
    yield sse_message("complete", {
        "success": False,
        "code": code,
        "message": f"Failed after {max_retries} attempts. Last error: {last_error}",
        "session_id": session.session_id,
        "base_filename": base_filename
    })
