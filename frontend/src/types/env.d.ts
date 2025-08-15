/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  //  more env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
