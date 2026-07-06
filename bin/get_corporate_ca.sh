#!/usr/bin/env bash
# Generate bin/corporate_ca.pem from the certificate your corporate TLS-inspecting
# proxy presents for pypi.org. Run this only on a network behind such a proxy; on
# a normal network you do not need it. The generated pem is git-ignored and picked
# up automatically by `make venv` / `make run` (see lib/bootstrap.sh).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

extract_corporate_ca() {
	print_status "config" "Extracting corporate CA from pypi.org ..."
	BOOTSTRAP_CERT_OUT="$CORPORATE_CA_PEM" "$PYTHON" - <<'PYEOF'
import os
import socket
import ssl
import sys

hostname = "pypi.org"
out = os.environ["BOOTSTRAP_CERT_OUT"]

# Verification is intentionally disabled here: the whole point is to capture the
# CA that a TLS-inspecting proxy substitutes for pypi.org's chain, which by
# definition is not yet trusted. The captured cert is written to disk for the
# operator to inspect; nothing is fetched over this connection but the cert.
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with socket.create_connection((hostname, 443), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            der = ssock.getpeercert(binary_form=True)
    pem = ssl.DER_cert_to_PEM_cert(der)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as fh:
        fh.write(pem)
except Exception as exc:  # noqa: BLE001
    print(f"Failed to extract certificate: {exc}", file=sys.stderr)
    sys.exit(1)
PYEOF
}

main() {
	print_status "section" "Corporate CA Setup"
	bootstrap_init

	print_status "warning" "This trusts whatever CA your network presents for pypi.org."
	print_status "warning" "Only run it behind a corporate TLS-inspecting proxy."
	if [[ -f "$CORPORATE_CA_PEM" ]]; then
		print_status "warning" "Overwriting existing $CORPORATE_CA_PEM"
	fi

	extract_corporate_ca
	print_status "success" "Corporate CA saved: $CORPORATE_CA_PEM"

	wire_corporate_ca
	print_status "info" "Re-run 'make venv' to install dependencies through the proxy."
}

main "$@"
