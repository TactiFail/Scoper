# Scoper

`scoper` helps penetration testers stay in-scope by performing IP address or hostname lookups against provided scope lists. Users can provide a scope list and optional exclusion list, against which Scoper can check individual IP addresses and hostnames, or whole files of them one per line. Scopes and exclusions can be individual IPs, CIDR ranges, or IP ranges (e.g. 192.168.1.100-200). This saves time whenever you need to answer the question "Is this in scope?"

Additionally, Scoper can output `iptables` rules to block all inbound and outbound traffic to excluded targets, to ensure that no other tools accidentally send traffic their way.

## Quickstart

Example run:

```
$ cat test/scope.txt
10.1.1.0/24
10.1.2.0/24
10.1.4.0/24
10.1.5.1-150
10.1.6.250

$ cat test/exclude.txt
10.1.1.100
10.1.3.0/24
10.1.4.10-20

$ cat test/targets.txt
10.1.1.10
10.1.1.100
10.1.2.100
10.1.3.100
10.1.4.100
10.1.5.100
10.1.6.250
google.com

$ ./scoper.py -sf test/scope.txt -ef test/exclude.txt test/targets.txt
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

[+] The target 10.1.1.10 is in scope
[!] The target 10.1.1.100 is explicitly excluded from the scope
[+] The target 10.1.2.100 is in scope
[!] The target 10.1.3.100 is explicitly excluded from the scope
[+] The target 10.1.4.100 is in scope
[+] The target 10.1.5.100 is in scope
[+] The target 10.1.6.250 is in scope
[-] The target 142.250.191.174 (google.com) is out of scope.
```

## Setup

Download `scoper`:

```
git clone https://github.com/TactiFail/scoper
cd scoper
```

install dependencies:

```
pip3 install -r requirements.txt
```

and that's it as far as installation.

## Usage

`scoper` is pretty easy to use, but first you need to define your scope.

### Scope Files

There are two files of importance:

 - A list of in-scope targets (required)
 - A list of excluded targets (optional)

#### Scope File

The scope file is pretty much what you'd expect. It's a text file of your in-scope targets, one per line. Each line can be an individual IP, a CIDR range, or an IP range (e.g. `10.1.5.1-150`). Anything in this file is considered in-scope for the engagement. Anything not in this file is considered out-of-scope.

Example:

```
$ cat test/scope.txt
10.1.1.0/24
10.1.2.0/24
10.1.4.0/24
10.1.5.1-150
10.1.6.250
```

#### Exclusion File

The optional exclusion file is used to mark out specific IPs or ranges within your scope which are to be excluded from testing. For example, using the above scope you could specifically exclude `10.1.1.100` from that scope by putting it in the exclusion file. The exclusion file uses the same format as the scope file, i.e. you can have individual IPs, CIDR ranges, or IP ranges (e.g. `10.1.4.10-20`).

Example:

```
$ cat test/exclude.txt
10.1.1.100
10.1.3.0/24
10.1.4.10-20
```

The exclusion file entries always take precedence over scope file entries.

### Defining Scope

There are a few ways to set up your scope and exclusion files:

#### Using the `.env` File

Probably the easiest way is to create a `.env` file with your scope and exclusion lists:

```
$ cp .env.example .env
$ cat .env
SCOPE_FILE_PATH=/home/tester/scope.txt
EXCLUDE_FILE_PATH=/home/tester/exclude.txt
```

If those are set, `scoper` will use those files automatically. They can either be absolute or relative file paths.

#### Using Environment Variables

You can also set these paths as environment variables:

```
export SCOPE_FILE_PATH=/home/tester/scope.txt
export EXCLUDE_FILE_PATH=/home/tester/exclude.txt
```

Environment variables set in this way will take precedence over `.env` file settings.

#### Using Implicit `scope.txt` and `exclude.txt` Files

If neither of those are set, `scoper` will look for a `scope.txt` and `exclude.txt` file in its directory. Those have not been included in the repo as we recommend using the `.env` file approach.

#### Using The `-sf` and `-ef` Flags

Finally, you can define the scope and exclusion files with the `-sf` and `-ef` flags respectively:

```
$ ./scoper.py -sf /home/tester/scope.txt -ef /home/tester/exclude.txt targets.txt
```

This will take precedence over any other option. This can be useful if you have multiple scope/exclude lists for whatever reason.

### Precedence

The order of precedence (top takes priority) for defining scope and exclude files is:

 - Explicit Flags
 - Implicit Files
 - Environment Variables
 - `.env` File

### Scope Format

Scope and exclusion file entries can be one of:

 - Single IPv4 address (e.g. `10.1.1.10`)
 - CIDR range (e.g. `10.1.1.0/24`)
 - IPv4 address range (e.g. `10.1.5.1-150`)
 - Single hostname (e.g. `google.com`)
   - Note that hostnames cannot be a single word such as `google`; a proper domain is needed

### Help output

```
$ ./scoper.py -h
usage: scoper.py [-h] [-sf SCOPE_FILE] [-ef EXCLUDE_FILE] [-i] [-v] [-fw | -g | -li | -le | -lo | -ln] [target]

Check whether target machines are in scope. Optionally generate iptables rules if not.

positional arguments:
  target                IP address, hostname, or a file containing targets to check

options:
  -h, --help            show this help message and exit
  -sf SCOPE_FILE, --scope-file SCOPE_FILE
                        file containing a list of in-scope IP addresses or ranges
  -ef EXCLUDE_FILE, --exclude-file EXCLUDE_FILE
                        file containing a list of excluded IP addresses or ranges
  -i, --interactive     interactive mode
  -v, --verbose         verbose output

output:
  mutually exclusive, choose one or none

  -fw, --firewall       generate iptables rules for excluded targets found in target list
  -g, --greppable       output in greppable format
  -li, --list-in        only list in-scope targets
  -le, --list-ex        only list excluded targets
  -lo, --list-out       only list out-of-scope targets
  -ln, --list-not       only list not-in-scope targets (combines -le and -lo)
```

