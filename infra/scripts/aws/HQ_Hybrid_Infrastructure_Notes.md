# HQ Hybrid Infrastructure Notes

## Purpose

These notes capture the infrastructure observed so far from Auvik and connect it to the broader hybrid environment: on-prem network, AWS/Azure view-only discovery, Egnyte documentation, and GitHub repositories.

The goal is to build a read-only understanding of:

- What devices and networks exist.
- How internet, firewall, core switching, access switching, VLANs, and subnets connect.
- Where critical dependencies and possible risks are.
- What questions should be answered before proposing changes.
- What inventory or documentation could be useful to the team.

## Current High-Level Topology

```text
Internet / Cloud
  |
  v
USPAJ35A-FW01
Meraki MX450 firewall
  |
  v
UPPAJ35A-SWCORE-01.fs.local
Cisco C9500-48Y4C core switch
  |
  +--> 10.5.0.0/20 subnet
  |      +--> 9 devices
  |      +--> 14 devices in 10.5.2.x range
  |      +--> 3 Auvik virtual appliances
  |      +--> 5 unknown devices, including Device@10.5.1.134
  |
  +--> Cisco C9300-48UN switch stacks
         +--> USPAJ35A-SW.fs.local
         +--> Access-layer devices and VLANs
         +--> Admin, Lobby, Vendor, Kitchen, WiFi, HQ Supernet, and other networks
```

## Main Mental Model

| Layer | Device / Area | Meaning |
|---|---|---|
| Internet Edge | Internet / cloud icon | Public internet or ISP-facing side of the network map |
| Firewall | USPAJ35A-FW01, Meraki MX450 | Security edge between internet and internal HQ networks |
| Core | UPPAJ35A-SWCORE-01, Cisco C9500 | Central internal switching/routing layer |
| Access / Distribution | Cisco C9300 stacks | Where real-world devices, Wi-Fi, office gear, and appliances likely connect |
| Subnets / VLANs | 10.5.0.0/20, 10.30.x.x networks | Logical network segments for different systems, users, locations, or functions |
| Monitoring | Auvik virtual appliances | Network discovery and monitoring collectors |

## Internet Edge / Firewall

### Device Summary

| Field | Value |
|---|---|
| Map Layer | Internet Edge / Perimeter |
| Upstream Connection | Internet / cloud icon in Auvik |
| Device Name | USPAJ35A-FW01 |
| Device Type | Firewall / security appliance |
| Vendor / Model | Cisco Meraki MX450 |
| Management Status | Managed |
| Network / Site | HQ Supernet |
| IP Addresses Seen | 10.30.240.1, 10.30.250.14 possibly, 10.30.250.30, 10.30.250.33 |

Note: `10.30.25014` looked like a possible formatting issue. Confirm whether this should be `10.30.250.14`.

### Interpretation

`USPAJ35A-FW01` appears to be the main firewall/security appliance sitting between the public internet and the internal HQ network.

Likely flow:

```text
Internet / Cloud
  |
  v
USPAJ35A-FW01 - Meraki MX450 Firewall
  |
  v
HQ internal networks / downstream core switch / VLANs
```

This device is probably one of the most important devices in the environment. It may control:

- Internet access.
- Inbound and outbound firewall rules.
- Site-to-site VPNs.
- Client VPN.
- SD-WAN behavior.
- VLAN interfaces or default gateways, depending on design.
- Security policies.
- Connectivity to cloud or branch locations.

### What The Main Fields Mean

| Field | Meaning |
|---|---|
| Internet / cloud icon | The outside/public side of the network, usually ISP/internet-facing |
| `FW01` | Likely "Firewall 01", possibly the primary firewall |
| Managed status | Auvik has management visibility into the device |
| Meraki MX450 | Enterprise Meraki security appliance, likely managed through Meraki Dashboard |
| Multiple private IPs | The firewall may participate in multiple internal networks or VLANs |
| HQ Supernet | A larger summarized HQ network range or site grouping |

### High-Value Remarks

- Because this firewall sits directly below the internet/cloud layer, it is a critical dependency for HQ internet and possibly VPN/cloud connectivity.
- Because the model is Meraki MX450, the Meraki Dashboard may be the source of truth for WAN uplinks, firewall rules, VLANs, VPNs, and security settings.
- Multiple IPs on the firewall suggest it may connect to multiple VLANs, transit networks, management networks, or internal segments.
- If there is no `FW02` or HA pair, this firewall may be a single point of failure.

### Follow-Up Questions

1. Is `USPAJ35A-FW01` the primary internet-edge firewall for HQ?
2. Is there a secondary firewall, such as `USPAJ35A-FW02`, in HA/failover mode?
3. Which ISP circuits connect to this firewall?
4. Are there dual WAN links?
5. Does this firewall terminate VPN tunnels to AWS, Azure, branches, or vendors?
6. Which listed IP is the inside gateway, management IP, or transit IP?
7. Is Meraki Dashboard the authoritative source for firewall configuration?
8. Are firewall rules documented?
9. Are config backups enabled?
10. Who owns and approves firewall changes?

## Core Switch

### Device Summary

| Field | Value |
|---|---|
| Device Role | Core switch |
| Device Name | UPPAJ35A-SWCORE-01 |
| Domain Seen | fs.local |
| Vendor / Model | Cisco C9500-48Y4C |
| Management Status | Managed |
| Example IPs Seen | 10.30.14.1, 10.30.14.2, 10.30.14.3, 10.30.18.3 |
| Interface Example | TwentyFiveGigE1/0/43 |
| Connection Count Seen | Blue line showing 6 grouped connections |
| Networks / Labels Seen | Admin, Lobby, Vendor, Kitchen, WiFi, WiFi Admin, HQ Supernet, and others |

### Interpretation

The Cisco C9500 is the core switch. This means it is likely a central internal device responsible for connecting many parts of the network together.

Likely flow:

```text
Meraki MX450 Firewall
  |
  v
UPPAJ35A-SWCORE-01 Core Switch
  |
  +--> Internal VLANs
  +--> Access switch stacks
  +--> Server or appliance subnets
  +--> Wi-Fi networks
  +--> Lobby/vendor/kitchen/admin networks
```

If the firewall is the front door to the internet, the core switch is the main internal traffic hub.

### Interface Types Seen

| Interface Type | Meaning |
|---|---|
| Ethernet | Normal physical switch port |
| Loopback | Virtual interface often used for management, routing, or stable device identity |
| VLAN | Layer 3 VLAN interface / SVI, often used as a gateway for a subnet |
| Virtual NIC | Software-defined or virtual interface, often tied to VMs, appliances, or logical services |
| Other | Auvik detected an interface but did not clearly classify it |
| Tunnel | Logical interface, possibly used for routing, VPN, overlay, or vendor-specific features |

### What VLAN Interfaces Mean

If the core switch shows many VLAN interfaces, it may be routing between internal networks. These are often called SVIs.

Example:

```text
VLAN 14 -> 10.30.14.1
VLAN 18 -> 10.30.18.3
```

Important interpretation:

> The core switch may be acting as the default gateway for multiple internal VLANs. If true, not all internal traffic goes through the firewall. Some traffic may route directly through the core switch.

### Blue Line Showing 6 Connections

Auvik showing a blue line with `6` likely means it grouped six physical or logical connections between devices.

One hover detail observed:

```text
6 connections
TwentyFiveGigE1/0/43 on UPPAJ35A-SWCORE-01.fs.local
```

This suggests a high-speed uplink.

| Part | Meaning |
|---|---|
| TwentyFiveGigE | 25-gigabit Ethernet |
| 1/0/43 | Cisco interface numbering |
| 6 connections | Multiple links grouped in the map |
| Core switch to another switch | Likely uplinks to downstream switch stack |

Possible explanations:

- Redundant uplinks.
- Port-channel / link aggregation.
- Trunk links carrying many VLANs.
- Multiple stack members connected upstream.
- Auvik grouping related physical/logical connections.

### High-Value Remarks

- The C9500 core switch is likely a critical internal dependency.
- It may route many VLANs and connect the firewall, access switches, Wi-Fi networks, and server/appliance subnets.
- The presence of many network labels means the core participates in multiple logical network segments.
- The `TwentyFiveGigE` uplinks suggest high-volume backbone connections, not normal user access ports.
- If there is only one core switch and no redundant peer, this could be a major single point of failure.

