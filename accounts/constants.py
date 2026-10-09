"""Account-creation permission matrix — enforcement for the governance doc
'Who Should Create Accounts?'.

Three creators exist in a typical Malawi secondary school:

  1. Registry Clerk / Secretary  -> student + parent accounts
  2. HR Officer / Deputy (Admin) -> teacher + non-teaching staff accounts
  3. Head Teacher                -> admin / bursar / auditor accounts, plus
                                    an override on everything else.

Everyone else has zero account-creation ability. Expressed as Django
permissions on the User model so the matrix is data, not hard-coded role
checks, and a Head Teacher can delegate without a code change.
"""

# Codenames — resolved as `accounts.<codename>` in Django.
CREATE_ACCOUNT = 'accounts.create_account'
CREATE_STUDENT_ACCOUNT = 'accounts.create_student_account'
CREATE_PARENT_ACCOUNT = 'accounts.create_parent_account'
CREATE_TEACHER_ACCOUNT = 'accounts.create_teacher_account'
CREATE_STAFF_ACCOUNT = 'accounts.create_staff_account'
CREATE_ADMIN_ACCOUNT = 'accounts.create_admin_account'
CREATE_BURSAR_ACCOUNT = 'accounts.create_bursar_account'
CREATE_AUDITOR_ACCOUNT = 'accounts.create_auditor_account'
CREATE_HIGH_PRIVILEGE_ACCOUNT = 'accounts.create_high_privilege_account'
APPROVE_ACCOUNT_CREATION = 'accounts.approve_account_creation'


# Invitation purpose -> specific permission required to issue it.
INVITATION_PURPOSE_PERMISSION = {
    'student': CREATE_STUDENT_ACCOUNT,
    'parent': CREATE_PARENT_ACCOUNT,
    'teacher': CREATE_TEACHER_ACCOUNT,
    'staff': CREATE_STAFF_ACCOUNT,
    'admin': CREATE_ADMIN_ACCOUNT,
    'bursar': CREATE_BURSAR_ACCOUNT,
    'auditor': CREATE_AUDITOR_ACCOUNT,
}

# Purposes that additionally require the high-privilege gate.
HIGH_PRIVILEGE_PURPOSES = {'admin', 'bursar', 'auditor'}

# Purpose -> approval workflow (doc §5).
#   implicit    — admission/appointment already signed off, no extra step
#   two_step    — HR drafts -> Head Teacher approves -> invitation sends
#   three_step  — Head Teacher creates directly + 2FA + cool-off
APPROVAL_WORKFLOW = {
    'student': 'implicit',
    'parent': 'implicit',
    'teacher': 'two_step',
    'staff': 'two_step',
    'admin': 'three_step',
    'bursar': 'three_step',
    'auditor': 'three_step',
}

# Purpose -> how the account is created when the invitation is claimed.
#   auto_claim  — user sets their own password via the invitation link
#   direct      — Head Teacher sets an initial password + 2FA is enforced
CREATION_METHOD = {
    'student': 'auto_claim',
    'parent': 'auto_claim',
    'teacher': 'auto_claim',
    'staff': 'auto_claim',
    'admin': 'direct',
    'bursar': 'direct',
    'auditor': 'direct',
}

# High-privilege cool-off before the account goes live (doc §5).
HIGH_PRIVILEGE_COOLOFF_HOURS = 24

# Self-registration policy (doc §3): parent-only, always with proof.
SELF_REGISTRATION_ALLOWED_ROLES = ('parent',)