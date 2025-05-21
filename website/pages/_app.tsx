import '@/styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>Knocodex - Your AI-powered Junior Developer</title>
        <meta name="description" content="Knocodex is an open-source Python library that provides autonomous coding capabilities using AI agents." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/favicon.svg" />
        <meta name="theme-color" content="#0073ff" />
        <meta property="og:title" content="Knocodex - Your AI-powered Junior Developer" />
        <meta property="og:description" content="Knocodex is an open-source Python library that provides autonomous coding capabilities using AI agents." />
        <meta property="og:image" content="/knocodex-logo.svg" />
        <meta property="og:url" content="https://knocodex.dev" />
        <meta name="twitter:card" content="summary_large_image" />
      </Head>
      <div className="grid-background"></div>
      <Component {...pageProps} />
    </>
  )
}
