// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { FiGithub } from 'react-icons/fi'
import { GiMagnifyingGlass } from 'react-icons/gi'
import { ImImages } from 'react-icons/im'
import { SiClaude, SiOllama } from 'react-icons/si'
import { Link } from 'react-router-dom'
import { ROUTES } from '@/config'
import styles from './landing.module.scss'

export function Component(): React.ReactElement {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Vuemantic</h1>
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
        <div className={styles.sections}>
          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <GiMagnifyingGlass />
            </div>
            <h2 className={styles.sectionTitle}>Semantic Search</h2>
            <p className={styles.sectionText}>
              Natural language queries like "red car" or "funny meme". Vision
              models analyze image/video content with vector embeddings for
              semantic similarity using pgvector.
            </p>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <ImImages />
            </div>
            <h2 className={styles.sectionTitle}>Media Management</h2>
            <p className={styles.sectionText}>
              AI Analysis: Upload images and videos. Vision models extract
              features, generate descriptions, and create vector embeddings for
              semantic search.
            </p>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <SiOllama />
            </div>
            <h2 className={styles.sectionTitle}>Technology Stack</h2>
            <p className={styles.sectionText}>
              Qwen2.5-VL for vision analysis, bge-m3 for embeddings. PostgreSQL +
              pgvector for vector search. Ollama for local model inference. React
              + TypeScript frontend.
            </p>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <SiClaude />
            </div>
            <h2 className={styles.sectionTitle}>Coming Soon</h2>
            <p className={styles.sectionText}>
              MCP Server: Model Context Protocol integration. Let AI assistants
              query your media collection through standardized tool interfaces.
            </p>
          </section>
        </div>

        <div className={styles.actions}>
          <Link to={ROUTES.LOGIN} className={styles.button}>
            Open Demo
          </Link>
          <a
            href="/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.buttonOutline}
          >
            API Documentation
          </a>
        </div>
      </div>
    </div>
  )
}

Component.displayName = 'Landing'
