import { useEffect, useState } from 'react'
import Head from 'next/head'
import Header from '@/components/Header'
import Terminal from '@/components/Terminal'
import WaitlistForm from '@/components/WaitlistForm'
import ComparisonTable from '@/components/ComparisonTable'
import FAQ from '@/components/FAQ'
import HireSection from '@/components/HireSection'
import Footer from '@/components/Footer'

export default function Home() {
  const [gridPoints, setGridPoints] = useState<{ x: number, y: number, delay: number }[]>([])

  useEffect(() => {
    // Create grid points for the background effect
    const points = []
    const count = 50
    for (let i = 0; i < count; i++) {
      points.push({
        x: Math.random() * 100,
        y: Math.random() * 100,
        delay: Math.random() * 2
      })
    }
    setGridPoints(points)
  }, [])

  return (
    <>
      <Head>
        <title>Knocodex - Your AI-powered Junior Developer</title>
        <meta name="description" content="Knocodex is an open-source Python library that provides autonomous coding capabilities using AI agents." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* Grid points for background effect */}
      {gridPoints.map((point, index) => (
        <div
          key={index}
          className="grid-point"
          style={{
            left: `${point.x}%`,
            top: `${point.y}%`,
            animationDelay: `${point.delay}s`
          }}
        />
      ))}

      <Header />

      <main>
        {/* Hero Section */}
        <section className="hero-section relative overflow-hidden py-16 md:py-24">
          {/* Animated code background */}
          <div className="absolute inset-0 opacity-10 z-0">
            <div className="code-rain"></div>
          </div>

          <div className="container mx-auto px-4 relative z-10">
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-6xl font-bold mb-4">
                Your AI-powered <span className="text-primary-500">Junior Developer</span>
              </h1>
              <p className="text-xl md:text-2xl max-w-3xl mx-auto mb-8">
                Knocodex transforms your development workflow with autonomous coding capabilities using AI agents.
              </p>
              <div className="flex flex-wrap gap-4 justify-center mb-12">
                <a href="#terminal" className="btn-primary text-lg px-6 py-3">
                  Try it out
                </a>
                <a href="https://github.com/avijeett007/knocodex" className="btn-secondary text-lg px-6 py-3">
                  GitHub
                </a>
              </div>
            </div>

            <div className="max-w-4xl mx-auto">
              <div className="relative">
                {/* Glowing effect behind terminal */}
                <div className="absolute -inset-1 bg-primary-500 rounded-lg opacity-20 blur-xl"></div>

                {/* Terminal with auto-typing demo */}
                <Terminal autoType={true} fullSize={true} />

                {/* Terminal reflection */}
                <div className="h-4 bg-gradient-to-b from-primary-900/50 to-transparent rounded-b-lg mt-1"></div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="section bg-black/30">
          <div className="container mx-auto">
            <h2 className="section-title">Key Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="card">
                <h3 className="text-xl font-bold mb-2">🤖 AI-Powered</h3>
                <p>Leverage the power of Claude and other AI models to understand and implement code.</p>
              </div>
              <div className="card">
                <h3 className="text-xl font-bold mb-2">🔄 GitHub Integration</h3>
                <p>Automatically process issues, implement solutions, and create pull requests.</p>
              </div>
              <div className="card">
                <h3 className="text-xl font-bold mb-2">⚙️ Autonomous Workflow</h3>
                <p>Let Knocodex handle routine coding tasks while you focus on high-level design.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Terminal Demo Section */}
        <section id="terminal" className="section relative">
          {/* Code background pattern */}
          <div className="absolute inset-0 opacity-5 z-0 overflow-hidden">
            <pre className="text-xs text-primary-500 whitespace-pre-wrap">
              {`
def main():
    """Main entry point for the application."""
    try:
        data = process_data("input.csv")
        model = PredictionModel()
        predictions = model.predict(data)
        print(f"Generated {len(predictions)} predictions")
    except FileNotFoundError:
        print("Error: input.csv file not found")
        return 1
    return 0

def export_data(data, filename, format="csv"):
    """Export data to a file in the specified format."""
    if format == "csv":
        with open(filename, "w") as f:
            for row in data:
                f.write(",".join(str(x) for x in row) + "\\n")
    elif format == "json":
        import json
        with open(filename, "w") as f:
            json.dump(data, f)
    else:
        raise ValueError(f"Unsupported format: {format}")
    return True
              `}
            </pre>
          </div>

          <div className="container mx-auto relative z-10">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="section-title">Interactive Developer Experience</h2>
              <p className="text-xl mb-12 max-w-3xl mx-auto">
                Experience the power of Knocodex through our interactive terminal. Type commands, view code, and see how Knocodex can transform your development workflow.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className="text-2xl font-bold mb-4 text-primary-300">Try These Commands:</h3>
                <div className="bg-black/50 rounded-lg p-6 border border-primary-500/30">
                  <ul className="space-y-4 font-mono">
                    <li className="flex items-start">
                      <span className="text-primary-500 mr-2">$</span>
                      <div>
                        <code className="text-white">knocodex init</code>
                        <p className="text-sm text-gray-400 mt-1">Initialize a new project with Knocodex</p>
                      </div>
                    </li>
                    <li className="flex items-start">
                      <span className="text-primary-500 mr-2">$</span>
                      <div>
                        <code className="text-white">cat src/main.py</code>
                        <p className="text-sm text-gray-400 mt-1">View the main Python file</p>
                      </div>
                    </li>
                    <li className="flex items-start">
                      <span className="text-primary-500 mr-2">$</span>
                      <div>
                        <code className="text-white">knocodex fix</code>
                        <p className="text-sm text-gray-400 mt-1">Let Knocodex fix bugs in your code</p>
                      </div>
                    </li>
                    <li className="flex items-start">
                      <span className="text-primary-500 mr-2">$</span>
                      <div>
                        <code className="text-white">knocodex implement</code>
                        <p className="text-sm text-gray-400 mt-1">Implement a new feature with AI</p>
                      </div>
                    </li>
                    <li className="flex items-start">
                      <span className="text-primary-500 mr-2">$</span>
                      <div>
                        <code className="text-white">demo</code>
                        <p className="text-sm text-gray-400 mt-1">Run a full demo workflow</p>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>

              <div className="relative">
                {/* Glowing effect */}
                <div className="absolute -inset-1 bg-primary-500 rounded-lg opacity-10 blur-lg"></div>
                <Terminal fullSize={true} />
              </div>
            </div>
          </div>
        </section>

        {/* Waitlist Section */}
        <section className="section bg-black/30">
          <div className="container mx-auto">
            <h2 className="section-title">Join the Waitlist</h2>
            <p className="text-center mb-8">
              Be the first to know when we launch new features and updates.
            </p>
            <div className="max-w-md mx-auto">
              <WaitlistForm />
            </div>
          </div>
        </section>

        {/* Comparison Section */}
        <section className="section">
          <div className="container mx-auto">
            <h2 className="section-title">How Knocodex Compares</h2>
            <p className="text-center mb-8">
              See how Knocodex stacks up against other AI coding tools.
            </p>
            <ComparisonTable />
          </div>
        </section>

        {/* Hire Section */}
        <section className="section bg-black/30">
          <div className="container mx-auto">
            <HireSection />
          </div>
        </section>

        {/* FAQ Section */}
        <section className="section">
          <div className="container mx-auto">
            <h2 className="section-title">Frequently Asked Questions</h2>
            <div className="max-w-3xl mx-auto">
              <FAQ />
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </>
  )
}
