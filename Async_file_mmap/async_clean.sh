#!/bin/bash

f="$1"

jq -c '
        . | del(.index["_type"]) |
        walk(if type == "string" and test("^[0-9]+(\\.[0-9]+)?$") then tonumber else . end) |
        if .layers.ip.ip_ip_proto != null then
            .layers.ip.ip_ip_proto |= (if . == 6 then "tcp" elif . == 17 then "udp" elif . == 1 then "icmp" elif . == 2 then "igmp" elif . == 89 then "ospf" else . end) 
        else
            .
        end |
        del(.layers.eth.eth_eth_ig) |
        del(.layers.eth.eth_eth_lg) |
        del(.layers.eth.eth_eth_addr) |
        del(.layers.eth.eth_eth_addr_oui) |
        del(.layers.eth.eth_eth_src_resolved) |
        del(.layers.eth.eth_eth_dst_resolved) |
        del(.layers.ip.ip_ip_host) |
        del(.layers.ip.ip_ip_addr) |
        del(.layers.ip.ip_ip_src_host) |
        del(.layers.ip.ip_ip_dst_host) |
        del(.layers.udp.udp_udp_port) |
        del(.layers.tcp.tcp_tcp_port) |
        del(.layers.udp.udp_udp_payload) |
        del(.layers.tcp.tcp_tcp_payload)
    ' "cap_json/$f" > "ready/$f"