import "./globals.css";

export const metadata = {
  title: "K-TaxBench 리더보드",
  description:
    "한국 회계·세무 AI 실무 신뢰도 평가 — 공개 리더보드 (read-only). 순위는 비공개 holdout 기준, 공개셋 점수 별도 표기 (ADR 0009).",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