### Follow-Up Questions

1. Is there a second core switch for redundancy?
2. Are the 6 uplinks bundled into a port-channel?
3. Are uplinks split across redundant stack members or chassis?
4. Which VLANs have their gateway on the core switch?
5. Which VLANs route through the firewall instead?
6. Which downstream switch stacks connect to this core?
7. Are there interface errors or down uplinks?
8. Are the core configs backed up?
9. Is the C9500 firmware supported and current?
10. Is there a current VLAN/subnet inventory?

## Switch Stacks / Access Layer

### Device Summary

| Field | Value |
|---|---|
| Device Role | Access or distribution switch stack |
| Vendor / Model | Cisco Catalyst C9300-48UN |
| Stack Name Seen | USPAJ35A-SW.fs.local |
| Upstream Device | UPPAJ35A-SWCORE-01.fs.local |
| Uplink Type Seen | TwentyFiveGigE uplink to core |
| Example IPs Seen | 10.30.2.15, 10.30.4.15, 10.30.2.17, 10.30.4.17 |
| Interface Count Seen | About 360 interfaces |
| Interface Types Seen | Mostly Ethernet, plus tunnel/virtual/logical interfaces |
| Networks Seen | 10.30.0.0/24, HQ Supernet, Admin, Lobby, Vendor, Kitchen, WiFi, token-ring default, and others |

### Interpretation

The C9300 devices appear to be access or distribution switch stacks connected downstream from the core switch.

Likely flow:

```text
UPPAJ35A-SWCORE-01 Core Switch
  |
  v
Cisco C9300-48UN Switch Stack
  |
  +--> Desktops
  +--> Printers
  +--> Wireless access points
  +--> Phones
  +--> Cameras
  +--> Badge readers
  +--> Lobby devices
  +--> Vendor devices
  +--> Kitchen devices
```

### What A Switch Stack Means

A switch stack is multiple physical switches managed as one logical switch.

This explains the large interface count.

Example:

```text
48 ports x multiple stack members
+ uplink ports
+ VLAN interfaces
+ port-channels
+ tunnel/logical interfaces
= hundreds of interfaces
```

High-value interpretation:

> The approximately 360 interfaces suggest this object is likely a multi-member switch stack serving many physical endpoints and VLANs.

### Why The Same Networks Appear On Multiple Switches

It is normal for multiple switches to show the same VLAN or network labels.

This can mean:

- The switch carries that VLAN on a trunk.
- The switch has access ports assigned to that VLAN.
- The switch has devices connected in that subnet.
- The switch has an SVI or management IP in that network.
- Auvik associates the switch with networks it can see through neighbors.

Important distinction:

> Seeing a VLAN on a switch does not always mean that switch owns or routes the VLAN. It may only carry the VLAN to downstream devices.

### Network Labels

| Label | Possible Meaning | Questions |
|---|---|---|
| Admin | IT/admin user network or management network | Who can access it? Is it privileged? |
| Lobby | Front-desk, visitor, kiosk, or guest-facing network | Is it isolated from internal systems? |
| Vendor | Third-party or vendor-managed devices | Which vendors use it? What can it reach? |
| Kitchen | Facilities, IoT, displays, tablets, or appliances | Does it need internet-only access? |
| WiFi | Wireless users or access-point related network | Which SSID maps to this VLAN? |
| WiFi Admin | Admin wireless or wireless infrastructure network | Is access restricted? |
| HQ Supernet | Parent network grouping for HQ | What exact CIDR range does it represent? |
| Token-ring default | Likely legacy/default/discovery artifact | Confirm before treating as real dependency |

### High-Value Remarks

- The C9300 switch stacks likely represent the real-world access layer where users and devices connect.
- The multiple 25GbE uplinks back to the core suggest these stacks carry significant traffic.
- The stack likely serves multiple physical areas or device groups.
- Different switches can share many VLAN names while still serving different floors, closets, or device populations.
- The next useful step is to map each stack to a physical area, uplink ports, active VLANs, and downstream device types.

### Follow-Up Questions

1. Which building, floor, closet, or area does each C9300 stack serve?
2. How many physical members are in each stack?
3. Are the uplinks redundant?
4. Are the uplinks bundled as port-channels?
5. Which VLANs are carried versus actively used?
6. Which Wi-Fi SSIDs map to which VLANs?
7. Are vendor, lobby, kitchen, and guest-style networks isolated?
8. Are there interface errors, disabled ports, or down uplinks?
9. Are stack members on supported firmware?
10. Are stack configs backed up?

## Subnet: 10.5.0.0/20

### Observed Summary

| Field | Value |
|---|---|
| Subnet | 10.5.0.0/20 |
| Connected From | Core switch |
| Approximate Address Range | 10.5.0.0 through 10.5.15.255 |
| Size | About 4,096 addresses |
| Devices Seen | 9 devices, 14 devices in 10.5.2.x, 3 Auvik virtual appliances, 5 unknown devices |
| Example Unknown Device | Device@10.5.1.134 |

### Interpretation

`10.5.0.0/20` is a large private internal subnet. Because it connects from the core switch and contains Auvik virtual appliances plus multiple device groups, it may be an important infrastructure, server, monitoring, or mixed-use subnet.

Current view:

```text
10.5.0.0/20
  +--> 9 devices
  +--> 14 devices in 10.5.2.x
  +--> 3 Auvik virtual appliances
  +--> 5 unknown devices, including Device@10.5.1.134
```

### What Auvik Virtual Appliances Likely Mean

The Auvik virtual appliances are probably collectors used to discover and monitor the network.

They may perform:

- Subnet scanning.
- SNMP polling.
- API polling.
- Topology discovery.
- Alerting data collection.
- Sending monitoring data back to Auvik cloud.

High-value remark:

> The presence of 3 Auvik virtual appliances suggests this subnet is important for network visibility and may be part of the monitoring/discovery path.

### Unknown Devices

Devices named like `Device@10.5.1.134` usually mean Auvik sees an IP address but does not have a clean hostname, device type, vendor, or credentialed identity.

Possible causes:

- No DNS record.
- No SNMP/API credentials.
- Device blocks discovery.
- Stale/old endpoint.
- Printer, camera, IoT device, VM, appliance, or unmanaged server.
- Incomplete monitoring coverage.

High-value remark:

> Unknown devices on important subnets should be classified. They may be harmless, but they create visibility gaps.

### Follow-Up Questions

1. What is the business purpose of `10.5.0.0/20`?
2. Is this a server subnet, monitoring subnet, management subnet, user subnet, or mixed subnet?
3. What is the gateway IP for this subnet?
4. Is the gateway on the core switch?
5. Why are there 3 Auvik virtual appliances?
6. Which subnets does each Auvik collector monitor?
7. What are the unknown `Device@...` entries?
8. Are any domain controllers, DNS servers, file servers, or application servers in this subnet?
9. Does AWS or Azure connect to this subnet through VPN, Direct Connect, or ExpressRoute?
10. Is there a documented owner for this subnet?

## Internal Domain: fs.local

### Observed

The core and switches show hostnames under:

```text
fs.local
```

Examples:

```text
UPPAJ35A-SWCORE-01.fs.local
USPAJ35A-SW.fs.local
```

### Interpretation

`.local` usually indicates an internal/private domain name. In many environments, this means there may be on-prem Active Directory, internal DNS, internal certificates, file shares, printers, scripts, or legacy applications tied to internal naming.

This matters for cloud migration.

Simple explanation:

> `.local` can make full cloud migration harder because systems may depend on internal DNS names, on-prem Active Directory, local file shares, local authentication, internal routing, or applications that assume they are running inside the corporate network.

### Why This Can Block "Move Everything To Cloud"

Potential dependencies:

- Domain controllers.
- Internal DNS servers.
- File shares using paths tied to internal names.
- Apps configured to call servers like `server.fs.local`.
- Printers and scanners joined to local networks.
- Scripts using hardcoded internal hostnames.
- Certificates issued for internal names.
- Legacy systems that cannot easily run in cloud.
- VPN and routing assumptions.
- Identity integrations that depend on AD.

### High-Value Manager-Friendly Remark

> The presence of `fs.local` suggests internal DNS or Active Directory naming is in use. Before any major cloud migration, the team would need to map domain controllers, DNS dependencies, file shares, scripts, certificates, legacy apps, and systems referencing `.local` names.