## Examples

All examples assume t he following scope, exclusion, and target files unless otherwise specified:

```
$ cat test/scope.txt
10.1.1.0/24
10.1.2.0/24
10.1.4.0/24
10.1.5.1-150
10.1.6.250

$ cat test/exclude.txt
10.1.1.100
10.1.3.0/24
10.1.4.10-20

$ cat test/targets.txt
10.1.1.10
10.1.1.100
10.1.2.100
10.1.3.100
10.1.4.100
10.1.5.100
10.1.6.250
google.com
```

Specific examples may have them defined differently (direct, `.env` file config, undefined, etc.) but their contents will be the same for the purposes of demonstration.

### Basic Examples

#### Single Target, No Exclusions

```
$ cat .env
SCOPE_FILE_PATH=test/scope.txt
#EXCLUDE_FILE_PATH=test/exclude.txt

$ ./scoper.py 10.1.1.100
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

[+] The target 10.1.1.100 is in scope
```

#### Single Target with Exclusions

```
$ cat .env
SCOPE_FILE_PATH=test/scope.txt
EXCLUDE_FILE_PATH=test/exclude.txt

$ ./scoper.py 10.1.1.100
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

[X] The target 10.1.1.100 is explicitly excluded from the scope
```

#### Target List File

```
$ ./scoper.py test/targets.txt
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

[+] The target 10.1.1.10 is in scope
[X] The target 10.1.1.100 is explicitly excluded from the scope
[+] The target 10.1.2.100 is in scope
[X] The target 10.1.3.100 is explicitly excluded from the scope
[+] The target 10.1.4.100 is in scope
[+] The target 10.1.5.100 is in scope
[+] The target 10.1.6.250 is in scope
[-] The target 172.217.1.110 (google.com) is out of scope.
```

#### Greppable Output

```
$ ./scoper.py test/targets.txt -g
10.1.1.10 : InScope
10.1.1.100 : Excluded
10.1.2.100 : InScope
10.1.3.100 : Excluded
10.1.4.100 : InScope
10.1.5.100 : InScope
10.1.6.250 : InScope
google.com : OutOfScope
```

#### Firewall Rules Generation

```
$ ./scoper.py test/targets.txt -fw
iptables -A INPUT -s 10.1.1.100 -j DROP
iptables -A OUTPUT -d 10.1.1.100 -j DROP
iptables -A INPUT -s 10.1.3.100 -j DROP
iptables -A OUTPUT -d 10.1.3.100 -j DROP
```

#### Verbose Output
```
$ ./scoper.py test/targets.txt -v
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

[+] The target 10.1.1.10 is in scope, matching line: 10.1.1.0/24
[X] The target 10.1.1.100 is explicitly excluded from the scope, matching line: 10.1.1.100
[+] The target 10.1.2.100 is in scope, matching line: 10.1.2.0/24
[X] The target 10.1.3.100 is explicitly excluded from the scope, matching line: 10.1.3.0/24
[+] The target 10.1.4.100 is in scope, matching line: 10.1.4.0/24
[+] The target 10.1.5.100 is in scope, matching line: 10.1.5.1-150
[+] The target 10.1.6.250 is in scope, matching line: 10.1.6.250
[-] The target 172.217.1.110 (google.com) is out of scope.
```

#### Invalid Targets

```
$ cat test/targets.txt
10.1.1.10
10.1.1.100
10.1.2.100
10.1.3.100
10.1.4.100
10.1.5.100
10.1.6.250
google.com
1.1.1.1.1
asdf
asdffsad.fdsafasdfasffffqeqewfqwefqwef.com

$ ./scoper.py test/targets.txt -v
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

[+] The target 10.1.1.10 is in scope, matching line: 10.1.1.0/24
[X] The target 10.1.1.100 is explicitly excluded from the scope, matching line: 10.1.1.100
[+] The target 10.1.2.100 is in scope, matching line: 10.1.2.0/24
[X] The target 10.1.3.100 is explicitly excluded from the scope, matching line: 10.1.3.0/24
[+] The target 10.1.4.100 is in scope, matching line: 10.1.4.0/24
[+] The target 10.1.5.100 is in scope, matching line: 10.1.5.1-150
[+] The target 10.1.6.250 is in scope, matching line: 10.1.6.250
[-] The target 142.250.191.142 (google.com) is out of scope.
[!] Skipping unresolvable target '1.1.1.1.1'
[!] Skipping unresolvable target 'asdf'
[!] Skipping unresolvable target 'asdffsad.fdsafasdfasffffqeqewfqwefqwef.com'
```

#### Interactive Mode

*Interactive Mode* is a new feature as of v.1.1.0

By passing in the `-i` or `--interactive` flags, you can enter a loop where you provide a single target at a time. History is stored so you can press up or down to quickly navigate through previous entries, for example to increment the last octet quickly or fix a typo. You can type `exit`, `quit`, or press `ctrl + c` to leave.

```
$ ./scoper.py -i
 _____ _____ _____ _____ _____ _____
|   __|     |     |  _  |   __| __  |
|__   |   --|  +  |   __|   __|    -|
|_____|_____|_____|__|  |_____|__|__| v1.1.0 by @TactiFail

Enter targets, one at a time
[>] 10.1.1.10
[+] The target 10.1.1.10 is in scope
[>] google.com
[-] The target 142.250.191.142 (google.com) is out of scope.
[>] 10.1.3.20
[X] The target 10.1.3.20 is explicitly excluded from the scope
[>] exit
Exiting...
```