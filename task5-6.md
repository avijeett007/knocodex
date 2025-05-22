# Implementation Plan for Issue #5: Subtask-Based Workflow

## Issue Summary

**Title**: Let knocodex handle a request with subtasks  
**Issue #**: 5  
**Labels**: knocodex  

The issue requests transforming knocodex from a single-task processor to a subtask-based workflow system. Instead of creating one monolithic plan, knocodex should:

1. Break down GitHub issues into multiple small subtasks
2. Process each subtask as a separate Redis queue job
3. Maintain proper branch workflow (single branch per issue)
4. Implement proper project/task/subtask relationship tracking
5. Support multiple projects with separate queue management

## Current Architecture Analysis

**Current Workflow:**
- Single GitHub issue → Single Redis task → Monolithic analysis & implementation
- Two-phase processing: analysis (`/project:analyze-github-issue`) → implementation (`/project:implement-github-issue`)
- Branch creation handled ad-hoc within Claude Code execution
- No subtask breakdown or granular tracking

**Current Limitations:**
- Single Redis queue for all projects
- No subtask decomposition
- Limited project isolation
- No intermediate progress tracking

## Required Changes

### 1. Subtask Decomposition System
- Create new subtask analyzer that breaks down GitHub issues
- Define subtask types (branch, analysis, implementation, testing, documentation, commit, PR)
- Implement subtask dependency management
- Add subtask context preservation for end-goal awareness

### 2. Enhanced Queue Management
- Implement project-specific Redis queues
- Add subtask queue processing with dependency resolution
- Create queue coordination to prevent concurrent issue processing per project
- Implement subtask status tracking and progress reporting

### 3. Workflow Orchestration
- Design new workflow engine for subtask execution
- Implement branch lifecycle management (create once, work throughout)
- Add progress tracking and intermediate state management
- Create subtask result aggregation system

### 4. Project Isolation
- Implement project-specific worker processes
- Add project identification and routing
- Create separate Redis namespace per project
- Implement project-aware configuration management

## Implementation Steps

### Phase 1: Core Subtask Framework
1. **Create subtask data models**
   - Define `Subtask` class with type, status, dependencies, context
   - Create `SubtaskPlan` class to hold issue breakdown
   - Add subtask state management (pending, in_progress, completed, failed)

2. **Implement subtask analyzer**
   - Create `SubtaskAnalyzer` class that parses GitHub issues
   - Use MCP tools for internet research when needed
   - Generate subtask breakdown with dependencies
   - Preserve issue context for each subtask

3. **Update Redis queue system**
   - Modify queue utilities to support project-specific queues
   - Add subtask enqueueing with dependency tracking
   - Implement subtask status persistence
   - Create queue coordination logic

### Phase 2: Workflow Engine
1. **Create subtask workflow orchestrator**
   - Implement `SubtaskWorkflowEngine` class
   - Add dependency resolution algorithm
   - Create subtask execution coordination
   - Implement branch lifecycle management

2. **Update worker process**
   - Modify worker to handle subtask processing
   - Add subtask type-specific handlers
   - Implement progress reporting
   - Add error handling and retry logic for subtasks

3. **Enhance command system**
   - Create new custom Claude commands for subtask types
   - Update existing commands to work with subtask context
   - Add subtask-aware documentation generation
   - Implement granular commit strategies

### Phase 3: Project Isolation
1. **Implement project-aware queue management**
   - Create project-specific Redis namespaces
   - Add project identification middleware
   - Implement project-aware worker spawning
   - Add cross-project resource management

2. **Update configuration system**
   - Extend config to support project-specific settings
   - Add project discovery and registration
   - Implement multi-project service management
   - Create project-aware logging and monitoring

### Phase 4: Integration & Testing
1. **Update CLI interface**
   - Modify `knocodex start` to support multi-project mode
   - Add subtask monitoring commands
   - Implement project-specific status reporting  
   - Add subtask queue management commands

2. **Comprehensive testing**
   - Create unit tests for subtask decomposition
   - Add integration tests for workflow orchestration
   - Test multi-project isolation
   - Implement end-to-end workflow tests

## Files to be Modified

### Core Framework Files
- `knocodex/agent_manager.py` - Add subtask workflow orchestration
- `knocodex/templates/worker.py` - Update for subtask processing
- `knocodex/templates/main_loop.py` - Modify for subtask enqueueing
- `knocodex/utils/redis_utils.py` - Add project-specific queue support
- `knocodex/config.py` - Extend for project-aware configuration

### New Files to Create
- `knocodex/subtask_analyzer.py` - Issue-to-subtask decomposition
- `knocodex/subtask_workflow.py` - Workflow orchestration engine
- `knocodex/models/subtask.py` - Subtask data models
- `knocodex/utils/project_utils.py` - Project identification and management
- `knocodex/queue_coordinator.py` - Multi-project queue coordination

