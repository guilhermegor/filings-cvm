# Load .review-bots.yaml from the base ref (#379)

- [x] `policy_root()` in `bin/check_review_threads.py` reads the roster from `origin/<GITHUB_BASE_REF>`
- [x] `bin/check_gate_integrity.py` flags any change to `.review-bots.yaml`
- [x] Unit tests for both