## AWS / Azure View-Only Discovery Notes

Since access is view-only, the highest-value contribution is discovery, mapping, and documentation.

Things to inventory:

- AWS accounts and Azure subscriptions.
- Regions in use.
- VPCs and VNets.
- Subnets.
- Route tables.
- VPN gateways, Direct Connect, ExpressRoute, or site-to-site VPNs.
- Security groups and network security groups.
- EC2 instances and Azure VMs.
- RDS, Azure SQL, or other managed databases.
- S3 buckets and Azure storage accounts.
- Load balancers.
- IAM / Entra groups.
- CloudWatch / Azure Monitor.
- Backup configuration.
- Tags such as owner, environment, cost center, app, service, or business unit.

Questions to connect cloud back to on-prem:

1. Is there a VPN or private connection from AWS/Azure to HQ?
2. Which VPC/VNet routes point back to on-prem?
3. Are any cloud systems dependent on `fs.local` DNS?
4. Are there domain controllers or DNS forwarders in cloud?
5. Which cloud resources map to GitHub repos?
6. Which cloud resources have clear owners and tags?

## Egnyte Documentation Notes

Egnyte may contain the business and documentation reality. Do not move or delete anything during discovery.

Useful things to look for:

- Current network diagrams.
- Old network diagrams.
- Firewall documents.
- Vendor documents.
- Circuit/ISP contracts.
- Runbooks.
- Server inventories.
- Cloud diagrams.
- AWS/Azure notes.
- Change records.
- Onboarding docs.
- Files that may contain credentials and should be moved to a proper secret manager.

High-value documentation idea:

> Build a current-vs-stale documentation index that identifies active runbooks, old diagrams, missing owners, and duplicated/conflicting infrastructure notes.

## GitHub Repository Discovery Notes

Reading GitHub repositories can help explain what systems the company has, what apps exist, and what the team cares about.

For each repo, inspect:

- `README.md`
- `.github/workflows/`
- `Dockerfile`
- `docker-compose.yml`
- `terraform/`
- `infra/`
- `k8s/`
- `helm/`
- `scripts/`
- `Makefile`
- `CODEOWNERS`
- `.env.example`
- `package.json`, `go.mod`, `pyproject.toml`, or equivalent dependency files
- `docs/`

If there is no README, use this note format:

| Field | Notes |
|---|---|
| Repo |  |
| Purpose guessed from code |  |
| Language / framework |  |
| Deploy path |  |
| Infra files |  |
| Owners / CODEOWNERS |  |
| Cloud dependencies |  |
| On-prem dependencies |  |
| Risks |  |
| Questions |  |

High-value connection:

> GitHub can help map applications to infrastructure. A repo may reveal deploy targets, cloud services, environment variables, internal DNS names, databases, queues, storage buckets, CI/CD workflows, and owner teams.

## Current Risk / Opportunity Themes

### Possible Single Points Of Failure

- Is there only one Meraki firewall?
- Is there only one core switch?
- Are core-to-access uplinks redundant?
- Are access switch stacks split across redundant uplinks?

### Network Segmentation

- Are Lobby, Vendor, Kitchen, WiFi, and Admin networks isolated properly?
- Which networks can reach internal systems?
- Which traffic routes through the firewall versus the core switch?

### Visibility Gaps

- Unknown devices such as `Device@10.5.1.134` need classification.
- Some devices may lack DNS, SNMP, API credentials, or ownership metadata.
- VLAN names and subnet purposes may not be fully documented.

### Cloud Migration Dependencies

- `.local` indicates possible internal DNS/AD dependency.
- On-prem systems may depend on local identity, file shares, DNS, certificates, printers, appliances, or hardcoded hostnames.
- AWS/Azure view-only discovery should focus on identifying private connections and dependencies back to HQ.

### Documentation Gaps

- Egnyte may have current and stale documents mixed together.
- GitHub repos may lack READMEs or clear ownership.
- A unified inventory could connect Auvik devices, cloud resources, GitHub repos, owners, and docs.

## Suggested First Deliverable

Create a read-only hybrid infrastructure inventory with these columns:

| Category | Example |
|---|---|
| Asset name | USPAJ35A-FW01 |
| Asset type | Firewall, switch, subnet, cloud resource, repo |
| Platform | Auvik, AWS, Azure, GitHub, Egnyte |
| IP / CIDR | 10.30.240.1, 10.5.0.0/20 |
| Environment | HQ, prod, dev, shared, unknown |
| Owner | Team/person if known |
| Business purpose | Internet edge, core switching, Wi-Fi, vendor network |
| Dependencies | Upstream/downstream devices, cloud links, repos |
| Redundancy | HA pair, port-channel, backup, unknown |
| Documentation link | Egnyte/Confluence/GitHub link |
| Risk / gap | Unknown device, missing owner, stale docs |
| Next question | What needs to be confirmed |

## Manager-Friendly Summary

The current Auvik map suggests an HQ network where the internet/cloud edge connects into a Meraki MX450 firewall, which then connects into a Cisco C9500 core switch. The core switch appears to connect large internal subnets, including `10.5.0.0/20`, and downstream Cisco C9300 switch stacks that likely serve real-world office devices and VLANs such as Admin, Lobby, Vendor, Kitchen, and WiFi.

The presence of `fs.local` in device hostnames suggests internal DNS or Active Directory dependencies, which may be one reason a complete cloud migration would be difficult. Before proposing changes, a useful next step would be to build a read-only inventory mapping on-prem devices, VLANs/subnets, AWS/Azure resources, GitHub repositories, owners, and current documentation.

## Open Questions To Keep Updating

1. Is `USPAJ35A-FW01` paired with a secondary firewall?
2. What ISP circuits feed the Meraki firewall?
3. Does the Meraki firewall terminate VPNs to AWS, Azure, branches, or vendors?
4. Is `UPPAJ35A-SWCORE-01` the only core switch?
5. Which VLANs have gateways on the core switch?
6. Are the 6 blue connections to the access stack a port-channel?
7. Which physical areas do the C9300 switch stacks serve?
8. What is the purpose of `10.5.0.0/20`?
9. What are the unknown devices in `10.5.x.x`?
10. Which systems depend on `fs.local`?
11. Which AWS/Azure resources route back to on-prem?
12. Which GitHub repos map to which applications and infrastructure?
13. Which Egnyte docs are current versus stale?

## Core Switch vs Downstream Switches

### Simple Difference

| Switch Type | Plain-English Meaning | Typical Job |
|---|---|---|
| Core switch | The central internal traffic hub | Connects firewall, major subnets, access switch stacks, servers, Wi-Fi, and routing paths |
| Distribution switch | Middle layer between core and access | Aggregates multiple access switches or building/floor areas |
| Access switch | Where real devices plug in | Connects laptops, desktops, printers, phones, APs, cameras, badge readers, and appliances |
| Switch stack | Multiple physical switches acting like one switch | Gives one managed switch object with many ports/interfaces |

In this environment, the rough model appears to be:

```text
Firewall
  |
  v
Core switch
  |
  +--> Switch stack 1
  +--> Switch stack 2
  +--> Switch stack 3
  +--> Switch stack 4
  +--> Switch stack 5
  +--> Switch stack 6
```

The core switch is not important just because it has more ports. It is important because of its role. It sits higher in the topology and connects major network sections together.

The downstream switches may still be large and important. If they are C9300 stacks with about 360 interfaces, they likely serve a lot of real-world endpoints.

### Why The Downstream Switches Have Around 360 Interfaces

Seeing about 360 interfaces on several switches is normal if they are switch stacks.

A C9300-48UN has 48 access ports per physical switch, plus uplink ports. If several physical switches are stacked together, Auvik may show them as one logical device.

Example:

```text
Switch member 1: 48 ports
Switch member 2: 48 ports
Switch member 3: 48 ports
Switch member 4: 48 ports
Switch member 5: 48 ports
Switch member 6: 48 ports
Plus uplinks, VLAN interfaces, port-channels, loopbacks, tunnels, and virtual interfaces
```

This can easily produce hundreds of interfaces.

Important interpretation:

> Similar interface counts do not mean the switches use the same interfaces. It probably means each stack has a similar number of physical switch members and ports.

### Cisco Interface Names

Example:

```text
GigabitEthernet3/0/1
```

Breakdown:

| Part | Meaning |
|---|---|
| GigabitEthernet | 1-gigabit Ethernet interface |
| 3 | Stack member number |
| 0 | Module/subslot number, often 0 on fixed switches |
| 1 | Port number on that stack member |

So `GigabitEthernet3/0/1` usually means:

> Port 1 on stack member 3.

Another example:

```text
TwentyFiveGigE1/0/43
```

This usually means:

> A 25-gigabit port, likely used as an uplink, on stack member 1, port 43.

### Blue Lines And Overlap In Auvik

Blue lines in Auvik usually represent device connections. When many switches connect back to the core, the map can become visually messy because links overlap.

If a line shows a number like `6`, that usually means Auvik is grouping multiple connections into one visible line.

Possible meanings:

- Six physical links between two devices.
- Links bundled into a port-channel.
- Redundant uplinks.
- Trunk links carrying multiple VLANs.
- Multiple stack members connecting back to the core.

Do not rely only on the visual layout. The better evidence is the hover/click detail:

- Local interface name.
- Remote interface name.
- Link speed.
- Link status.
- Whether it is a trunk, access port, or port-channel.

### Can Multiple Switches Have The Same Networks?

Yes. This is very normal.

Multiple switches can show the same VLANs or networks because the same logical network may exist in many physical areas.

Example:

```text
Admin VLAN
  +--> carried on switch stack 1
  +--> carried on switch stack 2
  +--> carried on switch stack 3

WiFi VLAN
  +--> carried to access points across multiple closets/floors

Lobby VLAN
  +--> present only on switches near lobby devices
```

Important distinction:

| What Auvik Shows | What It Might Mean |
|---|---|
| VLAN/network appears on a switch | The switch carries that VLAN |
| Device IPs appear under that network | Devices on that switch are using that subnet |
| Switch has an IP in that subnet | It may have a management IP or VLAN interface |
| Switch has the gateway IP | It may be routing for that VLAN |
| VLAN appears on many switches | The VLAN is extended across the building |

So if several switches show `Admin`, `Lobby`, `Vendor`, `Kitchen`, or `WiFi`, that does not automatically mean they are duplicates. It may mean those VLANs are available in multiple places.

### What `10.30.2.0/24` Means

`10.30.2.0/24` is a subnet.

It includes addresses from:

```text
10.30.2.0 - 10.30.2.255
```

Common usable device range:

```text
10.30.2.1 - 10.30.2.254
```

Possible examples:

| IP | Possible Role |
|---|---|
| 10.30.2.1 | Default gateway for that subnet |
| 10.30.2.15 | Switch management IP |
| 10.30.2.17 | Another switch or stack management IP |
| 10.30.2.x | Devices in that subnet |

High-value note:

> When a switch has an IP like `10.30.2.15`, that may be the management address used to reach and monitor the switch. It does not necessarily mean the switch routes the whole `10.30.2.0/24` subnet.

### What `VLAN 4 Admin` Means

`VLAN 4 Admin` means VLAN ID 4 has the label/name `Admin`.

VLANs are logical network segments. They let the same physical switching infrastructure carry separate networks.

Example:

```text
VLAN 4 Admin
  |
  +--> Admin users or admin devices
  +--> Possibly management access
  +--> Could map to subnet 10.30.4.0/24, but confirm in Auvik or switch config
```

Do not assume VLAN 4 always equals `10.30.4.0/24`, but it often lines up that way in environments that use clean numbering. Confirm with the gateway/subnet shown in Auvik.

### What `Access VLAN 1 Default` Means

If an interface shows:

```text
GigabitEthernet3/0/1
Configuration: access vlan 1 default
```

That usually means this port is configured as an access port in VLAN 1.

Plain English:

> Anything plugged into this port is placed into VLAN 1 unless another configuration changes it.

Definitions:

| Term | Meaning |
|---|---|
| Access port | A port assigned to one VLAN, usually for an endpoint device |
| Trunk port | A port that carries multiple VLANs, usually between switches or to access points |
| VLAN 1 | Cisco default VLAN |
| Default | The port may still be on the default VLAN because it was never explicitly assigned |

Important judgment:

> Lots of active user/device ports in VLAN 1 can be a hygiene concern. VLAN 1 is the Cisco default and many teams prefer not to use it heavily for production endpoints or management.

But do not assume it is bad from one port. It may be:

- Unused.
- Shutdown.
- A default config on an empty port.
- A placeholder.
- A port that has not been cleaned up.
- A real endpoint port that should be reviewed.

The important follow-up is whether the port is active and what device is connected.

### Access Port vs Trunk Port

| Port Type | Carries | Common Use |
|---|---|---|
| Access port | One VLAN | Laptop, desktop, printer, phone, camera, appliance |
| Trunk port | Multiple VLANs | Switch-to-switch uplink, access point, virtualization host, firewall/core link |

If a port goes from an access switch to the core, it is usually a trunk or port-channel, because it needs to carry many VLANs back to the core.

If a port goes to a laptop/printer/camera, it is usually an access port.

### What To Capture For Each Downstream Switch

Use this format when clicking each switch under the core:

| Field | Notes |
|---|---|
| Switch name |  |
| Model |  |
| Role | Access stack / distribution stack / unknown |
| Upstream core interface |  |
| Local uplink interface |  |
| Number of grouped links |  |
| Interface count |  |
| Stack member count if visible |  |
| Management IPs |  |
| Networks/VLANs seen |  |
| Networks unique to this switch |  |
| Networks shared with other switches |  |
| Active alerts |  |
| Unknown connected devices |  |
| Physical area served |  |
| Questions |  |

### How To Make Judgment While Clicking Around

Ask these questions:

1. Is this switch upstream or downstream from the core?
2. Does it have endpoints connected, or is it mostly uplinks?
3. Are the uplinks high-speed and redundant?
4. Are the uplinks trunks or port-channels?
5. Which VLANs are present?
6. Which VLANs are actually active with devices?
7. Are any sensitive networks present, such as Admin, Vendor, or WiFi Admin?
8. Are there many ports still on VLAN 1?
9. Are the VLAN 1 ports active or unused?
10. Does the switch have alerts, interface errors, or down uplinks?

### Current Working Interpretation

The six switches below the core are likely switch stacks or distribution/access switches. They may have similar interface counts because each stack has a similar number of physical members and logical interfaces. They can also show the same VLANs because the same networks may be carried across many physical areas.

The useful next step is not to memorize every interface. The useful next step is to classify each switch by:

- Physical area served.
- Uplink back to core.
- VLANs/networks present.
- VLANs/networks unique to that switch.
- Whether it has active devices in sensitive VLANs.
- Whether uplinks are redundant.
- Whether many active ports are still on VLAN 1.

## Cisco Switch StackWise And StackPower Notes

### What The Stacking Diagram Means

A Cisco switch stack is multiple physical switches connected together so they behave like one logical switch.

Instead of managing five separate switches one-by-one, the network team can manage them as one stack:

```text
Switch stack
  +--> SW1
  +--> SW2
  +--> SW3
  +--> SW4
  +--> SW5
```

In Auvik or Cisco tools, this may appear as one switch object with hundreds of interfaces. That is why a stack of multiple 48-port switches can show around 360 interfaces.

### StackWise Ring

`StackWise` is Cisco's switch stacking technology. It connects the switches together for data/control-plane stacking.

If the diagram shows:

```text
SW1 -> SW2 -> SW3 -> SW4 -> SW5 -> back to SW1
```

that is a StackWise ring.

Plain English:

> StackWise lets multiple physical switches operate as one logical switch, with one stack master/control plane and shared management.

Why the ring matters:

- The switches act like one managed unit.
- Ports are named by stack member, such as `GigabitEthernet3/0/1`.
- If one stack cable/link fails, traffic/control may still go the other way around the ring.
- If the full ring breaks in more than one place, the stack can split or lose redundancy.
- A healthy full ring is better than a half-ring or broken-ring condition.

Example interface meaning:

```text
GigabitEthernet3/0/1
```

| Part | Meaning |
|---|---|
| `GigabitEthernet` | 1Gb Ethernet port |
| `3` | Switch stack member 3 |
| `0` | Module/subslot |
| `1` | Port 1 on that switch member |