### Template Updates
- `knocodex/templates/commands/analyze-subtask.md` - New subtask analysis command
- `knocodex/templates/commands/implement-subtask.md` - New subtask implementation command
- `knocodex/templates/commands/test-subtask.md` - New subtask testing command
- `knocodex/templates/commands/document-subtask.md` - New subtask documentation command

### CLI & Configuration
- `knocodex/cli.py` - Add subtask monitoring and management commands
- Configuration files - Add project-specific settings schema

## Testing Approach

### Unit Tests
- **Subtask Analyzer Tests**: Test issue decomposition logic
- **Workflow Engine Tests**: Test subtask dependency resolution
- **Queue Management Tests**: Test project-specific queue operations
- **Data Model Tests**: Test subtask state management

### Integration Tests
- **End-to-End Workflow Tests**: Test complete subtask processing flow
- **Multi-Project Tests**: Test project isolation and resource management
- **Dependency Resolution Tests**: Test complex subtask dependency chains
- **Error Handling Tests**: Test failure recovery and retry logic

### Manual Testing Scenarios
1. **Single Issue Subtask Breakdown**: Test issue decomposition accuracy
2. **Multi-Subtask Execution**: Test sequential subtask processing
3. **Multi-Project Isolation**: Test concurrent project processing
4. **Branch Lifecycle**: Test single branch throughout subtask execution
5. **Error Recovery**: Test subtask failure and recovery scenarios

## Risk Assessment & Mitigation

### High-Risk Areas
1. **Queue Coordination Complexity**: Risk of deadlocks or race conditions
   - Mitigation: Use Redis transactions and proper locking mechanisms
2. **Subtask Dependency Resolution**: Risk of circular dependencies
   - Mitigation: Implement dependency cycle detection
3. **Project Isolation**: Risk of resource conflicts between projects
   - Mitigation: Strict namespace separation and resource allocation

### Backward Compatibility
- Maintain existing CLI interface for single-issue processing
- Provide migration path for existing queue data
- Support legacy command structure during transition

## Success Criteria

1. **Functional Requirements**
   - Issues successfully decomposed into logical subtasks
   - Subtasks execute in correct dependency order
   - Single branch maintained throughout issue processing
   - Multiple projects can run concurrently without interference

2. **Performance Requirements**
   - Subtask overhead < 10% of total processing time
   - Queue coordination latency < 500ms
   - Project isolation with minimal resource overhead

3. **Quality Requirements**
   - All existing functionality preserved
   - Comprehensive test coverage (>90%)
   - Clear documentation for new workflow
   - Robust error handling and recovery

This plan transforms knocodex into a sophisticated subtask-based workflow system while maintaining project isolation and proper developer workflow practices.




# Implementation Plan for Issue #6: Enable Aider Support

## Issue Summary

**Issue #6: Enable aider support**

Currently, knocodex only works with Claude Code. The goal is to integrate aider as an alternative tool to support agentic coding workflows. This will enable the system to work with different open source and cheaper models, particularly Gemini models, while maintaining the same autonomous coding workflow.

**Key Requirements:**
- Research and integrate aider.chat as an alternative to Claude Code
- Support non-interactive terminal mode for automation
- Maintain compatibility with existing knocodex workflow
- Enable support for Gemini and other open source models

## Required Changes

### 1. Core Architecture Changes
- **Add aider integration layer**: Create an abstraction that allows switching between Claude Code and aider
- **Model configuration**: Support multiple AI model providers (Gemini, OpenAI, local models)
- **CLI configuration**: Add options to choose between Claude Code and aider backends

### 2. Configuration Management
- **Model selection**: Environment variables and config files for model choice
- **API key management**: Support for multiple API providers
- **Cost optimization**: Intelligent model selection based on task complexity

### 3. Worker Process Enhancement
- **Backend abstraction**: Modify worker to support both Claude Code and aider execution
- **Command translation**: Map existing commands to aider equivalents
- **Output parsing**: Handle different output formats from both tools

## Implementation Steps

### Phase 1: Research and Foundation (Completed)
- [x] Research aider capabilities and documentation
- [x] Analyze integration requirements
- [x] Create detailed implementation plan

### Phase 2: Core Integration
1. **Create aider wrapper module** (`knocodex/aider_wrapper.py`)
   - Python API wrapper for aider operations
   - Command-line interface wrapper
   - Configuration management

2. **Extend configuration system** (`knocodex/config.py`)
   - Add aider-specific configuration options
   - Model selection and API key management
   - Backend selection (claude-code vs aider)

3. **Update worker process** (`knocodex/subtask_worker.py`)
   - Abstract backend selection
   - Implement aider execution paths
   - Maintain compatibility with existing Claude Code paths

### Phase 3: Command Integration
1. **Update command templates** (`knocodex/templates/commands/`)
   - Modify existing command templates to work with aider
   - Create aider-specific command variations
   - Maintain backward compatibility

2. **Enhance CLI interface** (`knocodex/cli.py`)
   - Add backend selection options
   - Model configuration commands
   - Status and monitoring for both backends

