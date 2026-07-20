# Future Standard NYC Network Alert Conversation Notes

## Purpose

Use this note to understand NYC network alerts, separate likely root cause from downstream symptoms, and have a useful conversation with the person who was working on the site.

The goal is not to pretend to know exactly what happened. The goal is to sound observant, curious, and infrastructure-minded.

## Alert Pattern Observed

Alerts mentioned:

```text
1 new alert on NYC network requiring attention
Critical network element offline: FW-NYC-0128-MA
Critical network element offline: FW-NYC-01282-SL
Critical network element offline: SWC-NYC-01083
Warning: interface status mismatch on port 3 of SW-NYC-02336
Port 3 on SW-NYC-02336 is administratively up but operationally down
Port 3 on SW-NYC-02336 connected to port 50 on SW-NYC-01122
Internet connection lost on port 1 of FW-NY-01084
Default gateway 47.19.76.170 lost
Network element offline: SW-NYC-02337
Network element offline: Device@10.12.1.254
Network element offline: AP-NYC-02976
APC 23rd Floor UPS infrastructure device offline
Interface port description not set on SW-NYC-02336 port 3
```

## First Read

This looks like a NYC network maintenance or cascading connectivity event.

The pattern is bigger than one endpoint going down.

Likely categories:

```text
Firewall/Internet edge alerts
Switch/core/access alerts
Specific switch-uplink interface mismatch
AP offline alert
UPS/infrastructure device offline alert
Unknown device offline alert
```

This could mean:

1. Planned maintenance was happening.
2. A WAN/ISP circuit or firewall interface went down.
3. A switch uplink/cable/SFP failed or was unplugged.
4. A network closet or power/UPS event caused downstream devices to drop.
5. Auvik lost visibility to a segment, causing multiple devices to appear offline.

## Root Cause vs Downstream Symptoms

The most important mental model:

```text
Root cause = the first/main dependency that failed
Symptoms = devices that alerted because they depend on that root device/path
```

Example:

```text
Firewall WAN loses default gateway
  -> site loses internet/VPN/monitoring path
  -> downstream devices may show offline
  -> APs/switches/unknown devices may alert
```

Another example:

```text
Switch uplink between SW-NYC-02336 and SW-NYC-01122 goes down
  -> devices behind SW-NYC-02336 lose upstream connectivity
  -> APs/endpoints/unknown devices behind that switch alert offline
```

Another example:

```text
23rd floor UPS or closet loses power/network management
  -> switch/APs in that closet lose power or monitoring
  -> many device offline alerts appear together
```

## Device And Alert Meaning

### Firewall Pair: `FW-NYC-0128-MA` And `FW-NYC-01282-SL`

`MA` and `SL` may mean something like:

```text
MA = master/main/active firewall
SL = slave/standby/secondary firewall
```

This suggests a possible high-availability firewall pair.

If both firewalls alerted, possible explanations:

```text
Firewall HA failover happened
Both firewalls rebooted during maintenance
Auvik lost management visibility to both
Power/network path to the firewall pair dropped
Upstream/downstream links were interrupted
Firewall config or HA state changed
```

Conversation question:

> I saw both the MA and SL NYC firewall alerts. Was that a firewall HA failover, a reboot, or did Auvik just lose management visibility during maintenance?

### Firewall WAN Alert: `FW-NY-01084` Port 1 Lost Gateway `47.19.76.170`

This is a high-value alert.

It means the firewall's internet/WAN side likely lost reachability to its upstream default gateway.

Interpretation:

```text
FW-NY-01084 port 1
  -> ISP handoff / modem / router / upstream circuit
  -> default gateway 47.19.76.170
```

Possible causes:

```text
ISP outage
Firewall WAN port/link down
Bad cable or SFP
ISP equipment rebooted
Firewall failover event
Maintenance on WAN handoff
Power issue affecting ISP gear
```

Conversation question:

