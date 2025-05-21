import { useEffect, useRef, useState } from 'react'
import { useSound } from '@/hooks/useSound'

interface TerminalProps {
  fullSize?: boolean
  autoType?: boolean
}

interface TerminalLine {
  type: 'input' | 'output' | 'error' | 'success' | 'code' | 'prompt'
  content: string
}

const Terminal: React.FC<TerminalProps> = ({ fullSize = false, autoType = false }) => {
  const [input, setInput] = useState('')
  const [history, setHistory] = useState<TerminalLine[]>([
    { type: 'output', content: '┌──────────────────────────────────────────────────┐' },
    { type: 'output', content: '│                                                  │' },
    { type: 'output', content: '│   🚀 Welcome to Knocodex Terminal v0.1.0 🚀      │' },
    { type: 'output', content: '│   Your AI-powered Junior Developer               │' },
    { type: 'output', content: '│                                                  │' },
    { type: 'output', content: '└──────────────────────────────────────────────────┘' },
    { type: 'output', content: 'Type "help" to see available commands or try a demo workflow.' },
  ])
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isTyping, setIsTyping] = useState(false)
  const [currentTypingIndex, setCurrentTypingIndex] = useState(0)
  const [demoCommands, setDemoCommands] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const terminalBodyRef = useRef<HTMLDivElement>(null)

  // Sound effects
  const keyPressSound = useSound('/sounds/key-press.mp3', { volume: 0.2 })
  const commandSuccessSound = useSound('/sounds/command-success.mp3', { volume: 0.3 })
  const commandErrorSound = useSound('/sounds/command-error.mp3', { volume: 0.3 })

  const commands = {
    help: {
      description: 'Show available commands',
      execute: () => {
        return [
          { type: 'output', content: 'Available commands:' },
          { type: 'output', content: '  help                - Show available commands' },
          { type: 'output', content: '  knocodex            - Show information about Knocodex' },
          { type: 'output', content: '  knocodex setup      - Set up Knocodex globally' },
          { type: 'output', content: '  knocodex init       - Initialize a project' },
          { type: 'output', content: '  knocodex start      - Start the autonomous agent' },
          { type: 'output', content: '  knocodex stop       - Stop the autonomous agent' },
          { type: 'output', content: '  knocodex status     - Check agent status' },
          { type: 'output', content: '  knocodex fix        - Fix a bug using AI' },
          { type: 'output', content: '  knocodex implement  - Implement a feature using AI' },
          { type: 'output', content: '  demo                - Run a demo workflow' },
          { type: 'output', content: '  ls                  - List files in current directory' },
          { type: 'output', content: '  cat [file]          - Display file contents' },
          { type: 'output', content: '  git [args]          - Run git commands' },
          { type: 'output', content: '  clear               - Clear the terminal' },
        ]
      }
    },
    clear: {
      description: 'Clear the terminal',
      execute: () => {
        setHistory([])
        return []
      }
    },
    demo: {
      description: 'Run a demo workflow',
      execute: () => {
        startDemoWorkflow()
        return [
          { type: 'output', content: 'Starting demo workflow...' },
        ]
      }
    },
    ls: {
      description: 'List files in current directory',
      execute: () => {
        return [
          { type: 'output', content: 'project/' },
          { type: 'output', content: '├── .git/' },
          { type: 'output', content: '├── .knocodex/' },
          { type: 'output', content: '├── src/' },
          { type: 'output', content: '│   ├── main.py' },
          { type: 'output', content: '│   ├── utils.py' },
          { type: 'output', content: '│   └── models.py' },
          { type: 'output', content: '├── tests/' },
          { type: 'output', content: '│   └── test_main.py' },
          { type: 'output', content: '├── README.md' },
          { type: 'output', content: '└── requirements.txt' },
        ]
      }
    },
    cat: {
      description: 'Display file contents',
      execute: (args: string[]) => {
        if (args.length === 0) {
          return [{ type: 'error', content: 'Usage: cat [file]' }]
        }

        const file = args[0]

        if (file === 'src/main.py') {
          return [
            { type: 'output', content: '# src/main.py' },
            { type: 'code', content: 'from utils import process_data' },
            { type: 'code', content: 'from models import PredictionModel' },
            { type: 'code', content: '' },
            { type: 'code', content: 'def main():' },
            { type: 'code', content: '    """Main entry point for the application."""' },
            { type: 'code', content: '    data = process_data("input.csv")' },
            { type: 'code', content: '    model = PredictionModel()' },
            { type: 'code', content: '    predictions = model.predict(data)' },
            { type: 'code', content: '    print(f"Generated {len(predictions)} predictions")' },
            { type: 'code', content: '' },
            { type: 'code', content: 'if __name__ == "__main__":' },
            { type: 'code', content: '    main()' },
          ]
        } else if (file === 'README.md') {
          return [
            { type: 'output', content: '# Project README' },
            { type: 'output', content: '' },
            { type: 'output', content: 'This is a sample project that demonstrates Knocodex capabilities.' },
            { type: 'output', content: '' },
            { type: 'output', content: '## Installation' },
            { type: 'output', content: '' },
            { type: 'output', content: '```bash' },
            { type: 'output', content: 'pip install -r requirements.txt' },
            { type: 'output', content: '```' },
          ]
        } else {
          return [{ type: 'error', content: `File not found: ${file}` }]
        }
      }
    },
    git: {
      description: 'Run git commands',
      execute: (args: string[]) => {
        if (args.length === 0) {
          return [{ type: 'error', content: 'Usage: git [command]' }]
        }

        const command = args[0]

        if (command === 'status') {
          return [
            { type: 'output', content: 'On branch main' },
            { type: 'output', content: 'Your branch is up to date with \'origin/main\'.' },
            { type: 'output', content: '' },
            { type: 'output', content: 'Changes not staged for commit:' },
            { type: 'output', content: '  (use "git add <file>..." to update what will be committed)' },
            { type: 'output', content: '  (use "git restore <file>..." to discard changes in working directory)' },
            { type: 'output', content: '        modified:   src/main.py' },
            { type: 'output', content: '' },
            { type: 'output', content: 'no changes added to commit (use "git add" and/or "git commit -a")' },
          ]
        } else {
          return [{ type: 'output', content: `Simulating: git ${args.join(' ')}` }]
        }
      }
    },
    knocodex: {
      description: 'Show information about Knocodex',
      execute: (args: string[]) => {
        if (args.length === 0) {
          return [
            { type: 'output', content: 'Knocodex - Your AI-powered Junior Developer' },
            { type: 'output', content: 'Version: 0.1.0' },
            { type: 'output', content: 'Use "knocodex help" to see available commands.' },
          ]
        }

        switch (args[0]) {
          case 'setup':
            return simulateSetup()
          case 'init':
            return simulateInit()
          case 'start':
            return simulateStart()
          case 'stop':
            return simulateStop()
          case 'status':
            return simulateStatus()
          case 'fix':
            return simulateFix()
          case 'implement':
            return simulateImplement()
          default:
            return [
              { type: 'error', content: `Unknown command: knocodex ${args[0]}` },
              { type: 'output', content: 'Use "help" to see available commands.' },
            ]
        }
      }
    }
  }

  const simulateSetup = () => {
    return [
      { type: 'output', content: 'Setting up Knocodex globally...' },
      { type: 'output', content: 'Checking requirements...' },
      { type: 'success', content: '✓ Python 3.9 found' },
      { type: 'success', content: '✓ pip found' },
      { type: 'success', content: '✓ Redis found' },
      { type: 'output', content: 'Setting up GitHub authentication...' },
      { type: 'output', content: 'Please enter your GitHub token:' },
      { type: 'output', content: '****************************************' },
      { type: 'success', content: '✓ GitHub authentication successful' },
      { type: 'output', content: 'Configuring Claude MCP servers...' },
      { type: 'success', content: '✓ Claude MCP servers configured' },
      { type: 'output', content: 'Creating global configuration file...' },
      { type: 'success', content: '✓ Global configuration created at ~/.knocodex/config.json' },
      { type: 'success', content: 'Knocodex setup complete!' },
    ]
  }

  const simulateInit = () => {
    return [
      { type: 'output', content: 'Initializing project for Knocodex...' },
      { type: 'output', content: 'Creating project-specific configuration...' },
      { type: 'success', content: '✓ Project configuration created at .knocodex/config.json' },
      { type: 'output', content: 'Setting up custom Claude commands...' },
      { type: 'success', content: '✓ Custom commands configured' },
      { type: 'output', content: 'Importing MCP servers from Claude Desktop...' },
      { type: 'success', content: '✓ MCP servers imported' },
      { type: 'success', content: 'Project initialization complete!' },
    ]
  }

  const simulateStart = () => {
    return [
      { type: 'output', content: 'Starting Knocodex autonomous agent...' },
      { type: 'output', content: 'Starting Redis server...' },
      { type: 'success', content: '✓ Redis server started' },
      { type: 'output', content: 'Starting worker...' },
      { type: 'success', content: '✓ Worker started' },
      { type: 'output', content: 'Starting GitHub issue monitor...' },
      { type: 'success', content: '✓ Now monitoring GitHub issues with the "knocodex" label' },
      { type: 'success', content: 'Knocodex agent started!' },
    ]
  }

  const simulateStop = () => {
    return [
      { type: 'output', content: 'Stopping Knocodex autonomous agent...' },
      { type: 'output', content: 'Stopping worker...' },
      { type: 'success', content: '✓ Worker stopped' },
      { type: 'output', content: 'Stopping Redis server...' },
      { type: 'success', content: '✓ Redis server stopped' },
      { type: 'success', content: 'Knocodex agent stopped!' },
    ]
  }

  const simulateStatus = () => {
    return [
      { type: 'output', content: 'Checking Knocodex agent status...' },
      { type: 'output', content: 'Agent type: claude' },
      { type: 'output', content: 'Worker running: Yes' },
      { type: 'output', content: 'Redis running: Yes' },
      { type: 'output', content: 'Dashboard running: No' },
    ]
  }

  const simulateFix = () => {
    return [
      { type: 'output', content: 'Analyzing bug in src/main.py...' },
      { type: 'output', content: 'Identifying issue...' },
      { type: 'output', content: 'Found potential bug: Missing error handling for file not found' },
      { type: 'output', content: 'Generating fix...' },
      { type: 'code', content: 'def main():' },
      { type: 'code', content: '    """Main entry point for the application."""' },
      { type: 'code', content: '    try:' },
      { type: 'code', content: '        data = process_data("input.csv")' },
      { type: 'code', content: '        model = PredictionModel()' },
      { type: 'code', content: '        predictions = model.predict(data)' },
      { type: 'code', content: '        print(f"Generated {len(predictions)} predictions")' },
      { type: 'code', content: '    except FileNotFoundError:' },
      { type: 'code', content: '        print("Error: input.csv file not found")' },
      { type: 'code', content: '        return 1' },
      { type: 'code', content: '    return 0' },
      { type: 'success', content: '✓ Bug fixed successfully' },
      { type: 'output', content: 'Creating pull request...' },
      { type: 'success', content: '✓ Pull request #42 created: "Fix file not found error handling"' },
    ]
  }

  const simulateImplement = () => {
    return [
      { type: 'output', content: 'Implementing new feature: Add data export functionality' },
      { type: 'output', content: 'Analyzing project structure...' },
      { type: 'output', content: 'Generating implementation plan...' },
      { type: 'output', content: '1. Add export function to utils.py' },
      { type: 'output', content: '2. Update main.py to use the export function' },
      { type: 'output', content: '3. Add tests for the export function' },
      { type: 'output', content: 'Implementing changes...' },
      { type: 'code', content: '# Adding to utils.py' },
      { type: 'code', content: 'def export_data(data, filename, format="csv"):' },
      { type: 'code', content: '    """Export data to a file in the specified format."""' },
      { type: 'code', content: '    if format == "csv":' },
      { type: 'code', content: '        with open(filename, "w") as f:' },
      { type: 'code', content: '            for row in data:' },
      { type: 'code', content: '                f.write(",".join(str(x) for x in row) + "\\n")' },
      { type: 'code', content: '    elif format == "json":' },
      { type: 'code', content: '        import json' },
      { type: 'code', content: '        with open(filename, "w") as f:' },
      { type: 'code', content: '            json.dump(data, f)' },
      { type: 'code', content: '    else:' },
      { type: 'code', content: '        raise ValueError(f"Unsupported format: {format}")' },
      { type: 'code', content: '    return True' },
      { type: 'success', content: '✓ Feature implemented successfully' },
      { type: 'output', content: 'Creating pull request...' },
      { type: 'success', content: '✓ Pull request #43 created: "Add data export functionality"' },
    ]
  }

  // Demo workflow with auto-typing
  const startDemoWorkflow = () => {
    if (isTyping) return;

    const demoSequence = [
      'knocodex init',
      'ls',
      'cat src/main.py',
      'knocodex fix',
      'git status',
      'knocodex implement',
      'knocodex start'
    ];

    setDemoCommands(demoSequence);
    setIsTyping(true);
    setCurrentTypingIndex(0);

    // Start the demo sequence
    typeNextCommand(demoSequence, 0);
  }

  const typeNextCommand = (demoCommands: string[], index: number) => {
    if (index >= demoCommands.length) {
      setIsTyping(false);
      return;
    }

    const command = demoCommands[index];
    let currentText = '';
    let charIndex = 0;

    // Clear the input first
    setInput('');

    // Type the command character by character
    const typingInterval = setInterval(() => {
      if (charIndex < command.length) {
        // Play key press sound occasionally (not for every character)
        if (Math.random() > 0.7) {
          keyPressSound.play();
        }

        currentText += command[charIndex];
        setInput(currentText);
        charIndex++;
      } else {
        clearInterval(typingInterval);

        // Execute the command after typing
        setTimeout(() => {
          const args = command.trim().split(' ');
          const cmd = args[0];
          const cmdArgs = args.slice(1);

          // Add the command to history
          setHistory(prev => [...prev, { type: 'input', content: `$ ${command}` }]);

          // Add a "processing" indicator
          setHistory(prev => [...prev, { type: 'prompt', content: 'Processing...' }]);

          // Save to command history
          setCommandHistory([command, ...commandHistory]);
          setInput('');

          // Process command with delay
          setTimeout(() => {
            // Remove the processing indicator
            setHistory(prev => prev.filter(line => !(line.type === 'prompt' && line.content === 'Processing...')));

            // Get command result
            let result: TerminalLine[] = [];

            if (cmd in commands) {
              result = commands[cmd as keyof typeof commands].execute(cmdArgs) as TerminalLine[];
            }

            // Add results with typing effect
            if (result.length > 0) {
              // Use our enhanced typing effect function
              addResultsWithTypingEffect(result);

              // Move to the next command after a delay
              setTimeout(() => {
                typeNextCommand(demoCommands, index + 1);
              }, result.length * 300 + 500); // Delay based on number of lines
            } else {
              // If no results, move to next command
              setTimeout(() => {
                typeNextCommand(demoCommands, index + 1);
              }, 500);
            }
          }, 500); // Processing delay
        }, 300); // Delay after typing
      }
    }, 100); // Character typing speed
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim()) return

    // If demo is running, don't allow manual input
    if (isTyping) return

    // Add the input to history immediately
    const commandInput = input.trim()
    setHistory(prev => [...prev, { type: 'input', content: `$ ${commandInput}` }])

    // Add a "processing" indicator
    setHistory(prev => [...prev, { type: 'prompt', content: 'Processing...' }])

    // Process command
    const args = commandInput.split(' ')
    const cmd = args[0]
    const cmdArgs = args.slice(1)

    // Save the command to history
    setCommandHistory([commandInput, ...commandHistory])
    setHistoryIndex(-1)
    setInput('')

    // Simulate processing delay
    setTimeout(() => {
      // Remove the processing indicator
      setHistory(prev => prev.filter(line => !(line.type === 'prompt' && line.content === 'Processing...')))

      // Get command result
      let result: TerminalLine[] = []

      if (cmd in commands) {
        result = commands[cmd as keyof typeof commands].execute(cmdArgs) as TerminalLine[]
      } else if (cmd) {
        // Play error sound for unknown commands
        commandErrorSound.play()

        result = [
          { type: 'error', content: `Command not found: ${cmd}` },
          { type: 'output', content: 'Type "help" to see available commands.' }
        ]

        // Easter egg for non-knocodex commands
        if (cmd !== 'knocodex') {
          result.push({ type: 'output', content: 'Subscribe to kno2gether to learn more about knocodex: https://youtube.com/@kno2gether' })
        }
      }

      // Add results with typing effect
      addResultsWithTypingEffect(result)
    }, 500) // Initial processing delay
  }

  // Function to add results with a typing effect
  const addResultsWithTypingEffect = (results: TerminalLine[]) => {
    if (results.length === 0) return

    // For success/error messages, play appropriate sound
    if (results[0].type === 'success') {
      commandSuccessSound.play();
    } else if (results[0].type === 'error') {
      commandErrorSound.play();
    }

    // Add results one by one with a typing effect
    let index = 0;

    const addNextResult = () => {
      if (index < results.length) {
        const result = results[index];

        // For code blocks, add character by character
        if (result.type === 'code') {
          let content = result.content;
          let charIndex = 0;
          let displayedContent = '';

          // Add a placeholder for the code that will be typed
          const codePlaceholder: TerminalLine = {
            type: 'code',
            content: ''
          };

          setHistory(prev => [...prev, codePlaceholder]);

          // Type the code character by character
          const typeInterval = setInterval(() => {
            if (charIndex < content.length) {
              displayedContent += content[charIndex];

              // Update the last line with the new content
              setHistory(prev => {
                const newHistory = [...prev];
                newHistory[newHistory.length - 1] = {
                  type: 'code',
                  content: displayedContent
                };
                return newHistory;
              });

              charIndex++;

              // Occasionally play key sound
              if (Math.random() > 0.8) {
                keyPressSound.play();
              }
            } else {
              clearInterval(typeInterval);
              index++;
              setTimeout(addNextResult, 100);
            }
          }, 20); // Faster typing for code
        } else {
          // For regular output, add the whole line with a delay
          setHistory(prev => [...prev, result]);
          index++;

          // Add a random delay between lines for more natural feel
          setTimeout(addNextResult, Math.random() * 200 + 100);
        }
      }
    };

    addNextResult();
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Play key press sound for special keys
    if (['Enter', 'ArrowUp', 'ArrowDown', 'Tab'].includes(e.key)) {
      keyPressSound.play();
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault()
      const nextIndex = Math.min(historyIndex + 1, commandHistory.length - 1)
      if (nextIndex >= 0 && commandHistory[nextIndex]) {
        setHistoryIndex(nextIndex)
        setInput(commandHistory[nextIndex])
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      const nextIndex = Math.max(historyIndex - 1, -1)
      if (nextIndex >= 0) {
        setHistoryIndex(nextIndex)
        setInput(commandHistory[nextIndex])
      } else {
        setHistoryIndex(-1)
        setInput('')
      }
    }
  }

  useEffect(() => {
    // Focus the input when the component mounts
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    // Scroll to bottom when history changes
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight
    }
  }, [history])

  useEffect(() => {
    // Start auto-typing demo if autoType prop is true
    if (autoType && !isTyping) {
      setTimeout(() => {
        startDemoWorkflow();
      }, 1000);
    }
  }, [autoType]);

  return (
    <div className={`terminal-container ${fullSize ? 'w-full' : 'max-w-2xl mx-auto'} shadow-lg shadow-primary-500/20`}>
      <div className="terminal-header">
        <div className="flex items-center">
          <svg className="w-5 h-5 mr-2 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
          <span className="font-mono text-primary-300">knocodex@dev:~</span>
        </div>
        <div className="flex space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
      </div>
      <div
        className="terminal-body"
        ref={terminalBodyRef}
        style={{ height: fullSize ? '500px' : '350px' }}
        onClick={() => inputRef.current?.focus()}
      >
        {history.map((line, index) => (
          <div key={index} className={`terminal-line terminal-${line.type}`}>
            {line.type === 'code' ? (
              <pre className="pl-4 border-l-2 border-primary-500/50 text-green-300 font-mono">{line.content}</pre>
            ) : line.type === 'prompt' ? (
              <div className="text-primary-300 font-bold">{line.content}</div>
            ) : (
              line.content
            )}
          </div>
        ))}
        <form onSubmit={handleSubmit} className="flex items-center mt-2">
          <span className="terminal-prompt font-bold">$</span>
          <input
            ref={inputRef}
            type="text"
            className="terminal-input ml-2"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            disabled={isTyping}
            placeholder={isTyping ? "Demo running..." : "Type a command..."}
          />
          <span className="terminal-cursor animate-terminal-cursor"></span>
        </form>
      </div>
    </div>
  )
}

export default Terminal