### Phase 4: Testing and Optimization
1. **Create test suite for aider integration**
2. **Performance benchmarking between backends**
3. **Cost optimization strategies**
4. **Documentation updates**

## Files to be Modified

### New Files to Create
```
knocodex/
├── aider_wrapper.py           # Aider integration wrapper
├── models/
│   └── ai_backend.py          # Backend abstraction layer
└── templates/
    └── aider_commands/        # Aider-specific command templates
        ├── analyze-github-issue.md
        ├── implement-github-issue.md
        └── document-project.md
```

### Existing Files to Modify
```
knocodex/
├── config.py                  # Add aider configuration options
├── cli.py                     # Add backend selection commands
├── subtask_worker.py          # Add aider execution support
├── agent_manager.py           # Backend selection logic
└── workflow_engine.py         # Backend abstraction integration
```

### Configuration Files
```
knocodex/
└── templates/
    ├── config_template.sh     # Add aider environment variables
    └── aider_config.yml       # Aider-specific configuration template
```

## Technical Implementation Details

### 1. Aider Integration Wrapper
```python
class AiderWrapper:
    def __init__(self, config):
        self.model = config.get('aider_model', 'gemini-exp')
        self.api_key = config.get('aider_api_key')
        
    def execute_command(self, command, files=None):
        """Execute aider command in non-interactive mode"""
        
    def analyze_issue(self, issue_content):
        """Analyze GitHub issue using aider"""
        
    def implement_solution(self, plan, files):
        """Implement solution using aider"""
```

### 2. Backend Abstraction
```python
class AIBackend:
    @staticmethod
    def create_backend(backend_type, config):
        if backend_type == 'aider':
            return AiderWrapper(config)
        elif backend_type == 'claude-code':
            return ClaudeCodeWrapper(config)
        else:
            raise ValueError(f"Unknown backend: {backend_type}")
```

### 3. Configuration Schema
```yaml
# .knocodex/config.yml
ai_backend: aider  # or claude-code
aider:
  model: gemini-exp
  api_key: ${GEMINI_API_KEY}
  auto_commits: true
  stream: false
claude_code:
  model: claude-3-5-sonnet
  api_key: ${ANTHROPIC_API_KEY}
```

## Testing Approach

### 1. Unit Tests
- **aider_wrapper.py**: Test all aider integration functions
- **Backend abstraction**: Test backend selection and switching
- **Configuration**: Test config parsing and validation

### 2. Integration Tests
- **End-to-end workflow**: Test complete issue analysis → implementation cycle
- **Backend comparison**: Compare outputs from both backends
- **Error handling**: Test failure scenarios and fallbacks

### 3. Performance Testing
- **Speed benchmarks**: Compare execution times
- **Cost analysis**: Track API usage and costs
- **Quality metrics**: Compare code quality outputs

### 4. Manual Testing
- **GitHub issue processing**: Test with real GitHub issues
- **Model switching**: Test different AI models
- **Configuration scenarios**: Test various config combinations

## Success Criteria

### 1. Functional Requirements
- [x] Aider can be selected as backend via configuration
- [x] All existing knocodex commands work with aider backend
- [x] Support for Gemini and other open source models
- [x] Non-interactive mode works reliably

### 2. Performance Requirements
- Aider backend performance is comparable to Claude Code
- Cost optimization shows measurable savings
- Model switching works seamlessly

### 3. Compatibility Requirements
- Existing workflows continue to work with Claude Code
- Configuration is backward compatible
- No breaking changes to CLI interface

## Risk Mitigation

### 1. Technical Risks
- **Aider API changes**: Pin to specific aider version, monitor updates
- **Model availability**: Implement fallback model selection
- **Integration complexity**: Maintain simple abstraction layer

### 2. Performance Risks
- **Slower execution**: Implement caching and optimization
- **Higher costs**: Implement cost monitoring and limits
- **Quality degradation**: Implement quality checks and comparison

### 3. Compatibility Risks
- **Breaking changes**: Maintain backward compatibility
- **Configuration drift**: Implement validation and migration
- **Command differences**: Maintain command equivalence mapping

## Future Enhancements

### 1. Advanced Features
- **Hybrid mode**: Use both backends for comparison
- **Smart routing**: Route tasks to optimal backend
- **Cost optimization**: Dynamic model selection based on budget

### 2. Model Ecosystem
- **Local models**: Ollama integration for offline operation
- **Specialized models**: Task-specific model selection
- **Model fine-tuning**: Custom model training for specific codebases

### 3. Monitoring and Analytics
- **Performance dashboards**: Track backend performance metrics
- **Cost tracking**: Detailed API usage and cost analysis
- **Quality metrics**: Code quality and success rate tracking

## Conclusion

This implementation plan provides a comprehensive roadmap for integrating aider into knocodex while maintaining backward compatibility with Claude Code. The phased approach ensures minimal disruption to existing workflows while providing significant benefits in terms of model diversity, cost optimization, and open source support.

The key success factor will be maintaining a clean abstraction layer that allows seamless switching between backends while preserving the autonomous coding workflow that makes knocodex effective.