So if a device is connected to `GigabitEthernet3/0/1`, it is physically plugged into stack member 3, port 1.

### StackPower Ring

`StackPower` is separate from StackWise.

StackWise is about making switches act like one logical switch.

StackPower is about sharing power between switches in the stack.

Plain English:

> StackPower allows switches in the stack to share power resources, so one switch may help provide power to another if a power supply fails or if power is pooled.

A StackPower ring may look like:

```text
SW1 StackPower -> SW2 StackPower -> SW3 StackPower -> SW4 StackPower -> SW5 StackPower -> back to SW1
```

Why it matters:

- Power can be pooled or shared across stack members.
- It can provide extra resiliency if one power supply fails.
- It helps support PoE devices like phones, wireless APs, cameras, and badge readers.
- A broken StackPower ring may reduce power redundancy.
- If the stack powers many PoE devices, power design matters a lot.

### Power Supplies, PDUs, And Redundancy

The diagram showing power supply connections to `PDU A` and `PDU B` is about electrical redundancy.

Terms:

| Term | Meaning |
|---|---|
| PS | Power supply inside a switch |
| PDU | Power Distribution Unit, usually in the network rack |
| PDU A | One power path/source |
| PDU B | Another power path/source |
| StackPower | Power-sharing cable between switches |

Example from the diagram:

```text
SW1 PS -> PDU A
SW2 PS -> PDU B
SW1 StackPower -> SW2
SW2 StackPower -> SW1
```

This means the switches may be intentionally split across two power sources.

High-value interpretation:

> If switch power supplies are split between PDU A and PDU B, the stack may survive the loss of one PDU or one power circuit, depending on power load and StackPower configuration.

### StackWise vs StackPower

| Feature | Purpose | What It Protects Against |
|---|---|---|
| StackWise ring | Makes switches act like one logical switch | Management/control/data-path stacking failure |
| StackPower ring | Shares power between switches | Some power supply or PDU failures |
| Dual PDUs | Separate electrical feeds | Loss of one PDU, circuit, UPS, or power path |

These are related but not the same thing.

Simple version:

```text
StackWise = how the switches think/talk as one switch
StackPower = how the switches share power
PDU A/B = where the electricity comes from
```

### Why This Is Important For Real-World Reliability

A switch stack may look like one switch in Auvik, but physically it is multiple boxes. Reliability depends on more than just the network uplinks.

Important things to check:

- Is the StackWise ring complete?
- Are all stack members present and healthy?
- Which switch is the active/master switch?
- Is there a standby member?
- Are StackWise cables connected in a full ring?
- Is StackPower connected in a full ring?
- Are power supplies split across PDU A and PDU B?
- Are both PDUs backed by UPS/generator power?
- Are PoE loads low enough to survive one power failure?
- Are uplinks split across different stack members?

### What Could Go Wrong

Potential issues:

- StackWise ring broken: stack may still work but has less redundancy.
- StackPower ring broken: power sharing may be reduced.
- All power supplies plugged into only PDU A: PDU A failure could take down the stack.
- Uplinks only on one stack member: that member failing could isolate the whole stack.
- Too many PoE devices: losing one power source could force APs/phones/cameras offline.
- Stack member mismatch: different firmware/hardware states can create instability.

### High-Value Observation To Write In Confluence

> The downstream Cisco switch stacks appear to use StackWise ring connections for logical switch stacking and StackPower ring connections for power sharing. This means each stack may operate as one managed switch while being physically made of multiple switch members. The power diagram showing `PDU A` and `PDU B` suggests the design may be intended for power redundancy. Key items to verify are StackWise ring health, StackPower ring health, power supply distribution across PDUs, PoE load, and whether uplinks to the core are spread across different stack members.

### Questions To Ask The Network Team

1. Is the StackWise ring complete and healthy on each C9300 stack?
2. Is StackPower enabled and configured in redundant or power-sharing mode?
3. Are switch power supplies split between PDU A and PDU B?
4. Are PDU A and PDU B backed by separate UPS/circuits?
5. What happens to PoE devices if one PDU fails?
6. Which switch member is active/master?
7. Is there a standby stack member?
8. Are uplinks to the core spread across multiple stack members?
9. Are any stack members missing, mismatched, or reporting errors?
10. Is stack health monitored in Auvik or another tool?

## Infrastructure Code And Operational Engineering

### Key Mental Shift

Do not think of infrastructure as only:

```text
Move servers to AWS
```

That is only one slice.

A better definition:

> Infrastructure engineering means making systems run safely, reliably, securely, observably, and repeatably.

Cloud is just one place systems can run. A system can run on-prem, in AWS, in Azure, in Docker, on a VM, in SaaS, or across all of those at once.

Infrastructure includes both the real environment and the code/configuration that operates it.

```text
Physical/logical infra:
  Firewalls, switches, VLANs, servers, cloud accounts, storage, DNS, identity

Infrastructure code:
  Docker Compose, Terraform, CI/CD, scripts, monitoring config, runbooks, backups, audits
```

The useful question is not only:

```text
Can this move to cloud?
```

The better questions are:

```text
Can we understand it?
Can we rebuild it?
Can we monitor it?
Can we secure it?
Can we recover it?
Can we operate it without guessing?
```

### What Infrastructure Engineering Usually Covers

| Area | What It Means | Examples |
|---|---|---|
| System administration | Operating servers and services | Linux, Windows, patching, services, users, disk, processes |
| Networking | How systems connect | Firewalls, switches, VLANs, VPNs, DNS, subnets, routing |
| Cloud | Cloud resources and accounts | AWS/Azure accounts, VPCs, IAM, EC2/VMs, RDS, S3, VNets |
| Infrastructure as code | Repeatable environment definition | Terraform, CloudFormation, Bicep, Helm, Kubernetes YAML |
| Runtime configuration | How apps start and connect | Docker Compose, env vars, ports, volumes, health checks |
| Security | Preventing unsafe access/exposure | secrets, IAM, segmentation, public ports, patching |
| Observability | Knowing what is happening | logs, metrics, alerts, dashboards, traces, uptime checks |
| Automation | Reducing manual work | Bash, Python, PowerShell, scheduled jobs, CI/CD checks |
| Deployment safety | Shipping without guessing | tests, health checks, rollback, backups, release gates |
| Documentation | Making operations clear | runbooks, diagrams, ownership maps, inventories |
| Support | Handling real incidents | tickets, outage response, incident snapshots, root cause notes |
| Cost/risk | Reducing waste and exposure | unused resources, stale systems, old docs, over-permissioned access |

### The Universal Infra Reading Loop

Use this order in almost any infrastructure situation:

1. Inventory

   What exists? Repos, servers, switches, firewalls, databases, cloud resources, queues, docs, dashboards.

2. Ownership

   Who owns it? Which team, repo, vendor, project board, business function, or manager?

3. Runtime

   Where does it run? Laptop, Docker, VM, AWS, Azure, SaaS, on-prem, or hybrid?

4. Dependencies

   What does it need? Database, cache, queue, DNS, identity, storage, API, network route, firewall rule.

5. Health

   How do we know it works? Health checks, logs, dashboards, metrics, alerts, smoke tests.

6. Failure

   What breaks if it dies? Who notices? Who responds? Is there a runbook or rollback?

7. Risk

   What is exposed, old, manual, undocumented, unmonitored, over-permissioned, or fragile?

8. Improve

   What is the smallest safe improvement backed by evidence?

That loop applies to Auvik devices, AWS resources, GitHub repos, Docker services, and internal documentation.

### Why Infrastructure Code Matters

Infrastructure code is high value because it tells you how systems are actually intended to run.

In a repo, infra code can answer:

- What services exist?
- What ports are exposed?
- What depends on what?
- What data is persisted?
- What secrets/config are required?
- What health checks exist?
- What CI/CD checks run before merge/deploy?
- What monitoring exists?
- What backup/restore path exists?
- What would break if a dependency went down?

Infrastructure code is often closer to reality than a stale diagram because it is what developers and deployment systems actually use.

### Repo Examples From This Project

This Shopify project already has several useful infrastructure-code surfaces.

