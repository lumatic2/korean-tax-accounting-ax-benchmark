import baselineData from "../data/leaderboard-public.json";
import authorityData from "../data/authority-rag-public.json";
import LeaderboardView from "@/components/leaderboard-view";

function buildView(data, viewMeta) {
  const rankRep = data.ranking.report;
  const pubRep = data.public_sample.report;
  const disc = data.ranking.discrimination;
  const models = data.meta.models;
  const pins = data.version_pins || {};

  const rows = models
    .map((m) => ({
      model: m,
      holdout: rankRep.by_model[m]?.avg_total ?? null,
      public: pubRep.by_model[m]?.avg_total ?? null,
      holdoutN: rankRep.by_model[m]?.n ?? 0,
      publicN: pubRep.by_model[m]?.n ?? 0,
      holdoutModes: rankRep.by_model[m]?.by_mode ?? {},
      publicModes: pubRep.by_model[m]?.by_mode ?? {},
      grades: rankRep.by_model[m]?.grades ?? {},
      dims: rankRep.by_model[m]?.by_dimension ?? {},
      domains: rankRep.by_model[m]?.by_domain ?? {},
      pin: pins[m] || {},
    }))
    .sort((a, b) => (b.holdout ?? -1) - (a.holdout ?? -1))
    .map((r, i) => ({ ...r, rank: i + 1 })); // holdout 순위 고정(정렬과 무관하게 표기)

  const allDims = [...new Set(rows.flatMap((r) => Object.keys(r.dims)))].sort();
  const allDomains = [
    ...new Set(rows.flatMap((r) => Object.keys(r.domains))),
  ].sort();

  return {
    ...viewMeta,
    rows,
    allDims,
    allDomains,
    disc,
    meta: data.meta,
    errorsPublic: data.errors_public || [],
    errorsHoldoutAgg: data.errors_holdout_agg || { by_type: {} },
  };
}

// 서버 컴포넌트: JSON → 표 행 가공(랭킹은 holdout 기준, ADR 0009). 인터랙션은 client view.
export default function Page() {
  const views = [
    buildView(baselineData, {
      key: "closed_book",
      label: "Closed Book",
      badge: "ranking eligible",
      rankBadge: "holdout ranked",
      title: "K-TaxBench 리더보드",
      description:
        "한국 회계·세무 AI 실무 신뢰도 평가. 순위는 비공개 holdout 평균, 공개셋은 과적합 감시용 보조 지표로 분리합니다.",
      notice:
        "현재 `gpt-5.5`는 302문항 closed-book refresh, 기존 Claude 행은 2026-06-11 기준 closed/RAG 혼합 측정입니다. dataset/mode/pin을 함께 읽어야 합니다.",
    }),
    buildView(authorityData, {
      key: "authority_rag",
      label: "Authority RAG",
      badge: "separate view",
      rankBadge: "holdout measured",
      title: "K-TaxBench Authority RAG",
      description:
        "Benchmark-provided authority pack을 읽은 모델 답안을 별도 평가합니다. closed_book baseline과 평균을 섞지 않습니다.",
      notice:
        "`authority_rag-v1`은 아직 ranking-eligible이 아닙니다. frozen source pack과 Codex clean judge 기준의 별도 측정값으로 해석해야 합니다.",
    }),
  ];

  return (
    <LeaderboardView
      views={views}
    />
  );
}
