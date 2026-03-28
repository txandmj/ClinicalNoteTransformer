/// <reference types="vite/client" />

/** App-specific env vars (merged with Vite's ImportMetaEnv). */
interface ImportMetaEnv {
  readonly VITE_CLINICAL_API_KEY?: string;
}