> I saw `FW-NY-01084` lost its internet default gateway on port 1. Was that an ISP circuit issue, firewall failover, or maintenance on the WAN handoff?

### Core Or Closet Switch: `SWC-NYC-01083`

`SWC` may mean switch core, switch closet, or another internal naming convention.

If it went offline near the firewall alerts, it may be part of the dependency chain.

Possible meanings:

```text
A core/distribution switch went offline
A closet switch became unreachable
Auvik lost management visibility to a key switch
The switch rebooted or lost uplink/power
```

Conversation question:

> Was `SWC-NYC-01083` upstream of some of those other NYC devices? I was trying to tell whether the alerts were root-cause devices or downstream symptoms.

### Interface Status Mismatch: `SW-NYC-02336` Port 3 To `SW-NYC-01122` Port 50

Alert details:

```text
SW-NYC-02336 port 3
Administratively up
Operationally down
Connected to SW-NYC-01122 port 50
Port description not set
```

Plain-English meaning:

> The switch config says the port should be enabled, but the physical/link state is down.

This is often described as:

```text
admin up, link down
```

Possible causes:

```text
Cable unplugged
Remote switch rebooted
Remote port disabled or down
Bad copper/fiber cable
Bad SFP/transceiver
Patch panel issue
Planned maintenance disconnect
Power loss on the remote switch
Uplink/port-channel member failed
```

Why it matters:

If this port is an uplink or trunk, it may carry multiple VLANs. Losing it could create multiple downstream alerts.

Conversation question:

> For the port 3 to port 50 mismatch, was that an uplink between switches? I saw it was admin-up but link-down, so I was wondering if that was a cable/SFP issue, a switch reboot, or just maintenance.

Follow-up:

> Was port 3 part of a trunk or port-channel, or was it a single access link?

### AP Offline: `AP-NYC-02976`

An AP offline alert is often a symptom.

Possible causes:

```text
Switch port went down
PoE power was lost
Access switch rebooted
Uplink to switch failed
AP rebooted or failed
VLAN/network path changed
```

If the AP alert happened around the same time as switch/UPS alerts, it may mean the AP lost PoE or lost upstream network from the switch.

Conversation question:

> Did the AP go offline because it lost PoE from the switch, or was the AP itself being worked on?

### UPS Alert: APC 23rd Floor UPS Offline

This is important because a UPS alert can indicate a power or management-path issue in a network closet.

Possible meanings:

```text
UPS management card became unreachable
UPS lost network connectivity
UPS was rebooted/replaced
Power maintenance happened in that closet
The switch that monitors/reaches the UPS went down
The UPS itself had an issue
```

If UPS, switches, and APs alerted together, possible story:

```text
23rd floor closet/power/network event
  -> UPS management went offline
  -> switch or APs lost power/connectivity
  -> downstream network element offline alerts appeared
```

Conversation question:

> I noticed the APC 23rd Floor UPS went offline too. Was there power work happening in that closet, or did the UPS just lose network management?

### Unknown Device: `Device@10.12.1.254`

Auvik names something like `Device@10.12.1.254` when it sees an IP but cannot identify the hostname/type cleanly.

Possible reasons:

```text
No DNS record
No SNMP/API credentials
Device blocks discovery
Old/stale endpoint
Printer/camera/appliance/VM/network device
Monitoring visibility gap
```

Conversation question:

> I also saw `Device@10.12.1.254`. Is that an expected network device, gateway, or just an unknown endpoint Auvik has not fully identified?

## Most Likely Scenarios

### Scenario 1: Planned NYC Network Maintenance

Likely if someone was actively changing things.

Possible sequence:

```text
Firewall or switch maintenance begins
  -> firewall HA or WAN link alerts fire
  -> core/access switch visibility changes
  -> interface mismatch appears on switch uplink
  -> APs/UPS/unknown devices show offline temporarily
```

### Scenario 2: WAN / ISP Circuit Issue

Strong clue:

