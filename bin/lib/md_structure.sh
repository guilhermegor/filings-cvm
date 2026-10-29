#!/usr/bin/env bash

md_strip_fences() {
	tr -d '\r' | awk '
        BEGIN { in_fence = 0 }
        {
            if (match($0, /^[[:space:]]*(```+|~~~+)/)) {
                run = substr($0, RSTART, RLENGTH); gsub(/[[:space:]]/, "", run)
                ch = substr(run, 1, 1)
                if (!in_fence) { in_fence = 1; f_ch = ch; f_len = length(run); next }
                rest = substr($0, RSTART + RLENGTH)
                if (ch == f_ch && length(run) >= f_len && rest ~ /^[[:space:]]*$/) in_fence = 0
                next
            }
            if (!in_fence) print
        }'
}

md_strip_comments() {
	awk '
        BEGIN { in_comment = 0 }
        {
            line = $0; out = ""
            while (length(line) > 0) {
                if (in_comment) {
                    p = index(line, "-->")
                    if (p == 0) { line = ""; break }
                    line = substr(line, p + 3); in_comment = 0
                } else {
                    p = index(line, "<!--")
                    if (p == 0) { out = out line; line = ""; break }
                    out = out substr(line, 1, p - 1); line = substr(line, p + 4); in_comment = 1
                }
            }
            print out
        }'
}

md_normalize() {
	md_strip_fences | md_strip_comments
}

md_headings() {
	awk '
        function trim(s) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", s); return s }
        /^[[:space:]]*$/ { next }
        match($0, /^<!--[[:space:]]*slug:[[:space:]]*[A-Za-z0-9_-]+[[:space:]]*-->[[:space:]]*$/) {
            s = $0; sub(/^<!--[[:space:]]*slug:[[:space:]]*/, "", s); sub(/[[:space:]]*-->.*$/, "", s)
            slug = s; next
        }
        match($0, /^ ? ? ?#+[[:space:]]/) {
            hashes = $0; sub(/^ +/, "", hashes); sub(/[[:space:]].*$/, "", hashes)
            text = $0; sub(/^ *#+[[:space:]]+/, "", text)
            printf "%d\t%d\t%s\t%s\n", NR, length(hashes), (slug == "" ? "-" : slug), trim(text)
        }
        { slug = "" }
    '
}
