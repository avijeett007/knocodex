import React from 'react'

const ComparisonTable = () => {
  const features = [
    {
      name: 'AI Code Completion',
      knocodex: true,
      cursor: true,
      windsurf: true,
      aiide: true,
    },
    {
      name: 'Autonomous Issue Resolution',
      knocodex: true,
      cursor: false,
      windsurf: false,
      aiide: false,
    },
    {
      name: 'GitHub Integration',
      knocodex: true,
      cursor: true,
      windsurf: true,
      aiide: true,
    },
    {
      name: 'Automatic PR Creation',
      knocodex: true,
      cursor: false,
      windsurf: false,
      aiide: false,
    },
    {
      name: 'Documentation Generation',
      knocodex: true,
      cursor: false,
      windsurf: false,
      aiide: true,
    },
    {
      name: 'Task Queue Management',
      knocodex: true,
      cursor: false,
      windsurf: false,
      aiide: false,
    },
    {
      name: 'Multiple AI Agent Support',
      knocodex: true,
      cursor: false,
      windsurf: false,
      aiide: false,
    },
    {
      name: 'Open Source',
      knocodex: true,
      cursor: false,
      windsurf: false,
      aiide: false,
    },
  ]

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-black/50 border border-gray-700 rounded-lg overflow-hidden">
        <thead>
          <tr className="bg-primary-900/50">
            <th className="py-3 px-4 text-left">Feature</th>
            <th className="py-3 px-4 text-center">Knocodex</th>
            <th className="py-3 px-4 text-center">Cursor</th>
            <th className="py-3 px-4 text-center">Windsurf</th>
            <th className="py-3 px-4 text-center">AI IDE</th>
          </tr>
        </thead>
        <tbody>
          {features.map((feature, index) => (
            <tr key={index} className={index % 2 === 0 ? 'bg-black/30' : 'bg-black/10'}>
              <td className="py-3 px-4 border-t border-gray-700">{feature.name}</td>
              <td className="py-3 px-4 text-center border-t border-gray-700">
                {feature.knocodex ? (
                  <span className="text-green-500 text-xl">✓</span>
                ) : (
                  <span className="text-red-500 text-xl">✗</span>
                )}
              </td>
              <td className="py-3 px-4 text-center border-t border-gray-700">
                {feature.cursor ? (
                  <span className="text-green-500 text-xl">✓</span>
                ) : (
                  <span className="text-red-500 text-xl">✗</span>
                )}
              </td>
              <td className="py-3 px-4 text-center border-t border-gray-700">
                {feature.windsurf ? (
                  <span className="text-green-500 text-xl">✓</span>
                ) : (
                  <span className="text-red-500 text-xl">✗</span>
                )}
              </td>
              <td className="py-3 px-4 text-center border-t border-gray-700">
                {feature.aiide ? (
                  <span className="text-green-500 text-xl">✓</span>
                ) : (
                  <span className="text-red-500 text-xl">✗</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ComparisonTable