| Repo Path | What It Teaches |
|---|---|
| `docker-compose.yml` | Local NexusOS-style runtime: Postgres/pgvector, Redis, Qdrant, Zookeeper, Kafka, Ollama, Temporal, Temporal UI |
| `Pokemon/docker-compose.yml` | Pokemon app runtime: Postgres, Redis, RabbitMQ, PokeTCG service, Go server, Python consumers, analytics, scraper, React client |
| `Pokemon/docker-compose.prod.yml` | Production-style runtime differences worth comparing against local compose |
| `Pokemon/docker-compose.local-no-postgres-port.yml` | Example of reducing local host port exposure |
| `Pokemon/prometheus.yml` | Monitoring configuration surface |
| `Pokemon/promtail-config.yaml` | Log shipping / log collection configuration surface |
| `Pokemon/server/Dockerfile` | How the Go backend is built and packaged |
| `Pokemon/client/Dockerfile` | How the frontend is built and served |
| `.github/workflows/ci.yml` | CI pipeline and merge safety checks |
| `infra/scripts/aws/05_inventory.py` | Read-only AWS inventory script pattern |
| `infra/scripts/aws/company_repo_discovery.py` | Read-only repo discovery script pattern |
| `infra/scripts/security/01_secrets_auditor.py` | Security audit practice surface |
| `infra/scripts/network/01_port_scanner.py` | Network exposure / port discovery practice surface |
| `infra/scripts/linux/03_storage_audit.py` | Server/storage audit practice surface |

### Example: Reading The Root `docker-compose.yml`

The root compose file defines a local service stack:

```text
postgres  -> database with pgvector
redis     -> cache/session/idempotency-style storage
qdrant    -> vector database for RAG/memory
zookeeper -> Kafka dependency
kafka     -> event streaming / webhook buffering
ollama    -> local AI model runtime
temporal  -> workflow engine
temporal-ui -> workflow UI
```

Infra interpretation:

- The project is not just one app. It is a multi-service platform.
- Postgres, Redis, Qdrant, Kafka, and Temporal are operational dependencies.
- Health checks exist for several services, which is good infra hygiene.
- Several services expose host ports like `5432`, `6379`, `6333`, `9092`, `11434`, `7233`, and `8088`.
- Exposed local ports are useful for development but should be reviewed before any production-style deployment.
- Volumes such as `postgres_data`, `redis_data`, `qdrant_data`, `kafka_data`, and `ollama_data` represent persistent state.

Good infra questions:

1. Which of these services are required in production?
2. Which are local-only developer tools?
3. Which ports should be bound to localhost only?
4. Which services need backups?
5. Which services need dashboards and alerts?
6. What is the startup order and failure behavior?
7. What happens if Kafka, Redis, Qdrant, or Temporal is down?

### Example: Reading `Pokemon/docker-compose.yml`

The Pokemon app compose file shows a more application-like stack:

```text
postgres          -> main database
redis             -> cache
rabbitmq          -> message queue
poketcg           -> internal price lookup API
server            -> Go API gateway
api-consumer      -> Python ingestion worker
analytics-engine  -> Python analytics worker
scraping-service  -> optional browser scraping worker
client            -> React frontend
```

Infra interpretation:

- The app is service-oriented, not just a single backend.
- `depends_on` with health checks shows dependency order.
- RabbitMQ is a critical queue dependency between producer/consumer-style services.
- Some ports are bound to `127.0.0.1`, which is safer than exposing them on all interfaces.
- The Go server uses `.env`, which means config/secrets handling matters.
- The scraper uses Playwright/browser dependencies, which can affect CPU, memory, disk, and container image size.

Good infra questions:

1. Are all required services covered by health checks?
2. Are any sensitive ports exposed beyond localhost?
3. Are default credentials like `guest/guest` only for local development?
4. Are Postgres and RabbitMQ backed up?
5. What logs would show a failed ingestion job?
6. What alert would fire if the API consumer stopped working?
7. Can the app recover if RabbitMQ or Redis restarts?

### High-Value Tasks You Can Do In This Repo

These are practical tasks that map directly to real infrastructure engineering.

| Task | Why It Matters | Repo Example |
|---|---|---|
| Runtime architecture map | Turns compose files into a system diagram | Map root `docker-compose.yml` and `Pokemon/docker-compose.yml` services/dependencies |
| Port exposure audit | Finds services exposed to host/network | Compare `ports:` mappings across compose files |
| Health/readiness report | Shows whether services are actually operational | Check compose health checks and add a script that summarizes status |
| Secrets/config audit | Finds unsafe defaults and missing `.env.example` coverage | Review `env_file`, environment variables, CI secrets, compose defaults |
| Backup/restore drill | Proves data can be recovered | Backup Postgres volume and restore into a test container |
| Observability inventory | Finds logging/metrics gaps | Review `prometheus.yml`, `promtail-config.yaml`, app logs, health endpoints |
| Incident snapshot script | Captures evidence quickly during debugging | One script collects `docker ps`, recent logs, ports, disk, memory, git commit |
| CI/deploy guard | Prevents unsafe changes from merging | Extend `.github/workflows/ci.yml` with lint/test/secret/config checks |
| Repo discovery report | Builds onboarding visibility | Run or improve `infra/scripts/aws/company_repo_discovery.py` |
| AWS read-only inventory | Practices safe cloud discovery | Run or improve `infra/scripts/aws/05_inventory.py` |

### Concrete Task Backlog For Practice

Do these in order.

1. Create a runtime architecture markdown page

   Output:

   ```text
   service -> purpose -> depends_on -> ports -> volumes -> healthcheck -> risk/questions
   ```

   Use:

   ```text
   docker-compose.yml
   Pokemon/docker-compose.yml
   Pokemon/docker-compose.prod.yml
   ```

2. Create a Docker Compose port exposure audit

   Goal:

   ```text
   List every service with a host port mapping and classify it as localhost-only, public bind, internal-only, or unknown.
   ```

   Example findings to look for:

   ```text
   5432:5432          -> exposed on all interfaces unless restricted by Docker/host firewall
   127.0.0.1:5432:5432 -> localhost-only, safer for development
   expose: 8765       -> internal Docker network only
   ```

3. Create a health/readiness checker

   Goal:

   ```text
   One command reports healthy/unhealthy for Postgres, Redis, RabbitMQ, Qdrant, Kafka, Temporal, API, frontend.
   ```

   Output format:

   ```text
   service | status | check | notes
   ```

4. Create a secrets/config inventory

   Goal:

   ```text
   List required environment variables, where they are referenced, whether defaults exist, and whether defaults are safe.
   ```

   Pay attention to:

   ```text
   POSTGRES_PASSWORD defaults
   RabbitMQ guest/guest defaults
   env_file: .env
   GitHub Actions secrets
   API keys used by ingestion/scraping services
   ```

5. Create a backup/restore runbook

   Goal:

   ```text
   Prove Postgres can be backed up and restored into a test container.
   ```

   A real infra person does not only say backups exist. They prove restore works.

6. Create an incident snapshot script

   Goal:

   ```text
   One command captures enough evidence to debug without guessing.
   ```

   Capture:

   ```text
   git commit
   docker compose ps
   unhealthy containers
   last 100 lines of logs for key services
   listening ports
   disk usage
   memory usage
   recent restart counts
   health endpoint results
   ```

7. Create a CI safety checklist

   Goal:

   ```text
   Before merge/deploy, run tests, secret scan, compose validation, config audit, and basic health checks.
   ```

8. Improve AWS read-only inventory

   Existing script:

   ```text
   infra/scripts/aws/05_inventory.py
   ```

   Current coverage:

   ```text
   STS caller identity
   EC2 instances
   RDS instances
   S3 buckets
   CloudWatch log groups
   ```

   Future improvements:

   ```text
   VPCs
   subnets
   route tables
   NAT gateways
   internet gateways
   VPN gateways
   security groups
   load balancers
   EBS volumes/snapshots
   backup vaults
   tag hygiene
   public exposure flags
   ```

9. Improve repo discovery

   Existing script:

   ```text
   infra/scripts/aws/company_repo_discovery.py
   ```

   Future improvements:

   ```text
   Summarize repo purpose from files found
   detect missing README/CODEOWNERS
   detect CI/no CI
   detect Docker/Terraform/Kubernetes usage
   detect likely deploy path
   output Markdown inventory
   ```

10. Write runbooks

   Start with:

   ```text
   API down
   database restore
   queue backlog
   Redis unavailable
   failed deploy rollback
   disk full
   bad environment variable/config
   ```

### What To Do At Future Standard

