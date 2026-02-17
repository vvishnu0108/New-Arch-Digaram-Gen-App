import subprocess
from diagrams import Diagram, Cluster
from diagrams.azure.compute import VirtualMachine
from diagrams.azure.network import FrontDoors, Firewall, NetworkSecurityGroupsClassic
from diagrams.azure.monitor import LogAnalyticsWorkspaces
from diagrams.azure.security import Defender
from diagrams.onprem.client import User
from diagrams.generic.network import Router, Subnet

with Diagram("azure_vm_workload", show=False, outformat=["png", "dot"]):
    with Cluster("Management Subscription"):
        log_workspace = LogAnalyticsWorkspaces()
        defender = Defender()

    with Cluster("Connectivity Subscription"):
        user = User()
        front_door = FrontDoors()
        firewall = Firewall()
        hub_router = Router()
        user >> front_door >> firewall >> hub_router

    with Cluster("Workload Subscription"):
        spoke_router = Router()
        subnet = Subnet()
        nsg = NetworkSecurityGroupsClassic()
        vm1 = VirtualMachine()
        vm2 = VirtualMachine()

        hub_router >> spoke_router
        spoke_router >> subnet >> nsg
        nsg >> vm1 >> log_workspace
        nsg >> vm2 >> log_workspace

    firewall >> defender

subprocess.run(["graphviz2drawio", "azure_vm_workload.dot", "-o", "azure_vm_workload.drawio"], check=True)