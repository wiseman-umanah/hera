/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // add other env variables here as you add them
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
