# Existing Vametra authentication regression checks

- Read credentials from memory/test_credentials.md; do not add secrets to new test code or reports.
- Buyer identity remains Firebase + DO. Never seed website-local buyer identities.
- Staff JWT remains separate. Test valid/invalid/deactivated staff credentials and expired tokens.
- Firebase main-admin bearer plus an old X-Staff-Token must resolve main_admin; staff alone resolves sub_admin.
- Main login clears staff session. Staff login signs out the existing Firebase session.
- Verify subadmin cannot execute final decisions, revoke subscriptions, or hard-delete directly.
- Buyer/staff role or verification updates through profile patches cannot escalate privileges.
- Authorized final approval delegates a temporary target token on the server only. Verify DO GET /members/company
  matches the target Customer ID and returns the existing GEID; main administrator's binding must not change.
- Test one normal-signup, visibly flagged disposable account. Run approve/grant/contact/profile/doc/reject checks
  BEFORE cleanup. Hard-delete only that disposable account and confirm DO 404 and Firebase sign-in blocked.
- Never restore a real user's cancelled subscription to make a test pass.