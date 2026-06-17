/**
 * 정적 export (GitHub Pages). project pages 서브경로용 basePath는 배포 시 env로.
 *   PAGES_BASE_PATH=/ktaxbench-leaderboard npm run build
 */
const basePath = process.env.PAGES_BASE_PATH || "";

/** @type {import('next').NextConfig} */
export default {
  output: "export",
  basePath,
  trailingSlash: true,
  images: { unoptimized: true },
};
