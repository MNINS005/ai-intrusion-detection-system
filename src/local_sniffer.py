"""
Local packet sniffer for the IDS dashboard.

Run the Django server first, then run this script with administrator/root
permissions so Scapy can capture packets from the network interface.
"""

import argparse
import json
import sys
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


SERVICE_BY_PORT = {
    20: "ftp",
    21: "ftp",
    22: "ssh",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "other",
    143: "other",
    443: "http",
    465: "smtp",
    587: "smtp",
    8080: "http",
    8443: "http",
}


def detect_service(src_port, dst_port):
    return SERVICE_BY_PORT.get(dst_port) or SERVICE_BY_PORT.get(src_port) or "other"


def tcp_flag_to_nsl(tcp_layer):
    flags = str(tcp_layer.flags)
    if "R" in flags:
        return "REJ"
    if "S" in flags and "A" not in flags:
        return "S0"
    if "S" in flags and "F" in flags:
        return "SH"
    return "SF"


def packet_to_payload(packet):
    from scapy.layers.inet import IP, TCP, UDP, ICMP

    if IP not in packet:
        return None

    ip = packet[IP]
    src_bytes = len(packet)
    dst_bytes = 0

    if TCP in packet:
        tcp = packet[TCP]
        return {
            "protocol_type": "tcp",
            "service": detect_service(int(tcp.sport), int(tcp.dport)),
            "flag": tcp_flag_to_nsl(tcp),
            "src_bytes": src_bytes,
            "dst_bytes": dst_bytes,
            "src_ip": ip.src,
            "dst_ip": ip.dst,
            "src_port": int(tcp.sport),
            "dst_port": int(tcp.dport),
        }

    if UDP in packet:
        udp = packet[UDP]
        return {
            "protocol_type": "udp",
            "service": detect_service(int(udp.sport), int(udp.dport)),
            "flag": "SF",
            "src_bytes": src_bytes,
            "dst_bytes": dst_bytes,
            "src_ip": ip.src,
            "dst_ip": ip.dst,
            "src_port": int(udp.sport),
            "dst_port": int(udp.dport),
        }

    if ICMP in packet:
        return {
            "protocol_type": "icmp",
            "service": "other",
            "flag": "SF",
            "src_bytes": src_bytes,
            "dst_bytes": dst_bytes,
            "src_ip": ip.src,
            "dst_ip": ip.dst,
            "src_port": 0,
            "dst_port": 0,
        }

    return None


def submit_prediction(endpoint, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_packet_handler(endpoint, timeout, verbose):
    def handle_packet(packet):
        payload = packet_to_payload(packet)
        if not payload:
            return

        try:
            result = submit_prediction(endpoint, payload, timeout)
        except HTTPError as exc:
            print(f"[api-error] {exc.code}: {exc.reason}", file=sys.stderr)
            return
        except URLError as exc:
            print(f"[connection-error] Could not reach Django endpoint: {exc}", file=sys.stderr)
            return
        except Exception as exc:
            print(f"[sniffer-error] {exc}", file=sys.stderr)
            return

        status = result.get("predicted_class", "Unknown")
        line = (
            f"{status:7} {payload['protocol_type'].upper():4} "
            f"{payload['src_ip']}:{payload['src_port']} -> "
            f"{payload['dst_ip']}:{payload['dst_port']} "
            f"{payload['service']} {payload['flag']} bytes={payload['src_bytes']}"
        )
        print(line)

        if verbose:
            print(json.dumps({"payload": payload, "result": result}, indent=2))

    return handle_packet


def parse_args():
    parser = argparse.ArgumentParser(description="Capture local traffic and submit it to the IDS Django app.")
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8000/api/sniffer/predict/",
        help="Django sniffer prediction endpoint.",
    )
    parser.add_argument("--iface", default=None, help="Network interface name. Defaults to Scapy's default.")
    parser.add_argument("--filter", default="ip", help="BPF capture filter passed to Scapy.")
    parser.add_argument("--count", type=int, default=0, help="Number of packets to capture. 0 means unlimited.")
    parser.add_argument("--timeout", type=float, default=3.0, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--layer3",
        action="store_true",
        help="Use Scapy's layer-3 socket. Useful on Windows when Npcap/WinPcap is not installed.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print full payload and API result.")
    return parser.parse_args()


def main():
    try:
        from scapy.all import conf, sniff
    except ImportError:
        print("Scapy is not installed. Install it with: pip install scapy", file=sys.stderr)
        return 1

    args = parse_args()
    handler = build_packet_handler(args.endpoint, args.timeout, args.verbose)

    print(f"Sending captured traffic to: {args.endpoint}")
    print("Stop with Ctrl+C.")

    try:
        sniff_kwargs = {
            "prn": handler,
            "store": False,
            "count": args.count,
        }

        if args.layer3:
            sniff_kwargs["opened_socket"] = conf.L3socket(iface=args.iface)
        else:
            sniff_kwargs["iface"] = args.iface
            sniff_kwargs["filter"] = args.filter

        sniff(**sniff_kwargs)
    except PermissionError:
        print("Permission denied. Run this terminal as Administrator/root for packet capture.", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        if "winpcap is not installed" in str(exc).lower() or "libpcap" in str(exc).lower():
            print("Packet capture driver is missing. Try again with --layer3, or install Npcap.", file=sys.stderr)
            return 1
        print(f"Sniffer failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nSniffer stopped.")
    except Exception as exc:
        print(f"Sniffer failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
