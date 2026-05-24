import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 중 백엔드(FastAPI)로의 프록시.
// VITE_API_BASE_URL이 설정되면 client.ts가 절대 URL을 직접 사용하고,
// 미설정 시 아래 프록시를 통해 /api 를 로컬 서버로 넘긴다.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