At work, do the same thing, but read-only first.

Do not start by saying:

```text
We should migrate everything to AWS.
We should replace Auvik.
We should automate firewall changes with AI.
We should refactor all repos.
```

Start with evidence.

Ask:

1. What are the main systems Infrastructure supports?
2. Which tools are the source of truth: Auvik, Egnyte, GitHub, AWS, Azure, Jira/GitHub Projects?
3. Which repos should I study first?
4. Which AWS accounts and Azure subscriptions are production vs dev?
5. Where are runbooks and diagrams?
6. Where are alerts and dashboards?
7. What work repeats every week?
8. What is currently painful: access, monitoring, deployments, old docs, cloud cost, network issues, tickets?

Use this note format for each real system:

| Field | Notes |
|---|---|
| System |  |
| Business purpose |  |
| Owner/team |  |
| Where it runs | On-prem, AWS, Azure, SaaS, Docker, VM, unknown |
| Repo(s) |  |
| Cloud resources |  |
| Network dependencies | VLANs, firewall, DNS, VPN, subnet |
| Data dependencies | DB, storage, queue, cache |
| Identity/access | AD, Entra, IAM, SSO, service accounts |
| Monitoring | Dashboards, logs, alerts |
| Runbook |  |
| Known risks |  |
| Open questions |  |
| Small improvement idea |  |

### Future Standard: Safe First Ideas

Good first ideas:

- Hybrid infrastructure inventory: Auvik + AWS + Azure + GitHub + Egnyte.
- Critical device ownership map: firewall, core switch, access stacks, Auvik collectors.
- Repo ownership and deploy-path inventory.
- Runbook index: current vs stale docs.
- Monitoring gap list.
- Cloud tagging hygiene review.
- Read-only AWS/Azure inventory.
- GitHub access/team map.
- Incident snapshot template.
- AI use-case register for infra, focused on low-risk internal support.

The goal is to become the person who can say:

> Here is what we have, here is what depends on what, here is what is unclear, here is where the risk is, and here is the smallest safe improvement.

### How To Think When Coding Infra Tools

Before writing a script, answer these questions:

1. What question should this script answer?
2. What system has that answer?
3. What API, file, or command gives me the data?
4. Can I read it safely without changing anything?
5. Can I output JSON or Markdown?
6. Can I fail clearly with a useful error?

Example 1:

| Step | Answer |
|---|---|
| Question | Which AWS account am I using? |
| System | AWS STS |
| API | `get_caller_identity` |
| Script | `infra/scripts/aws/01_identity_check.py` or `05_inventory.py` |
| Output | Account, ARN, user ID, profile, region |

Example 2:

| Step | Answer |
|---|---|
| Question | Which services expose public ports locally? |
| System | Docker Compose files |
| Data | `ports:` mappings |
| Script idea | `docker_compose_security_audit.py` |
| Output | Service, host port, bind address, risk, recommendation |

Example 3:

| Step | Answer |
|---|---|
| Question | Which repos lack basic ownership/deploy documentation? |
| System | GitHub/local repo checkout |
| Data | README, CODEOWNERS, workflows, Dockerfile, compose, terraform, docs |
| Script | `infra/scripts/aws/company_repo_discovery.py` |
| Output | Repo signals, missing docs, next questions |

### Future Standard Personal Standard

Use this standard for your own work:

```text
Inventory before opinion.
Evidence before proposal.
Read-only before change.
Small improvement before big migration.
Runbook before tribal knowledge.
Restore test before claiming backups.
Health check before claiming uptime.
Owner map before asking for broad access.
```

Main mental shift:

> Do not ask, "What feature can I build?" Ask, "What operational risk can I reduce, what manual process can I automate, what unknown can I turn into an inventory, and what failure can I detect earlier?"
EOF

## fs.local And Why Full Cloud Migration Is Hard

### What `fs.local` Probably Means

When device names appear like this:

```text
UPPAJ35A-SWCORE-01.fs.local
USPAJ35A-SW.fs.local
```

`fs.local` is probably an internal/private DNS domain. In many company environments, this is tied to on-prem Active Directory and internal DNS.

Simple interpretation:

```text
fs.local = internal company DNS / Active Directory namespace
```

This means internal systems may be known by names such as:

```text
dc01.fs.local
fileserver01.fs.local
printer01.fs.local
app-db.fs.local
legacyapp01.fs.local
```

Those names usually only resolve correctly when a device is on the company network, connected to VPN, or using company DNS servers.

### Why `.local` Can Make Full Cloud Migration Hard

A full cloud move is not just moving servers from a building into AWS or Azure.

If systems depend on `fs.local`, then the company may also need to redesign or migrate:

- Internal DNS.
- Active Directory domain controllers.
- User and computer authentication.
- Group Policy or device management.
- File shares and mapped drives.
- Printer/scanner paths.
- Internal certificates.
- Legacy application configs.
- Scripts with hardcoded hostnames.
- Firewall rules and routing paths.
- VPN/cloud connectivity back to on-prem.

The hard part is hidden dependency discovery.

Example:

```text
A server can be moved to AWS.
But if the app still calls db01.fs.local, authenticates with on-prem AD,
reads files from \\fileserver01.fs.local\share, and depends on an internal
DNS server, then the migration is not complete.
```

### Common Hidden Dependencies

| Dependency | Why It Matters |
|---|---|
| Domain controllers | Users, computers, and services may authenticate against on-prem AD |
| Internal DNS | Apps and devices may only resolve `*.fs.local` inside the corporate network |
| File shares | Business workflows may depend on paths like `\\server.fs.local\share` |
| Legacy apps | Apps may have hardcoded `.local` database/API/file paths |
| Certificates | Internal certs may be issued for `.local` names |
| Printers/scanners | Office devices may depend on local DNS, VLANs, or print servers |
| Scripts | Old PowerShell/Bash/batch jobs may reference `.local` hosts directly |
| VPN routing | Cloud systems may need a tunnel back to on-prem to reach `fs.local` resources |
| Identity integrations | SaaS/cloud apps may sync users/groups from on-prem AD |

### Why Your Manager Said This Matters

When your manager says it is hard to go completely cloud because of `.local`, they probably mean:

> Too many systems still assume the internal network, internal DNS, and on-prem identity environment exist.

That does not mean cloud migration is impossible. It means the team needs a dependency map before making claims about moving everything.

The cloud migration question becomes:

```text
What depends on fs.local?
Can that dependency be removed, migrated, bridged, or replaced?
```

### What To Investigate Read-Only

Use this as a discovery checklist:

1. Where are the `fs.local` DNS servers?
2. Where are the domain controllers?
3. Are AWS or Azure resources configured to resolve `fs.local` names?
4. Are there DNS forwarders from cloud to on-prem?
5. Are there VPN, Direct Connect, or ExpressRoute routes back to `fs.local` systems?
6. Which GitHub repos reference `.local` hostnames in config, docs, scripts, or examples?
7. Which Egnyte docs mention `fs.local`, domain controllers, file shares, or legacy apps?
8. Which systems use mapped drives like `\\server.fs.local\share`?
9. Are internal certificates issued for `.local` names?
10. Which apps would break if the VPN or on-prem DNS went down?

### Practical Search Examples For GitHub Repos

In a local repo checkout, search for internal-domain references:

```bash
rg -n "fs\.local|\.local|ldap|domain controller|dns|\\\\|fileshare|file share|SMB|Active Directory|AD" .
```

Search common config surfaces:

```bash
rg -n "fs\.local|\.local" README.md docs/ scripts/ config/ .github/ infra/ terraform/ k8s/ helm/ 2>/dev/null
```

Things to capture:

| Field | Notes |
|---|---|
| Repo/file | Where the `.local` reference appears |
| Hostname | Example: `db01.fs.local` |
| Purpose | DB, file share, LDAP, API, printer, script, unknown |
| Runtime dependency | Does the app need this at startup/runtime? |
| Migration impact | Must migrate, replace, tunnel, or remove dependency |
| Owner/question | Who can confirm this? |

### High-Value Confluence Remark

> `fs.local` appears to be an internal DNS/Active Directory namespace. This is a potential cloud-migration dependency because applications, servers, scripts, file shares, certificates, printers, and identity flows may rely on names that only resolve inside the corporate network. A safe first step is a read-only dependency inventory of all `fs.local` references across Auvik, DNS, AWS/Azure networking, GitHub repos, Egnyte docs, and known runbooks.

