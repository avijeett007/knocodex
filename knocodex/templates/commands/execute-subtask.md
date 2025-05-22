# Execute Subtask Command

## Objective
Execute a specific subtask as part of a larger GitHub issue workflow.

## Context
You are working on subtask {{ subtask_id }} which is part of {{ project_name }} (Issue #{{ issue_number }}).

**Subtask Details:**
- Type: {{ subtask_type }}
- Title: {{ subtask_title }}
- Description: {{ subtask_description }}
- Dependencies: {{ subtask_dependencies }}
- Estimated Effort: {{ estimated_effort }}

**Project Context:**
- Repository: {{ repo_name }}
- Branch: {{ branch_name }}
- Base Directory: {{ project_path }}

## Instructions

### 1. Understand the Subtask
- Review the subtask description and requirements
- Check if all dependencies are completed
- Understand how this subtask fits into the overall issue

### 2. Implementation Guidelines
Based on the subtask type:

**ANALYZE:**
- Investigate the codebase and identify patterns
- Document findings and recommendations
- Create detailed analysis reports

**SETUP:**
- Set up necessary project structure
- Install dependencies or configure environment
- Create boilerplate code or configuration files

**IMPLEMENT:**
- Write the core functionality
- Follow existing code patterns and conventions
- Ensure clean, maintainable code

**TEST:**
- Write comprehensive tests
- Ensure good test coverage
- Run tests and verify they pass

**REFACTOR:**
- Improve code quality and structure
- Maintain existing functionality
- Update tests if necessary

**DOCUMENTATION:**
- Write clear, comprehensive documentation
- Update existing docs if needed
- Include code examples where appropriate

**REVIEW:**
- Code review and quality checks
- Verify implementation meets requirements
- Suggest improvements if needed

### 3. Execution Steps
1. Start with TODO list to track your progress
2. Read relevant existing code to understand context
3. Implement the changes following project conventions
4. Test your changes (if applicable)
5. Update documentation (if needed)
6. Commit changes with clear message referencing subtask

### 4. Output Requirements
- Complete the specific subtask requirements
- Follow project coding standards
- Ensure all tests pass
- Provide clear commit messages
- Update subtask status appropriately

### 5. Error Handling
- If you encounter blockers, document them clearly
- If dependencies are missing, note what's needed
- If requirements are unclear, implement best interpretation

## Success Criteria
- Subtask requirements are fully implemented
- Code follows project conventions
- Tests pass (where applicable)
- Documentation is updated (where needed)
- Changes are properly committed

Remember: Focus only on this specific subtask. Do not implement features outside the scope of this subtask.