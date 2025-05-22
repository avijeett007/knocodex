import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/user-guide/getting-started">
            Get Started
          </Link>
          <Link
            className="button button--outline button--lg button--primary"
            to="/docs/user-guide/subtask-workflow"
            style={{ marginLeft: '15px' }}>
            Subtask Workflow
          </Link>
          <Link
            className="button button--outline button--lg button--info"
            href="https://github.com/avijeett007/knocodex"
            style={{ marginLeft: '15px' }}>
            GitHub
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Autonomous Coding with AI Agents`}
      description="Knocodex is an open-source Python library for autonomous coding with AI agents that simplifies complex development workflows through subtask automation.">
      <HomepageHeader />
      <main>
        <div className="container margin-top--lg">
          <div className="row">
            <div className="col col--8 col--offset-2">
              <div className="text--center margin-bottom--lg">
                <h2>Revolutionize Your Development Workflow</h2>
                <p>
                  Knocodex integrates AI-powered coding assistance with workflow automation to help
                  developers tackle complex tasks more efficiently. Break down GitHub issues into manageable
                  subtasks and execute them in the optimal order with intelligent dependency management.
                </p>
              </div>
            </div>
          </div>
        </div>
        <HomepageFeatures />
        <div className="container margin-top--lg">
          <div className="row">
            <div className="col col--10 col--offset-1">
              <div className="card margin-bottom--lg" style={{ padding: '2rem', backgroundColor: '#f6f8fa' }}>
                <div className="card__header">
                  <h3>Ready to streamline your development process?</h3>
                </div>
                <div className="card__body">
                  <p>
                    Install Knocodex today and transform how your team handles development tasks. Integrate with
                    GitHub, break down issues into subtasks, and let AI assist in solving complex problems.
                  </p>
                  <pre><code>pip install knocodex</code></pre>
                </div>
                <div className="card__footer">
                  <Link
                    className="button button--primary button--block"
                    to="/docs/user-guide/installation">
                    Installation Guide
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </Layout>
  );
}
