#!/usr/bin/env python3

import argparse, ipaddress, socket, os, re, sys
from dotenv import load_dotenv

# Global variables
TARGETS = []
SCOPE = []
EXCLUSIONS = []
VERBOSE = False
DEBUG = False

# Load .env variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
SCOPE_FILE_PATH = os.getenv('SCOPE_FILE_PATH', 'scope.txt')
EXCLUDE_FILE_PATH = os.getenv('EXCLUDE_FILE_PATH', 'exclude.txt')


def run(greppable_output, firewall, list_in, list_ex, list_out, list_not):
    global SCOPE, TARGETS, EXCLUSIONS, VERBOSE

    # Main loop for each Target
    for target in TARGETS:
        if not target.valid:
            continue
        target.state, target.source = check_target_scope(target.ip_address)

        # We just care about firewalls, skip the rest
        if firewall:
            continue

        # Handle greppable
        if greppable_output:
            print(f"{target.target} : {target.state}")
            continue

        # Handle -li, -lo, and -le
        if list_in or list_ex or list_out or list_not:
            if list_in and target.state == "InScope":
                print(f"{target}")
            elif list_ex and target.state == "Excluded":
                print(f"{target}")
            elif list_out and target.state == "OutOfScope":
                print(f"{target}")
            elif list_not and (target.state == "Excluded" or target.state == "OutOfScope"):
                print(f"{target}")
            continue

        # Normal output
        if target.state == "InScope":
            print(f"[+] The target {target} is in scope", end='')
            if VERBOSE:
                print(f", matching line: {target.source}")
            else:
                print("")
        elif target.state == "Excluded":
            print(f"[X] The target {target} is explicitly excluded from the scope", end='')
            if VERBOSE:
                print(f", matching line: {target.source}")
            else:
                print("")
        else:
            print(f"[-] The target {target} is out of scope.")

    if firewall:
        generate_iptables_rules()


class Target:
    def __init__(self, target):
        self.target = target
        self.ip_address = None
        self.hostname = None
        self.valid = True

        # State can be one of "InScope", "OutOfScope", or "Excluded"
        self.state = None

        # Source refers to the line in the scope or exclusion file which matches
        self.source = None

        # Parse the target and set the appropriate variable
        self.parse_target(target)

    def parse_target(self, s):
        # IPv4
        try:
            ipaddress.IPv4Address(s)
            self.ip_address = s
            return
        except ipaddress.AddressValueError:
            pass

        # Hostname
        self.hostname = s
        self.ip_address = resolve_hostname(s)
        if self.ip_address is None:
            self.valid = False
        return

    def __str__(self):
        if self.hostname is not None:
            return f"{self.ip_address} ({self.hostname})"
        else:
            return f"{self.ip_address}"


def load_lists(scope_file, target, exclude_file):
    global SCOPE, TARGETS, EXCLUSIONS

    # Load scope
    try:
        if DEBUG:
            print(f"[@] Loading scope from {scope_file}")
        with open(scope_file, 'r') as file:
            SCOPE = [line.strip() for line in file if line.strip()]
        if DEBUG:
            print(f"[@] Loaded {len(SCOPE)} scope entries")
    except FileNotFoundError:
        print(f"[!] Warning: Scope file not found, bailing\n", file=sys.stderr)
        exit(1)

    # Load targets
    if DEBUG:
        print(f"[@] Loading targets from {target}")
    if os.path.isfile(target):
        with open(target, 'r') as file:
            for line in file:
                t = Target(line.strip())
                TARGETS.append(t)
    elif target:
        TARGETS = [Target(target)]
    if DEBUG:
        print(f"[@] Loaded {len(TARGETS)} targets")

    # Load exclusions, if any
    if DEBUG:
        print(f"[@] Loading exclusions from {exclude_file}")
    try:
        with open(exclude_file, 'r') as file:
            EXCLUSIONS = [line.strip() for line in file if line.strip()]
        if DEBUG:
            print(f"[@] Loaded {len(EXCLUSIONS)} exclusion entries\n")
    except FileNotFoundError:
        print(f"[!] Warning: Exclude file not found - will not check for exclusions\n", file=sys.stderr)