## Where To Start: AWS, Python, Security, Observability, And IaC

### The Correct Frame

Do not treat this project as only an app project.

Treat it like a practice company environment.

Your focus is:

```text
AWS + Python/boto3 + security + observability + infrastructure as code
```

So the job is not to start by building random app features. The job is to learn how to inspect, secure, monitor, and eventually define infrastructure repeatably.

Better framing:

```text
What exists?
Is it secure?
Is it observable?
Can I inventory it?
Can I detect risk?
Can I turn it into repeatable infrastructure?
```

That is the same kind of thinking needed for Future Standard.

### What This Project Represents

In this project, think of the system like this:

```text
PokemonTool = product intelligence / internal business app
Odoo = storefront, ERP, inventory, orders, CRM, business workflow
Postgres = source of truth / persistent data
Redis/RabbitMQ = runtime dependencies
Docker Compose = current local infrastructure
AWS = future hosting, discovery, security, and inventory practice layer
GitHub Actions = CI/CD and deployment safety
Python scripts = infrastructure automation tools
Terraform/IaC = repeatable cloud infrastructure definition
```

At Future Standard, the equivalent could be:

```text
Business application
Database
Queues/caches
Internal network
Cloud account
Monitoring
GitHub repos
CI/CD
Runbooks
Security controls
```

So this repo is a lab for building the same patterns safely.

### Start With Inventory Automation

Start with inventory before Terraform, dashboards, migration, or advanced automation.

Reason:

> Infrastructure people need to know what exists before they suggest changes.

First coding project:

```text
infra/scripts/local/compose_inventory.py
```

Purpose:

```text
Generate a Markdown/JSON report of the project infrastructure from local repo files.
```

Read these files first:

```text
docker-compose.yml
docker-compose.odoo.yml
Pokemon/docker-compose.yml
Pokemon/docker-compose.prod.yml
Pokemon/docker-compose.local-no-postgres-port.yml
.github/workflows/ci.yml
odoo/config/odoo.conf
odoo/.env.example
```

Report these fields:

| Field | Meaning |
|---|---|
| Service | Service/container name |
| Runtime | Docker image or build context |
| Ports | Host/container port mappings |
| Expose | Internal-only Docker ports |
| Depends on | Service dependencies |
| Volumes | Persistent data or mounted config/code |
| Networks | Docker networks used |
| Healthcheck | Whether a healthcheck exists |
| Env vars | Required or default configuration |
| Risk notes | Public ports, defaults, missing healthchecks, missing owner |

Example output:

```text
Service: odoo
Runtime: Docker image odoo:19.0
Ports: 127.0.0.1:8069 -> 8069
Depends on: odoo-db
Data: odoo_data volume
Healthcheck: not obvious on odoo service
Risk: dev password defaults, no public exposure, needs backup/restore plan
```

This teaches the most important infra skill:

> Turn messy systems into structured understanding.

### Then Add AWS/boto3 Inventory

After local inventory, build the cloud version:

```text
infra/scripts/aws/aws_inventory_report.py
```

Use boto3 in read-only mode.

Start with:

```text
STS caller identity
EC2 instances
RDS instances
S3 buckets
VPCs
subnets
route tables
security groups
CloudWatch log groups
IAM roles
resource tags
```

Output:

```text
Account
Region
Resource type
Name
ID
Public/private status
Tags
Risk notes
Questions
```

Future Standard equivalent:

> I can safely inventory AWS resources and produce a readable report without changing anything.

That is useful real infrastructure work.

### Then Build Security Audits

Once you can inventory, add security checks.

Local security script:

```text
infra/scripts/local/docker_security_audit.py
```

Check:

```text
ports bound to 0.0.0.0
ports exposed to localhost only
services with no healthcheck
default passwords
missing .env.example coverage
secrets hardcoded in compose/config files
persistent volumes with no backup note
containers likely running as root
admin UIs exposed locally
```

AWS security script:

```text
infra/scripts/aws/aws_security_audit.py
```

Check:

```text
security groups open to 0.0.0.0/0
public EC2 IPs
public RDS instances
S3 public access settings
IAM admin policies
CloudWatch log retention missing
unencrypted volumes/snapshots
untagged resources
internet gateways and public subnets
```

Security intuition questions:

```text
What is exposed?
Who can access it?
Is it encrypted?
Is it monitored?
Is it tagged and owned?
Is the default config still present?
```

### Then Build Observability Audits

After security, inspect observability.

Local observability script:

```text
infra/scripts/local/observability_inventory.py
```

Check:

```text
healthchecks in compose
Prometheus config
Grafana presence
Loki/Promtail config
log files or stdout logging
service dashboards
alert rules
critical services without healthchecks
```

AWS observability script:

```text
infra/scripts/aws/aws_observability_audit.py
```

Check:

```text
CloudWatch log groups
log retention days
CloudWatch alarms
dashboards
RDS monitoring
EC2 status checks
load balancer logs
missing metrics/alerts
```

Future Standard equivalent:

> I can tell which systems have logs/alerts and which systems are blind spots.

### Then Start Infrastructure As Code

Do not start with a huge migration.

Start with a small Terraform lab:

```text
infra/terraform/aws_odoo_sandbox/
```

First Terraform target:

```text
VPC
public subnet
private subnet
route tables
security groups
CloudWatch log group
tags
placeholder EC2 or ECS target
placeholder RDS design note
```

Goal:

```text
Can I describe infrastructure repeatably?
Can I tag it?
Can I secure it?
Can I explain the network?
Can I destroy/recreate it safely?
```

Do not try to deploy the full app on day one.

### Actual Roadmap

Follow this order:

1. Local compose inventory script
2. Local security audit script
3. Local observability audit script
4. AWS boto3 identity and inventory script
5. AWS security audit script
6. AWS observability audit script
7. Terraform mini-lab for AWS network/security baseline
8. Runbook generator from findings

This sequence builds intuition in the right order:

```text
Inventory -> Security -> Observability -> IaC -> Runbooks
```

### How To Think Before Coding Any Infra Tool

Before writing a script, answer:

```text
Question:
What am I trying to answer?

Source:
Where does the truth live?

Read-only method:
How can I inspect it safely?

Output:
Should this be JSON, Markdown, or a table?

Risk:
What would a manager or infra team care about?

Next action:
What should someone do with this information?
```

Example 1:

```text
Question: Which services expose ports?
Source: docker-compose files
Read-only method: parse YAML
Output: Markdown table
Risk: public DB/admin ports
Next action: bind to 127.0.0.1 or make internal-only
```

Example 2:

```text
Question: Which AWS account am I using?
Source: AWS STS
Read-only method: boto3 get_caller_identity
Output: account, ARN, user ID, profile, region
Risk: running scripts in the wrong account
Next action: confirm account/role before inventory or audit
```

Example 3:

```text
Question: Which services lack healthchecks?
Source: docker-compose files
Read-only method: parse service healthcheck blocks
Output: service, has_healthcheck, dependency criticality, recommendation
Risk: failures are not detected early
Next action: add healthcheck or monitor externally
```

### First Thing To Code Yourself

Start here:

```text
infra/scripts/local/compose_inventory.py
```

Requirements:

```text
Reads docker-compose.yml, docker-compose.odoo.yml, and Pokemon/docker-compose.yml
Parses YAML safely
Outputs Markdown by default
Optionally outputs JSON
Lists service, image/build, ports, expose, depends_on, volumes, healthcheck, networks
Adds simple risk notes
Does not modify files or call external services
Fails clearly if a file is missing or invalid
```

This one script connects:

```text
Python
infrastructure inventory
security thinking
observability thinking
Future Standard-style repo analysis
```

After that, build the boto3 AWS inventory version.

### Personal Standard

Use this standard:

```text
Inventory before opinion.
Evidence before proposal.
Read-only before change.
Small improvement before big migration.
Healthcheck before claiming uptime.
Restore test before claiming backups.
Owner map before asking for broad access.
Security/observability before production exposure.
IaC after understanding the existing runtime.
```

Main mental shift:

> Do not ask, "What app feature can I build?" Ask, "What operational risk can I reduce, what unknown can I turn into an inventory, what manual process can I automate, and what failure can I detect earlier?"
