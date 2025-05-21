import { useState } from 'react'

const FAQ = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null)

  const faqs = [
    {
      question: 'What is Knocodex?',
      answer: 'Knocodex is an open-source Python library that provides autonomous coding capabilities using AI agents. It acts as a junior developer that can understand, implement, and improve code based on natural language instructions.'
    },
    {
      question: 'How does Knocodex work?',
      answer: 'Knocodex uses AI agents (currently Claude Code, with Aider support coming soon) to analyze code, understand requirements, and implement solutions. It can monitor GitHub issues, automatically implement solutions, and create pull requests.'
    },
    {
      question: 'Is Knocodex free to use?',
      answer: 'Yes, Knocodex is open-source and free to use under the MIT License. However, some of the AI services it integrates with (like Claude) may require their own subscriptions or API keys.'
    },
    {
      question: 'What are the system requirements for Knocodex?',
      answer: 'Knocodex requires Python 3.6 or higher, Redis (for task queue), Git (for version control), a GitHub account (for GitHub integration), and Claude API access (for Claude agent).'
    },
    {
      question: 'Can Knocodex work with any programming language?',
      answer: 'Yes, Knocodex can work with any programming language that the underlying AI model (like Claude) supports. This includes most popular languages such as Python, JavaScript, Java, C++, etc.'
    },
    {
      question: 'How does Knocodex compare to other AI coding tools?',
      answer: 'Knocodex focuses on autonomous workflow integration rather than just code completion. It\'s designed to work as a junior developer that can handle complete tasks from issue analysis to PR creation.'
    },
    {
      question: 'Is there enterprise support available for Knocodex?',
      answer: 'Yes, we offer Knocodex+ Professional Services for enterprise support, custom development, and training. Contact us for more information.'
    },
    {
      question: 'How can I contribute to Knocodex?',
      answer: 'Contributions are welcome! You can contribute by submitting pull requests, reporting bugs, suggesting features, or improving documentation. Check out our GitHub repository for more details.'
    }
  ]

  const toggleFaq = (index: number) => {
    if (openIndex === index) {
      setOpenIndex(null)
    } else {
      setOpenIndex(index)
    }
  }

  return (
    <div>
      {faqs.map((faq, index) => (
        <div key={index} className="faq-item">
          <div 
            className="faq-question"
            onClick={() => toggleFaq(index)}
          >
            <span>{faq.question}</span>
            <span>{openIndex === index ? '−' : '+'}</span>
          </div>
          {openIndex === index && (
            <div className="faq-answer">
              {faq.answer}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default FAQ