```text
FW-NY-01084 port 1 lost default gateway 47.19.76.170
```

Possible sequence:

```text
ISP gateway unreachable
  -> internet path lost
  -> VPN/cloud/monitoring path interrupted
  -> Auvik reports critical network elements offline
```

This explains internet/firewall alerts well, but may not explain UPS/AP/switch alerts unless Auvik visibility depends on that WAN path.

### Scenario 3: Switch Uplink / Cable / SFP Issue

Strong clue:

```text
SW-NYC-02336 port 3 admin up but down
connected to SW-NYC-01122 port 50
```

Possible sequence:

```text
Uplink goes down
  -> downstream switch/devices lose connectivity
  -> AP/unknown devices offline
  -> interface mismatch repeats
```

### Scenario 4: Network Closet / UPS / Power Event

Strong clue:

```text
APC 23rd Floor UPS offline
AP offline
switch offline
interface mismatch
```

Possible sequence:

```text
Closet power or UPS management issue
  -> switch/APs lose power or management
  -> Auvik reports offline devices
  -> uplink/interface mismatch appears
```

## Best Conversation Starter

Use this:

> I was looking at the NYC alerts and trying to understand the dependency chain. I saw firewall MA/SL alerts, an internet gateway loss on `FW-NY-01084` port 1, a switch uplink mismatch between `SW-NYC-02336` port 3 and `SW-NYC-01122` port 50, plus AP and UPS alerts. Was that planned maintenance, a WAN circuit issue, or did a closet/power event cascade into those alerts?

This sounds useful because you are not pretending. You are asking about root cause versus symptoms.

## Better Learning Question

Use this if you want to sound curious and sharp:

> I am trying to learn how to tell root cause from downstream noise in Auvik. In that NYC event, would you treat the firewall/default gateway alert as the root, or the switch/UPS alerts?

## Good Follow-Up Questions

Ask these naturally:

```text
Was this planned maintenance or an actual incident?
Were the MA/SL firewall alerts from HA failover?
Was FW-NY-01084 port 1 connected to the primary ISP?
Is 47.19.76.170 the ISP gateway?
Did the switch uplink between SW-NYC-02336 and SW-NYC-01122 go down physically?
Was port 3 an uplink, trunk, or port-channel member?
Did the AP go offline because it lost PoE from the switch?
Was the APC 23rd Floor UPS actually down, or just unreachable from monitoring?
Which alert was the root cause versus a downstream symptom?
Did Auvik show recovery order?
Was there a change ticket tied to this?
```

## Safe Suggestions You Can Make

Use these if the conversation turns into improvement ideas:

> Would it be useful to make a quick dependency note for NYC showing the firewall pair, ISP gateway, core/access switch uplinks, APs, and UPS devices?

> Could we tag which alerts are likely root-cause devices versus downstream symptoms?

> Would it help to document critical uplinks like `SW-NYC-02336 port 3 -> SW-NYC-01122 port 50`?

> For future events, maybe we could keep a short runbook: if NYC internet gateway alert fires, check firewall WAN, ISP circuit, HA status, then core switch/uplink status.

## Things Not To Say

Avoid:

```text
I know what happened.
This is bad design.
Why did you break it?
We should replace this.
Auvik is wrong.
This should all be cloud.
```

Better:

```text
I am trying to understand the sequence.
I am trying to separate root cause from downstream alerts.
I wanted to ask how you would read this event.
```

## Clean Summary

The NYC alerts look like either planned network maintenance or a cascading connectivity event. The strongest root-cause candidates are:

```text
Firewall WAN/default gateway loss on FW-NY-01084 port 1
Firewall HA pair alert involving MA/SL devices
Switch uplink mismatch between SW-NYC-02336 and SW-NYC-01122
23rd floor UPS/network closet event
```

The AP, unknown device, and some network element offline alerts may be downstream symptoms.

Key intuition:

> Find the root alert, then separate symptoms from causes.
