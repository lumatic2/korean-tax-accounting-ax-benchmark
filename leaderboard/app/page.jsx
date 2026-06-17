import data from "../data/leaderboard-public.json";

// 점수(0~100) → 히트맵 색 (빨강→노랑→초록). 채도↑·극단일수록 진하게.
function heat(score) {
  if (score == null) return "#f1f3f7";
  const h = Math.max(0, Math.min(120, (score / 100) * 120)); // 0=red,120=green
  // 중간(50)에서 가장 옅고 양 극단에서 진해지도록 명도 변조
  const dist = Math.abs(score - 50) / 50; // 0(중간)~1(극단)
  const light = 86 - dist * 16; // 86%(중간)~70%(극단)
  return `hsl(${h} 74% ${light}%)`;
}

function fmt(v) {
  return v == null ? "–" : v.toFixed(1);
}

function gradeStr(grades) {
  return Object.entries(grades || {})
    .sort()
    .map(([g, n]) => `${g}:${n}`)
    .join("  ");
}

export default function Page() {
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
      grades: rankRep.by_model[m]?.grades ?? {},
      dims: rankRep.by_model[m]?.by_dimension ?? {},
      domains: rankRep.by_model[m]?.by_domain ?? {},
      pin: pins[m] || {},
    }))
    .sort((a, b) => (b.holdout ?? -1) - (a.holdout ?? -1));

  const allDims = [
    ...new Set(rows.flatMap((r) => Object.keys(r.dims))),
  ].sort();
  const allDomains = [
    ...new Set(rows.flatMap((r) => Object.keys(r.domains))),
  ].sort();

  const flagOk = disc.flag === "ok";

  return (
    <div className="wrap">
      <header>
        <h1>K-TaxBench 리더보드</h1>
        <p>
          한국 회계·세무 AI 실무 신뢰도 평가 · 읽기전용 v1 · 순위는 비공개
          holdout 기준, 공개셋 점수는 별도 표기 (
          <a
            href="https://github.com/lumatic2/korean-tax-accounting-ax-benchmark/blob/main/docs/adr/0009-leaderboard-submission-policy.md"
            rel="noreferrer"
          >
            ADR 0009
          </a>
          )
        </p>
      </header>

      <div className="banner">
        <div>
          <div className="lab">변별 spread (holdout)</div>
          <div className="big">{disc.spread}</div>
        </div>
        <div>
          <div className="lab">range</div>
          <div className="big">
            {disc.range[0]}–{disc.range[1]}
          </div>
        </div>
        <div>
          <div className="lab">flag</div>
          <div className={`big ${flagOk ? "flag-ok" : "flag-bad"}`}>
            {disc.flag}
          </div>
        </div>
        <div>
          <div className="lab">평가 레코드</div>
          <div className="big">
            {data.meta.n_holdout_records + data.meta.n_public_records}
          </div>
        </div>
      </div>

      <section>
        <h2>모델 랭킹</h2>
        <p className="note">
          순위 = holdout 평균(과적합 방지). 공개셋 평균은 별도 컬럼 — 두 값의
          격차가 공개셋 과적합 신호. 각 모델은 버전핀으로 동결(append-only).
        </p>
        <div className="table-wrap" role="region" aria-label="모델 랭킹 표" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>모델</th>
                <th className="num">holdout 평균 (순위)</th>
                <th className="num">공개셋 평균</th>
                <th>등급분포 (holdout)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.model}>
                  <td className="num">{i + 1}</td>
                  <td>
                    <div className="model">{r.model}</div>
                    <div className="badges">
                      {(r.pin.prompt_version || []).map((v) => (
                        <span className="badge pin" key={"pv" + v}>
                          scaffold {v}
                        </span>
                      ))}
                      {(r.pin.modes || []).map((v) => (
                        <span className="badge" key={"md" + v}>
                          {v}
                        </span>
                      ))}
                      {(r.pin.accessed_at || []).map((v) => (
                        <span className="badge" key={"ac" + v}>
                          법령 {v}
                        </span>
                      ))}
                      <span className="badge ok">✓ 재현 검증</span>
                    </div>
                  </td>
                  <td className="num">
                    <strong>{fmt(r.holdout)}</strong>
                  </td>
                  <td className="num">{fmt(r.public)}</td>
                  <td>{gradeStr(r.grades)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="heat">
        <h2>차원별 평균 (holdout)</h2>
        <p className="note">7차원 루브릭 — 어느 축이 약한지(환각·계산·근거).</p>
        <div className="table-wrap" role="region" aria-label="차원별 평균 표" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>모델</th>
                {allDims.map((d) => (
                  <th className="num" key={d}>
                    {d}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.model}>
                  <td className="model">{r.model}</td>
                  {allDims.map((d) => (
                    <td
                      className="cell"
                      key={d}
                      style={{ background: heat(r.dims[d]) }}
                    >
                      {fmt(r.dims[d])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="heat">
        <h2>분야별 평균 (holdout)</h2>
        <div className="table-wrap" role="region" aria-label="분야별 평균 표" tabIndex={0}>
          <table>
            <thead>
              <tr>
                <th>모델</th>
                {allDomains.map((d) => (
                  <th className="num" key={d}>
                    {d}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.model}>
                  <td className="model">{r.model}</td>
                  {allDomains.map((d) => (
                    <td
                      className="cell"
                      key={d}
                      style={{ background: heat(r.domains[d]) }}
                    >
                      {fmt(r.domains[d])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2>대표 오류 사례</h2>
        <p className="note">
          공개셋은 문항 id 노출, holdout은 type별 카운트만(문항 비공개 — 해자
          보호).
        </p>
        <h3 style={{ fontSize: 14, color: "var(--navy-soft)" }}>
          공개셋 (id 표시)
        </h3>
        <ul className="errlist">
          {data.errors_public.slice(0, 12).map((e, i) => (
            <li key={i}>
              <span className="etype">{e.type}</span>
              <strong>{e.id}</strong> · {e.model}/{e.mode} — {e.detail}
            </li>
          ))}
          {data.errors_public.length === 0 && <li>공개셋 오류 없음</li>}
        </ul>
        <h3 style={{ fontSize: 14, color: "var(--navy-soft)" }}>
          holdout (집계 카운트)
        </h3>
        <ul className="errlist">
          {Object.entries(data.errors_holdout_agg.by_type).map(([t, n]) => (
            <li key={t}>
              <span className="etype">{t}</span> {n}건
            </li>
          ))}
        </ul>
      </section>

      <section className="policy">
        <h2>제출·운영 정책 (ADR 0009)</h2>
        <ul>
          <li>
            <strong>순위는 holdout으로만</strong> — 공개셋(연습용) 점수는 별도
            표기. 두 값의 격차로 과적합을 가시화.
          </li>
          <li>
            <strong>버전핀 동결·append-only</strong> — 제출은 model·날짜·scaffold·mode
            동결. 재제출은 새 행(덮어쓰기 금지) → 재시도 best-pick 차단.
          </li>
          <li>
            <strong>철회 불가</strong> — 게시 결과는 내릴 수 없고 supersede 행으로만
            정정. 손실 표본 은폐 차단.
          </li>
          <li>
            <strong>재현 검증 등재</strong> — 버전핀으로 재실행 재현된 결과만 등재
            (self-report 금지, judge=비self).
          </li>
          <li>
            <strong>holdout 문항 비공개</strong> — 본문·정답·문항 id 미노출(집계값만).
            채점셋 해자 보호.
          </li>
        </ul>
      </section>

      <footer>
        K-TaxBench · 생성 소스: {(data.meta.source_files || []).join(", ")} ·
        judge·prompt·법령 기준일은 각 행 배지 참조
      </footer>
    </div>
  );
}
