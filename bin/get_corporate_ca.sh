#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

export_windows_trust_store() {
	print_status "config" "Reading the Windows trust store (ROOT + CA) ..."
	BOOTSTRAP_CERT_OUT="$CORPORATE_CA_PEM" "$PYTHON" - <<'PYEOF'
import os
import pathlib
import ssl
import sys

path_out = pathlib.Path(os.environ["BOOTSTRAP_CERT_OUT"])
list_pem: list[str] = []
set_seen: set[bytes] = set()

for str_store in ("ROOT", "CA"):
    try:
        list_certs = ssl.enum_certificates(str_store)
    except (AttributeError, OSError) as exc:
        print(f"Cannot read the {str_store} store: {exc}", file=sys.stderr)
        continue
    for bytes_der, _str_encoding, _obj_trust in list_certs:
        if bytes_der in set_seen:
            continue
        set_seen.add(bytes_der)
        list_pem.append(ssl.DER_cert_to_PEM_cert(bytes_der))

if not list_pem:
    print("No certificates found in the Windows trust store", file=sys.stderr)
    sys.exit(1)

path_out.parent.mkdir(parents=True, exist_ok=True)
path_out.write_text("".join(list_pem), encoding="utf-8")
print(len(list_pem))
PYEOF
}

explain_manual_route() {
	print_status "error" "Automatic extraction is implemented for Windows only."
	print_status "info" "On this OS the system trust store is already a PEM file. Copy it (or just your corporate CA) to:"
	print_status "info" "    $CORPORATE_CA_PEM"
	print_status "info" "Common locations:"
	print_status "info" "    Debian/Ubuntu  /etc/ssl/certs/ca-certificates.crt"
	print_status "info" "    RHEL/Fedora    /etc/pki/tls/certs/ca-bundle.crt"
	print_status "info" "    macOS          security find-certificate -a -p /Library/Keychains/System.keychain"
	print_status "info" "Then re-run 'poe venv'."
}

main() {
	print_status "section" "Corporate CA Setup"
	bootstrap_init

	if [[ -f "$CORPORATE_CA_PEM" ]]; then
		print_status "warning" "Overwriting existing $CORPORATE_CA_PEM"
	fi

	if [[ "$OS_TYPE" != "windows" ]]; then
		explain_manual_route
		exit 1
	fi

	local str_count
	str_count="$(export_windows_trust_store)"
	print_status "success" "Trust store exported ($str_count certs): $CORPORATE_CA_PEM"

	wire_corporate_ca
	print_status "info" "Re-run 'poe venv' to install dependencies through the proxy."
}

main "$@"
