// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { FiGithub } from 'react-icons/fi'
import { LuBrain, LuDatabase, LuImage, LuSearch } from 'react-icons/lu'
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
          Search your photos and videos using natural language. Abuses AI
          vision models and vector embeddings for semantic understanding.
        </p>

        <div className={styles.sections}>
          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <LuSearch />
            </div>
            <h2 className={styles.sectionTitle}>Semantic Search</h2>
            <p className={styles.sectionText}>
              Natural language queries like "red car" or "funny meme". Vision models analyze image/video content with vector embeddings for semantic similarity using pgvector.
            </p>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <LuImage />
            </div>
            <h2 className={styles.sectionTitle}>Media Management</h2>
            <p className={styles.sectionText}>
              Upload images and videos with automatic AI analysis and tagging. Smart thumbnail generation, efficient local storage, and batch processing support.
            </p>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <LuDatabase />
            </div>
            <h2 className={styles.sectionTitle}>Technology Stack</h2>
            <p className={styles.sectionText}>
              Qwen2.5-VL for vision analysis, bge-m3 for embeddings. PostgreSQL + pgvector for vector search. Ollama for local model inference. React + TypeScript frontend.
            </p>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionIcon}>
              <LuBrain />
            </div>
            <h2 className={styles.sectionTitle}>Coming Soon</h2>
            <p className={styles.sectionText}>
              MCP Server: Model Context Protocol integration. Let AI assistants query your media collection through standardized tool interfaces.
            </p>
          </section>
        </div>

        <div className={styles.actions}>
          <Link to={ROUTES.LOGIN} className={styles.button}>
            Login
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
