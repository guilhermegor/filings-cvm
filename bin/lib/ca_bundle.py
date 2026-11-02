"""Build a UNION CA bundle: the corporate proxy CA plus everything already trusted.

Used by ``bin/lib/bootstrap.sh::build_union_ca_bundle`` on networks behind a TLS-inspecting
proxy. Reads ``BX_CA_CORPORATE`` (the proxy's certificate) and ``BX_CA_OUT`` (where to
write), prints the number of certificates written, and exits non-zero rather than producing
a bundle that would narrow the host's trust.

⚠️ WHY THIS IS A FILE AND NOT A HEREDOC. It lived inside a shell function as a
``"$PYTHON" - <<'PYEOF'`` block: six lines of shell wrapping ~66 lines of security-relevant
Python that ruff never linted, mypy never checked, and no unit test could import. It is
covered behaviourally through the shell seam by
``tests/integration/test_bin_scripts.py::test_corporate_ca_bundle_is_a_union_not_a_replacement``
and its refusal sibling, which is why extracting it is verifiable rather than hopeful.

THE INVARIANT THIS FILE EXISTS TO KEEP: a bundle containing only the corporate CA is a
REPLACEMENT wearing the word "union". Writing one would narrow the trust store to a single
certificate — the exact defect this function was written to remove, arrived at from the
other direction — so that case fails loudly and leaves TLS untouched.
"""

from __future__ import annotations

import os
import pathlib
import re
import sys


TUPLE_CA_ENV_VARS = ("PIP_CERT", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE")

RE_PEM_BLOCK = re.compile(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", re.DOTALL)


def collect_sources(str_corporate: str, path_out: pathlib.Path) -> list:
    """Return every candidate CA source, corporate certificate first.

    Order matters: index 0 is the corporate CA, so the caller can tell "trust we added"
    from "trust that was already there".

    Parameters
    ----------
    str_corporate : str
        Path to the corporate proxy's certificate.
    path_out : pathlib.Path
        Where the union will be written.

    Returns
    -------
    list of str
        Candidate paths; not all of them necessarily exist.
    """
    list_sources = [str_corporate]

    for str_var in TUPLE_CA_ENV_VARS:
        str_existing = os.environ.get(str_var, "")
        if str_existing and pathlib.Path(str_existing) != path_out:
            list_sources.append(str_existing)

    try:
        import certifi

        list_sources.append(certifi.where())
    except ModuleNotFoundError:
        print("certifi not importable — union built without it", file=sys.stderr)

    return list_sources


def dedupe_certificates(list_sources: list) -> tuple:
    """Read every source and return its unique certificates.

    Parameters
    ----------
    list_sources : list of str
        Candidate paths, corporate certificate at index 0.

    Returns
    -------
    tuple
        ``(list_blocks, int_non_corporate)`` — the unique PEM blocks in first-seen order,
        and how many of them came from a source OTHER than the corporate certificate.
    """
    list_blocks: list[str] = []
    set_bodies: set[str] = set()
    int_non_corporate = 0

    for int_index, str_source in enumerate(list_sources):
        path_source = pathlib.Path(str_source)
        if not path_source.is_file():
            continue
        str_text = path_source.read_text(encoding="utf-8", errors="replace")
        for str_block in RE_PEM_BLOCK.findall(str_text):
            str_body = "".join(str_block.split())
            if str_body in set_bodies:
                continue
            set_bodies.add(str_body)
            list_blocks.append(str_block)
            if int_index > 0:
                int_non_corporate += 1

    return list_blocks, int_non_corporate


def main() -> int:
    """Write the union bundle, or refuse and explain why.

    Returns
    -------
    int
        0 after writing, 1 when there is nothing to write or the union would be a
        replacement.
    """
    path_out = pathlib.Path(os.environ["BX_CA_OUT"])
    list_sources = collect_sources(os.environ["BX_CA_CORPORATE"], path_out)
    list_blocks, int_non_corporate = dedupe_certificates(list_sources)

    if not list_blocks:
        print("No certificates found for the union bundle", file=sys.stderr)
        return 1

    if int_non_corporate == 0:
        print(
            "Refusing to write a CA bundle containing ONLY the corporate certificate: that "
            "narrows the trust store instead of widening it. Install certifi (pip install "
            "certifi) or point PIP_CERT/REQUESTS_CA_BUNDLE at the host's CA bundle, then retry.",
            file=sys.stderr,
        )
        return 1

    path_out.parent.mkdir(parents=True, exist_ok=True)
    path_out.write_text("\n".join(list_blocks) + "\n", encoding="utf-8")
    print(len(list_blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
