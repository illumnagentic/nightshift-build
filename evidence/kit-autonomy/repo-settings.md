# Repo settings: illumnagentic/nightshift-build

Date: 2026-10-24

Read command (run before and after):

```
gh api repos/illumnagentic/nightshift-build --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge,squash_merge_commit_title,squash_merge_commit_message,delete_branch_on_merge}'
```

Apply command:

```
gh api -X PATCH repos/illumnagentic/nightshift-build -F allow_merge_commit=false -F allow_rebase_merge=false -F allow_squash_merge=true -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=BLANK -F delete_branch_on_merge=true
```

| Field | Before | After |
|---|---|---|
| allow_squash_merge | true | true |
| allow_merge_commit | true | false |
| allow_rebase_merge | true | false |
| squash_merge_commit_title | COMMIT_OR_PR_TITLE | PR_TITLE |
| squash_merge_commit_message | COMMIT_MESSAGES | BLANK |
| delete_branch_on_merge | false | true |
