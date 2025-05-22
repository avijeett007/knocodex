# Analyze GitHub Issue Into Subtasks

Please analyze the GitHub issue and break it down into a comprehensive subtask plan.

## Instructions

1. **Fetch Issue Details**: Use the GitHub CLI to get the full issue information:
   ```bash
   gh issue view {{issue_number}} --json number,title,body,labels,assignees,milestone
   ```

2. **Analyze the Issue**: Examine the issue content to understand:
   - The core problem or feature request
   - Required technical changes
   - Dependencies between different parts
   - Testing requirements
   - Documentation needs

3. **Create Subtask Breakdown**: Break down the issue into logical subtasks that:
   - Are small enough to be completed independently (typically 1-4 hours each)
   - Have clear dependencies and execution order
   - Cover all aspects: analysis, implementation, testing, documentation
   - Can be executed by Claude Code in headless mode

4. **Generate Subtask Plan**: Create a detailed plan file at:
   `.knocodex/tasks/issue-{{issue_number}}-subtask-plan.json`

   The plan should follow this JSON structure:
   ```json
   {
     "issue_number": {{issue_number}},
     "title": "Issue title",
     "branch_name": "feature/issue-{{issue_number}}-description",
     "estimated_hours": 8,
     "subtasks": [
       {
         "id": "subtask-1",
         "title": "Analyze requirements and create technical design",
         "description": "Detailed description of what needs to be done",
         "type": "ANALYZE",
         "priority": 1,
         "dependencies": [],
         "estimated_minutes": 60,
         "files_to_modify": [],
         "acceptance_criteria": ["Criterion 1", "Criterion 2"]
       },
       {
         "id": "subtask-2", 
         "title": "Implement core functionality",
         "description": "Detailed implementation description",
         "type": "IMPLEMENT",
         "priority": 2,
         "dependencies": ["subtask-1"],
         "estimated_minutes": 120,
         "files_to_modify": ["file1.py", "file2.py"],
         "acceptance_criteria": ["Criterion 1", "Criterion 2"]
       }
     ]
   }
   ```

5. **Subtask Types**: Use these standard types:
   - `ANALYZE`: Research, planning, design work
   - `SETUP`: Environment setup, configuration
   - `IMPLEMENT`: Core code implementation
   - `TEST`: Writing and running tests
   - `REFACTOR`: Code cleanup and refactoring
   - `DOCUMENTATION`: Writing or updating docs
   - `REVIEW`: Code review and quality checks

6. **Dependency Rules**:
   - ANALYZE subtasks typically have no dependencies
   - SETUP subtasks come early in the process
   - IMPLEMENT subtasks depend on ANALYZE/SETUP
   - TEST subtasks depend on IMPLEMENT
   - DOCUMENTATION can run in parallel with testing
   - REVIEW comes near the end

7. **Create Summary**: After creating the subtask plan, create a human-readable summary at:
   `.knocodex/tasks/issue-{{issue_number}}-plan.md`

## Success Criteria

- [ ] Issue details fetched and analyzed
- [ ] Comprehensive subtask breakdown created
- [ ] JSON plan file created with proper structure
- [ ] Dependencies properly mapped
- [ ] Each subtask is appropriately sized
- [ ] All issue requirements covered by subtasks
- [ ] Summary document created for human review