## Description  
**What**: Briefly summarize the changes (e.g., "Added user authentication module").  
**Why**: Explain the motivation (e.g., "To comply with new security policies").  
**How**: Link to implementation details (e.g., "Used OAuth2.0 via Auth0").  

---

## Changes Made
**Added**:
- New feature: [Description].  
- Dependency: [Package@version].  

**Updated**:
- Refactored [Component] for [Reason].  

**Fixed**:
- Issue #[Number]: [Brief description].  

<!-- CLOSING KEYWORDS — GitHub closes the issue on merge ONLY in this exact shape.
     The line above LINKS the issue; it does not close it. Add one keyword line per issue:

       Closes #12
       Closes #13

     Three traps, all of them measured rather than assumed:
       * NO colon after the keyword. `Closes: #12` / `Fixes: #12` link but never close.
       * ONE keyword PER issue. `Closes #12, #13` closes only #12 — GitHub reads just the
         first item of a comma-separated list. Repeat it: `Closes #12, Closes #13`.
       * The PR must target the DEFAULT branch. A stacked PR (base = another feature
         branch) registers NO closing reference at all, however correct the syntax.
         Retargeting it onto the default branch activates the references — but re-run the
         query below after any retarget rather than assuming it.

     Verify the EFFECT, not the text, once the PR exists:

       gh api graphql -f query='{repository(owner:"OWNER",name:"REPO"){pullRequest(number:N){
         closingIssuesReferences(first:20){nodes{number}}}}}' \
         --jq '.data.repository.pullRequest.closingIssuesReferences.nodes[].number'

     An empty or short list means the PR closes nothing (or not everything) on merge.
     `gh pr view --json closingIssuesReferences` can serve a STALE cache right after
     `gh pr edit`; the GraphQL read above is the reliable one. -->

---

## Testing
### Manual Testing
- **Test Case 1**:  
    - Steps: `1. Navigate to /login → 2. Submit credentials`  
    - Expected: Redirect to dashboard.  
    - Evidence: ![Screenshot](link).  
- **Test Case 2**:  
    - Steps: `Simulate network failure during API call`.  
    - Expected: Graceful error handling.  

### Automated Testing
- **Unit Tests**:  
    - File: `test_auth.py`  
    - Coverage: 95% (via `pytest --cov`).  
- **Integration Tests**:  
    - File: `tests.yaml`  
    - Status: `OK/NOK`.  

**Not Applicable**:  
- Explain (e.g., "Documentation-only change").  

---

## Documentation
- **Code**:
    - Updated docstrings in [files].  
- **Guides**:
    - Added [section] to README.  
- **Changelog**:
    - Entry under [Version].  

---

## Additional Notes  
**Dependencies**:  
- Blocks/Depends on #[PR Number].  

**Follow-up**:  
- Tech debt: [Brief note].  

**Reviewer Focus**:  
- Pay attention to [specific files/logic].  
