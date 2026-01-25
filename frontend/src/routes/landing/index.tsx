/**
 * ©AngelaMos | 2026
 * index.tsx
 */

import { FiGithub } from 'react-icons/fi'
import { Link } from 'react-router-dom'
import { ROUTES } from '@/config'
import styles from './landing.module.scss'

export function Component(): React.ReactElement {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>VueMantic</h1>
        <p className={styles.subtitle}>Smart Multimodal Search</p>
        <a
          href="https://github.com/CarterPerez-dev/vuemantics"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.github}
          aria-label="View source on GitHub"
        >
          <FiGithub />
        </a>
      </header>

      <div className={styles.content}>
        <p className={styles.description}>
          Search your photos and videos using natural language. Powered by AI
          vision models and vector embeddings for semantic understanding.
        </p>

        <div className={styles.sections}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>AI-Powered Search</h2>
            <ul className={styles.features}>
              <li>Natural language queries: "blonde hair", "black jacket"</li>
              <li>Vision models analyze image/video content</li>
              <li>Vector embeddings for semantic similarity</li>
              <li>pgvector for fast similarity search</li>
              <li>Real-time processing with async queues</li>
            </ul>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Media Management</h2>
            <ul className={styles.features}>
              <li>Upload images and videos</li>
              <li>Automatic AI analysis and tagging</li>
              <li>Smart thumbnail generation</li>
              <li>Efficient local storage</li>
              <li>Batch processing support</li>
            </ul>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Technology Stack</h2>
            <ul className={styles.features}>
              <li>FastAPI backend with async processing</li>
              <li>PostgreSQL + pgvector for embeddings</li>
              <li>OpenAI & Gemini AI models</li>
              <li>React 19 + TypeScript frontend</li>
              <li>Redis for caching and queues</li>
            </ul>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Coming Soon</h2>
            <ul className={styles.features}>
              <li>Open-source local model support</li>
              <li>Video frame analysis</li>
              <li>Improved similarity tuning</li>
              <li>Batch search operations</li>
            </ul>
          </section>
        </div>

        <div className={styles.actions}>
          <Link to={ROUTES.REGISTER} className={styles.button}>
            Get Started
          </Link>
          <a
            href="/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.buttonOutline}
          >
            API Docs
          </a>
        </div>
      </div>
    </div>
  )
}

Component.displayName = 'Landing'
