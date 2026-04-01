// ===================
// © AngelaMos | 2026
// index.tsx
// ===================

import { useEffect } from 'react'
import { toast } from 'sonner'
import { useProviderSettings, useSetProvider, useTriggerReembed } from '@/api/hooks'
import type { EmbeddingProvider } from '@/api/types'
import { useReembedProgress, useSocket } from '@/core/socket'
import styles from './settings.module.scss'

export function Component(): React.ReactElement {
  const { data: providerData, isLoading } = useProviderSettings()
  const setProvider = useSetProvider()
  const triggerReembed = useTriggerReembed()

  const { reembedState, handleReembedProgress, handleReembedComplete, resetReembed } =
    useReembedProgress()

  useSocket({
    enabled: true,
    onReembedProgress: handleReembedProgress,
    onReembedComplete: handleReembedComplete,
  })

  useEffect(() => {
    if (reembedState.complete) {
      toast.success(
        `Re-embed complete: ${reembedState.processed} processed, ${reembedState.skipped} skipped, ${reembedState.failed} failed`
      )
    }
  }, [reembedState.complete, reembedState.processed, reembedState.skipped, reembedState.failed])

  const handleProviderChange = (provider: EmbeddingProvider): void => {
    setProvider.mutate(provider, {
      onSuccess: () => toast.success(`Switched to ${provider} provider`),
      onError: () => toast.error('Failed to switch provider'),
    })
  }

  const handleReembed = (): void => {
    resetReembed()
    triggerReembed.mutate(undefined, {
      onSuccess: () => toast.info('Re-embed job started'),
      onError: () => toast.error('Failed to start re-embed job'),
    })
  }

  const reembedPercent =
    reembedState.total > 0
      ? Math.round((reembedState.processed / reembedState.total) * 100)
      : 0

  const isLocal = providerData?.provider === 'local'
  const isGemini = providerData?.provider === 'gemini'

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div className={styles.pageHeaderLeft}>
          <span className={styles.pageLabel}>SYSTEM CONFIG</span>
          <span className={styles.pageMeta}>CFG—01</span>
        </div>
      </div>

      <div className={styles.body}>
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionLabel}>EMBEDDING PROVIDER</span>
            <span className={styles.sectionCode}>
              ACTIVE: {providerData?.provider?.toUpperCase() ?? '—'}
            </span>
          </div>

          <div className={styles.sectionBody}>
            <p className={styles.sectionDesc}>
              Choose how uploads are embedded. Switching providers does not
              re-embed existing uploads.
            </p>

            {isLoading ? (
              <div className={styles.loading}>LOADING...</div>
            ) : (
              <div className={styles.providers}>
                <button
                  type="button"
                  className={`${styles.provider} ${isLocal ? styles.providerActive : ''}`}
                  onClick={() => handleProviderChange('local')}
                  disabled={setProvider.isPending}
                >
                  <div className={styles.providerStatus}>
                    <div className={`${styles.providerDot} ${isLocal ? styles.providerDotActive : ''}`} />
                    <span className={`${styles.providerName} ${isLocal ? styles.providerNameActive : ''}`}>
                      LOCAL
                    </span>
                  </div>
                  <span className={styles.providerDetail}>
                    QWEN + BGE-M3 · 1024 DIMS
                  </span>
                  <span className={styles.providerCount}>
                    {providerData?.local_count ?? 0} UPLOADS
                  </span>
                </button>

                <button
                  type="button"
                  className={`${styles.provider} ${isGemini ? styles.providerActive : ''}`}
                  onClick={() => handleProviderChange('gemini')}
                  disabled={setProvider.isPending}
                >
                  <div className={styles.providerStatus}>
                    <div className={`${styles.providerDot} ${isGemini ? styles.providerDotActive : ''}`} />
                    <span className={`${styles.providerName} ${isGemini ? styles.providerNameActive : ''}`}>
                      GEMINI
                    </span>
                  </div>
                  <span className={styles.providerDetail}>
                    EMBEDDING-2-PREVIEW · 1536 DIMS
                  </span>
                  <span className={styles.providerCount}>
                    {providerData?.gemini_count ?? 0} UPLOADS
                  </span>
                </button>
              </div>
            )}
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionLabel}>RE-EMBED ALL</span>
            <span className={styles.sectionCode}>OPS—01</span>
          </div>

          <div className={styles.sectionBody}>
            <p className={styles.sectionDesc}>
              Re-process all uploads with the currently active provider.
              Runs in background.
            </p>

            <div className={styles.opsPanel}>
              {reembedState.active && (
                <div className={styles.progressBlock}>
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${reembedPercent}%` }}
                    />
                  </div>
                  <div className={styles.progressStats}>
                    <span>
                      {reembedState.processed} / {reembedState.total}
                    </span>
                    <span>{reembedPercent}%</span>
                  </div>
                  {(reembedState.skipped > 0 || reembedState.failed > 0) && (
                    <div className={styles.progressDetail}>
                      {reembedState.skipped > 0 && (
                        <span className={styles.skipped}>
                          {reembedState.skipped} SKIPPED
                        </span>
                      )}
                      {reembedState.failed > 0 && (
                        <span className={styles.failed}>
                          {reembedState.failed} FAILED
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {reembedState.complete && (
                <div className={styles.completeMsg}>
                  COMPLETE — {reembedState.processed} PROCESSED
                </div>
              )}

              <button
                type="button"
                className={`${styles.reembedBtn} ${reembedState.active ? styles.reembedBtnActive : ''}`}
                onClick={handleReembed}
                disabled={triggerReembed.isPending || reembedState.active}
              >
                {reembedState.active && <div className={styles.pulseDot} />}
                {reembedState.active ? 'RE-EMBEDDING...' : 'RE-EMBED ALL'}
              </button>
            </div>
          </div>
        </section>
        {providerData?.cost_estimate && (
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <span className={styles.sectionLabel}>GEMINI COST ESTIMATE</span>
              <span className={styles.sectionCode}>BILLING—01</span>
            </div>

            <div className={styles.sectionBody}>
              <p className={styles.sectionDesc}>
                Estimated embedding cost based on current Gemini uploads.
                Video estimate uses worst-case {providerData.cost_estimate.max_frames_per_video} frames per video.
              </p>

              <div className={styles.costGrid}>
                <div className={styles.costRow}>
                  <span className={styles.costLabel}>IMAGES</span>
                  <span className={styles.costValue}>
                    {providerData.cost_estimate.gemini_image_count}
                  </span>
                  <span className={styles.costRate}>
                    × ${providerData.cost_estimate.cost_per_image}
                  </span>
                  <span className={styles.costTotal}>
                    ${providerData.cost_estimate.estimated_image_cost.toFixed(4)}
                  </span>
                </div>

                <div className={styles.costRow}>
                  <span className={styles.costLabel}>VIDEOS</span>
                  <span className={styles.costValue}>
                    {providerData.cost_estimate.gemini_video_count}
                  </span>
                  <span className={styles.costRate}>
                    × ${providerData.cost_estimate.max_cost_per_video} max
                  </span>
                  <span className={styles.costTotal}>
                    ${providerData.cost_estimate.estimated_video_cost.toFixed(4)}
                  </span>
                </div>

                <div className={`${styles.costRow} ${styles.costRowTotal}`}>
                  <span className={styles.costLabel}>TOTAL</span>
                  <span className={styles.costValue} />
                  <span className={styles.costRate} />
                  <span className={styles.costTotal}>
                    ${providerData.cost_estimate.estimated_total_cost.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

Component.displayName = 'Settings'
