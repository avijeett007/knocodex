# Knocodex Website

This is the official website for Knocodex, hosted at [knocodex.dev](https://knocodex.dev).

## Features

- Interactive terminal-like interface inspired by Encom Boardroom
- Demonstration of Knocodex commands
- Waitlist signup form with Supabase integration
- Information about Knocodex+ professional services
- FAQ and comparison with other AI IDEs

## Getting Started

### Prerequisites

- Node.js 14.x or higher
- npm or yarn

### Installation

1. Clone the repository:

```bash
git clone https://github.com/avijeett007/knocodex.git
cd knocodex/website
```

2. Install dependencies:

```bash
npm install
# or
yarn install
```

3. Set up environment variables:

Create a `.env.local` file in the website directory with the following variables:

```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

4. Start the development server:

```bash
npm run dev
# or
yarn dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser to see the website.

## Project Structure

- `pages/`: Next.js pages
- `components/`: React components
- `public/`: Static assets
- `styles/`: CSS and styling
- `lib/`: Utility functions and API clients
- `hooks/`: Custom React hooks

## Key Components

- `Terminal`: Interactive terminal component that mimics Knocodex CLI
- `WaitlistForm`: Email collection form for the waitlist
- `ComparisonTable`: Comparison with other AI IDEs
- `FAQ`: Frequently asked questions
- `HireSection`: Information about Knocodex+ professional services

## Deployment

The website is automatically deployed to [knocodex.dev](https://knocodex.dev) when changes are pushed to the main branch.

## Contributing

Contributions to the website are welcome! Please feel free to submit a pull request with your changes.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

The website is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