def check_target_scope(ip_address):
    # Check exclusions first
    for address_range in EXCLUSIONS:
        if is_ip_in_range(str(ip_address), address_range):
            return "Excluded", address_range

    # Check scope list
    for address_range in SCOPE:
        if is_ip_in_range(str(ip_address), address_range):
            return "InScope", address_range

    # If not in either, it is out-of-scope
    return "OutOfScope", "not in scope or exclusion files"


def is_ip_in_range(ip, address_range):
    if '/' in address_range:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(address_range, strict=False)
    elif '-' in address_range:
        start_ip, end_ip_part = address_range.split('-')
        if len(end_ip_part.split('.')) == 1:
            start_ip_base = start_ip.rsplit('.', 1)[0]
            end_ip = f"{start_ip_base}.{end_ip_part}"
        else:
            end_ip = end_ip_part
        return ipaddress.ip_address(ip) >= ipaddress.ip_address(start_ip) and ipaddress.ip_address(
            ip) <= ipaddress.ip_address(end_ip)
    else:
        return ipaddress.ip_address(ip) == ipaddress.ip_address(address_range)


def resolve_hostname(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        print(f"[!] Could not resolve '{hostname}'", file=sys.stderr)
        return None


def generate_iptables_rules():
    global TARGETS
    for target in TARGETS:
        if target.state == "Excluded":
            print(f"iptables -A INPUT -s {target.ip_address} -j DROP")
            print(f"iptables -A OUTPUT -d {target.ip_address} -j DROP")


def banner():
    print(""" _____ _____ _____ _____ _____ _____ 
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.0.0 by @TactiFail
""")


def main():
    global TARGETS, VERBOSE

    parser = argparse.ArgumentParser(description='Check whether target machines are in scope. Optionally generate iptables rules if not.')

    # Main args
    parser.add_argument('target', type=str, help='IP address, hostname, or a file containing targets to check')
    parser.add_argument('-sf', '--scope-file', type=str, default=SCOPE_FILE_PATH, help='file containing a list of in-scope IP addresses or ranges')
    parser.add_argument('-ef', '--exclude-file', type=str, default=EXCLUDE_FILE_PATH, help='file containing a list of excluded IP addresses or ranges')
    parser.add_argument('-v',  '--verbose', action='store_true', help='verbose output')

    # Output args
    list_opts_group = parser.add_argument_group("output", "mutually exclusive, choose one or none")
    list_opts_group_ex = list_opts_group.add_mutually_exclusive_group()

    list_opts_group_ex.add_argument('-fw', '--firewall',  action='store_true', help='generate iptables rules for excluded targets found in target list')
    list_opts_group_ex.add_argument('-g',  '--greppable', action='store_true', help='output in greppable format')
    list_opts_group_ex.add_argument('-li', '--list-in',   action='store_true', help='only list in-scope targets')
    list_opts_group_ex.add_argument('-le', '--list-ex',   action='store_true', help='only list excluded targets')
    list_opts_group_ex.add_argument('-lo', '--list-out',  action='store_true', help='only list out-of-scope targets')
    list_opts_group_ex.add_argument('-ln', '--list-not',  action='store_true', help='only list not-in-scope targets (combines -le and -lo)')

    args = parser.parse_args()

    VERBOSE = args.verbose

    # Only show banner in some cases
    if not args.greppable and not args.firewall and not args.list_in and not args.list_ex and not args.list_out and not args.list_not:
        banner()

    # Load targets, scope, and exclusions (if any)
    load_lists(args.scope_file, args.target, args.exclude_file)

    run(args.greppable, args.firewall, args.list_in, args.list_ex, args.list_out, args.list_not)


if __name__ == "__main__":
    main()
