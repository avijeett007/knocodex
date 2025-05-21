import { useState } from 'react'
import Link from 'next/link'

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="bg-black/80 backdrop-blur-md sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <img src="/knocodex-text-logo.svg" alt="Knocodex" className="h-8" />
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-8">
            <Link href="/#features" className="text-gray-300 hover:text-white transition-colors">
              Features
            </Link>
            <Link href="/#terminal" className="text-gray-300 hover:text-white transition-colors">
              Demo
            </Link>
            <Link href="https://docs.knocodex.dev" className="text-gray-300 hover:text-white transition-colors">
              Docs
            </Link>
            <Link href="https://github.com/avijeett007/knocodex" className="text-gray-300 hover:text-white transition-colors">
              GitHub
            </Link>
            <Link href="https://youtube.com/@kno2gether" className="text-gray-300 hover:text-white transition-colors">
              YouTube
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-gray-300 hover:text-white"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden py-4 border-t border-gray-700">
            <ul className="space-y-4">
              <li>
                <Link
                  href="/#features"
                  className="block text-gray-300 hover:text-white transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Features
                </Link>
              </li>
              <li>
                <Link
                  href="/#terminal"
                  className="block text-gray-300 hover:text-white transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Demo
                </Link>
              </li>
              <li>
                <Link
                  href="https://docs.knocodex.dev"
                  className="block text-gray-300 hover:text-white transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Docs
                </Link>
              </li>
              <li>
                <Link
                  href="https://github.com/avijeett007/knocodex"
                  className="block text-gray-300 hover:text-white transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  GitHub
                </Link>
              </li>
              <li>
                <Link
                  href="https://youtube.com/@kno2gether"
                  className="block text-gray-300 hover:text-white transition-colors"
                  onClick={() => setIsMenuOpen(false)}
                >
                  YouTube
                </Link>
              </li>
            </ul>
          </nav>
        )}
      </div>
    </header>
  )
}

export default Header
