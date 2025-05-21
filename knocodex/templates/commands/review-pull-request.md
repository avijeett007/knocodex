This command will review a GitHub pull request and provide detailed, structured feedback following a standardized template.

The argument should be the GitHub PR number.

Follow these steps:
1. Use the GitHub CLI to fetch detailed information about the PR
2. Get the full diff of the PR changes
3. Check if the PR is related to a specific issue:
   - Look in the PR description for "Fixes #X" or "Closes #X" references
   - If found, note the issue number for relationship tracking
4. Check if this is an initial review or a re-review of an updated PR
5. Analyze the code changes for:
   - Code quality issues (style, conventions, readability)
   - Potential bugs or logical errors
   - Security concerns (input validation, auth issues, etc.)
   - Performance considerations (algorithms, database queries, etc.)
   - Adherence to project coding standards
   - Completeness of implementation
   - Test coverage and quality
   - Documentation completeness
6. Check for any related PRs or previous reviews
7. Generate a comprehensive review using the template at `.knocodex/templates/pr_review_template.md`
8. Fill in all sections of the template with detailed analysis
9. Save the review to `.knocodex/reviews/pr-{pr_number}-review.md`
10. Record the review in the PR-Issue relationship tracking system
11. Post the review as a comment on the PR using the GitHub CLI

Your review must include:
- Severity levels for each issue (Critical, High, Medium, Low)
- Specific line numbers for all issues
- Clear, actionable recommendations
- Code examples when suggesting changes
- At least one positive aspect of the PR
- A final recommendation: Approve, Approve with Changes, or Request Changes

The review should use a consistent, structured format that helps track issues across PR updates. Use markdown formatting to make the review easy to read.

For re-reviews of updated PRs:
- Focus primarily on changes made since the last review
- Check if previous issues have been addressed
- Note any new issues introduced by the changes
- Be more lenient on minor issues if the PR author has made significant progress

Update the PR-Issue relationship tracking with:
- The PR's relationship to any referenced issues
- The review ID and timestamp
- Review status (completed)
- Review type (initial or re-review)

ARGUMENTS: {pr_number}
