This command will analyze a GitHub issue and prepare a detailed plan for implementation.

The argument should be the GitHub issue number.

Follow these steps:
1. Use the GitHub CLI to fetch detailed information about the issue
2. Analyze the issue requirements
3. Review the existing codebase to understand what needs to be modified
4. Research any necessary information online using available MCP tools
5. Create a detailed implementation plan
6. Save the plan to .knocodex/tasks/[issue-number]-plan.md

The plan should include:
- Issue summary
- Required changes
- Implementation steps
- Files to be modified
- Testing approach
- Estimated complexity

Be thorough in your analysis and consider all aspects of the implementation, including:
- Performance implications
- Security considerations
- Backward compatibility
- Error handling
- Documentation updates

ARGUMENTS: {issue_number}
