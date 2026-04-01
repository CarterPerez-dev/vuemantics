// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { Link } from 'react-router-dom'
import { ROUTES } from '@/config'
import styles from './landing.module.scss'

export function Component(): React.ReactElement {
  return (
    <div className={styles.page}>
      <header className={styles.strip}>
        <div className={styles.stripLeft}>
          <span>MEDIA SEMANTICS</span>
          <span>ANGELAMOS</span>
          <span>SERIAL: VM—01</span>
        </div>
        <div className={styles.stripRight}>
          <span>©2026</span>
          <span>V2.1.4 —</span>
        </div>
      </header>

      <main className={styles.field}>
        <div className={styles.registration}>&gt;&gt;&gt;&gt;</div>

        <div className={styles.badge}>VM—01</div>

        <div className={styles.hero}>
          <h1 className={styles.title}>
            VUEMANTIC<span className={styles.reg}> ®</span>
          </h1>
          <div className={styles.subtitle}>
            <span>SEMANTIC</span>
            <span>MEDIA</span>
            <span>ANALYSIS</span>
          </div>
        </div>

        <div className={styles.rule}>
          <div className={styles.ruleAccent} />
        </div>

        <div className={styles.lower}>
          <div className={styles.specsCard}>
            <div className={styles.specsHeader}>
              <span>SYSTEM SPECIFICATIONS</span>
              <span>VM-SYS-01</span>
            </div>
            <div className={styles.specsGrid}>
              <div className={styles.spec}>
                <span className={styles.specLabel}>VISION MODEL</span>
                <span className={styles.specValue}>Qwen2.5-VL-7B</span>
              </div>
              <div className={styles.spec}>
                <span className={styles.specLabel}>EMBEDDINGS</span>
                <span className={styles.specValue}>bge-m3 · 1024d</span>
              </div>
              <div className={styles.spec}>
                <span className={styles.specLabel}>VECTOR STORE</span>
                <span className={styles.specValue}>pgvector</span>
              </div>
              <div className={styles.spec}>
                <span className={styles.specLabel}>INFERENCE</span>
                <span className={styles.specValue}>Ollama · Local</span>
              </div>
            </div>
          </div>

          <div className={styles.body}>
            <p>
              Multimodal vision analysis and vector embedding for semantic search
              across personal media libraries. Natural language queries.
              Self-hosted. Offline-capable.
            </p>
          </div>
        </div>

        <div className={styles.ghost} aria-hidden="true">
          COSINE SIMILARITY
        </div>
      </main>

      <footer className={styles.bottom}>
        <Link to={ROUTES.LOGIN} className={styles.enter}>
          ENTER SYSTEM
        </Link>
        <div className={styles.links}>
          <a
            href="https://github.com/CarterPerez-dev/vuemantics"
            target="_blank"
            rel="noopener noreferrer"
          >
            SOURCE ↗
          </a>
          <span className={styles.linkDivider}>|</span>
          <a href="/api/docs" target="_blank" rel="noopener noreferrer">
            API DOCS ↗
          </a>
        </div>
      </footer>
    </div>
  )
}

Component.displayName = 'Landing'
