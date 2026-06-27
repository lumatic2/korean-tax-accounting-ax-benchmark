"use client";

import * as React from "react";
import {
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Trophy,
  Database,
  LockKeyhole,
  CalendarClock,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// 점수(0~100) → 히트맵 색 (빨강→노랑→초록). 극단일수록 진하게.
function heat(score) {
  if (score == null) return "#f1f3f7";
  const h = Math.max(0, Math.min(120, (score / 100) * 120));
  const dist = Math.abs(score - 50) / 50;
  const light = 86 - dist * 16;
  return `hsl(${h} 74% ${light}%)`;
}

const fmt = (v) => (v == null ? "–" : v.toFixed(1));

function scoreTone(score) {
  if (score == null) return "bg-muted";
  if (score >= 90) return "bg-[#1a7a44]";
  if (score >= 75) return "bg-[#1d6fe0]";
  if (score >= 55) return "bg-[#b15c00]";
  return "bg-[#b3261e]";
}

function ScoreCell({ score, n, modes, peer, compareLabel }) {
  const delta = score != null && peer != null ? score - peer : null;
  return (
    <div className="min-w-[132px]">
      <div className="flex items-baseline justify-end gap-2">
        <strong className="tabular-nums text-[18px] leading-none text-primary">
          {fmt(score)}
        </strong>
        <span className="text-[11px] text-muted-foreground">n={n}</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", scoreTone(score))}
          style={{ width: `${Math.max(0, Math.min(100, score ?? 0))}%` }}
        />
      </div>
      {delta != null && (
        <div
          className={cn(
            "mt-1 text-right text-[11px] tabular-nums",
            Math.abs(delta) < 1
              ? "text-muted-foreground"
              : delta > 0
                ? "text-ok"
                : "text-warn"
          )}
        >
          {delta > 0 ? "+" : ""}
          {fmt(delta)} vs {compareLabel}
        </div>
      )}
      <div className="mt-2 flex flex-wrap justify-end gap-1">
        {Object.entries(modes || {})
          .sort()
          .map(([mode, avg]) => (
            <Badge key={mode} variant="pin">
              {mode} {fmt(avg)}
            </Badge>
          ))}
      </div>
    </div>
  );
}

function RankMark({ rank }) {
  const top = rank === 1;
  return (
    <div
      className={cn(
        "inline-flex h-7 min-w-7 items-center justify-center rounded-full px-2 text-[12px] font-bold tabular-nums",
        top ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
      )}
    >
      {rank}
    </div>
  );
}

function GradeStrip({ grades }) {
  const ordered = ["A", "B", "C", "D"];
  const total = ordered.reduce((acc, g) => acc + (grades?.[g] || 0), 0);
  return (
    <div className="min-w-[150px]">
      <div className="flex h-2 overflow-hidden rounded-full bg-muted">
        {ordered.map((g) => {
          const n = grades?.[g] || 0;
          const width = total ? (n / total) * 100 : 0;
          const color =
            g === "A"
              ? "bg-[#1a7a44]"
              : g === "B"
                ? "bg-[#1d6fe0]"
                : g === "C"
                  ? "bg-[#b15c00]"
                  : "bg-[#b3261e]";
          return <div key={g} className={color} style={{ width: `${width}%` }} />;
        })}
      </div>
      <div className="mt-1.5 font-mono text-[11px] text-secondary-foreground">
        {ordered.map((g) => `${g}:${grades?.[g] || 0}`).join("  ")}
      </div>
    </div>
  );
}

function SortHeader({ label, active, dir, onClick, className }) {
  const Icon = !active ? ArrowUpDown : dir === "asc" ? ArrowUp : ArrowDown;
  return (
    <button
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1 font-semibold select-none hover:text-primary transition-colors",
        active ? "text-primary" : "text-secondary-foreground",
        className
      )}
    >
      {label}
      <Icon className="h-3.5 w-3.5 opacity-70" />
    </button>
  );
}

export default function LeaderboardView({
  views,
}) {
  const [activeView, setActiveView] = React.useState(views[0]?.key);
  const [query, setQuery] = React.useState("");
  const [sortKey, setSortKey] = React.useState("holdout");
  const [sortDir, setSortDir] = React.useState("desc");
  const [hiddenDomains, setHiddenDomains] = React.useState(() => new Set());

  const view = views.find((v) => v.key === activeView) || views[0];
  const {
    rows,
    allDims,
    allDomains,
    disc,
    meta,
    errorsPublic,
    errorsHoldoutAgg,
  } = view;
  const flagOk = disc.flag === "ok";

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "model" ? "asc" : "desc");
    }
  }

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    const base = q
      ? rows.filter((r) => r.model.toLowerCase().includes(q))
      : rows.slice();
    base.sort((a, b) => {
      let av;
      let bv;
      if (sortKey === "model") {
        av = a.model;
        bv = b.model;
        return sortDir === "asc"
          ? av.localeCompare(bv)
          : bv.localeCompare(av);
      }
      av = a[sortKey] ?? -1;
      bv = b[sortKey] ?? -1;
      return sortDir === "asc" ? av - bv : bv - av;
    });
    return base;
  }, [rows, query, sortKey, sortDir]);

  const shownDomains = allDomains.filter((d) => !hiddenDomains.has(d));
  const leader = rows.find((r) => r.rank === 1) || rows[0];
  const latest = rows
    .slice()
    .sort((a, b) => {
      const ad = (a.pin.accessed_at || []).slice().sort().at(-1) || "";
      const bd = (b.pin.accessed_at || []).slice().sort().at(-1) || "";
      return bd.localeCompare(ad);
    })[0];

  function toggleDomain(d) {
    setHiddenDomains((prev) => {
      const next = new Set(prev);
      if (next.has(d)) next.delete(d);
      else next.add(d);
      return next;
    });
  }

  const stats = [
    { lab: "Holdout Leader", val: leader?.model || "–", sub: `${fmt(leader?.holdout)} avg`, icon: Trophy },
    { lab: "Latest Run", val: latest?.model || "–", sub: (latest?.pin.accessed_at || []).slice().sort().at(-1) || "–", icon: CalendarClock },
    { lab: "Spread", val: disc.spread, sub: `${disc.range[0]}–${disc.range[1]}`, icon: Database },
    {
      lab: "flag",
      val: disc.flag,
      sub: "discrimination",
      tone: flagOk ? "ok" : "warn",
      icon: flagOk ? CheckCircle2 : AlertTriangle,
    },
  ];

  return (
    <div className="mx-auto max-w-[1320px] px-6 pb-20 pt-8">
      {/* 헤더 */}
      <header className="mb-5 flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant="pin">read-only leaderboard</Badge>
            <Badge variant="ok">
              <LockKeyhole className="h-3 w-3" /> {view.rankBadge}
            </Badge>
            <Badge variant="pin">{view.badge}</Badge>
          </div>
          <h1 className="m-0 text-[30px] font-bold tracking-tight text-primary">
            {view.title}
          </h1>
          <p className="mt-1.5 max-w-3xl text-sm text-muted-foreground">
            {view.description} 동일 행 안에서 dataset, mode, judge, 측정일을 함께 고정합니다.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-right sm:grid-cols-3">
          <div>
            <div className="text-[11px] uppercase text-muted-foreground">Models</div>
            <div className="text-[20px] font-bold text-primary">{rows.length}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted-foreground">Holdout</div>
            <div className="text-[20px] font-bold text-primary">{meta.n_holdout_records}</div>
          </div>
          <div>
            <div className="text-[11px] uppercase text-muted-foreground">Public</div>
            <div className="text-[20px] font-bold text-primary">{meta.n_public_records}</div>
          </div>
        </div>
      </header>

      <div className="mb-5 flex flex-wrap gap-2">
        {views.map((v) => (
          <Button
            key={v.key}
            variant={v.key === activeView ? "default" : "outline"}
            onClick={() => {
              setActiveView(v.key);
              setSortKey("holdout");
              setSortDir("desc");
            }}
          >
            {v.label}
          </Button>
        ))}
      </div>

      {/* 통계 배너 */}
      <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div
              key={s.lab}
              className="rounded-lg border border-border bg-card p-4 shadow-sm"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {s.lab}
                </div>
                {Icon && <Icon className="h-4 w-4 text-accent" />}
              </div>
              <div
                className={cn(
                  "mt-2 flex items-center gap-1.5 text-[24px] font-bold leading-tight text-primary",
                  s.tone === "ok" && "text-[#5ce08a]",
                  s.tone === "warn" && "text-[#ffb454]"
                )}
              >
                {s.val}
              </div>
              <div className="mt-1 text-[12px] text-muted-foreground">{s.sub}</div>
            </div>
          );
        })}
      </div>

      <div className="mb-5 rounded-lg border border-[#cfe0fb] bg-[#f2f7ff] px-4 py-3 text-[13px] text-secondary-foreground">
        <strong className="text-primary">해석 주의:</strong> {view.notice}
      </div>

      {/* 검색 툴바 */}
      <div className="mb-4 flex items-center gap-3">
        <div className="relative w-full max-w-xs">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="모델 검색…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-8"
          />
        </div>
        <span className="text-[13px] text-muted-foreground">
          {filtered.length}/{rows.length} 모델
        </span>
      </div>

      {/* 모델 랭킹 */}
      <Card className="mb-7">
        <CardHeader>
          <CardTitle>모델 랭킹</CardTitle>
          <CardDescription>
            holdout 기준 순위. 공개셋 점수와 mode breakdown은 비교 조건을
            드러내기 위한 보조 정보입니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10 text-right">#</TableHead>
                <TableHead className="min-w-[390px]">
                  <SortHeader
                    label="모델"
                    active={sortKey === "model"}
                    dir={sortDir}
                    onClick={() => toggleSort("model")}
                  />
                </TableHead>
                <TableHead className="text-right">
                  <SortHeader
                    label="holdout 평균"
                    active={sortKey === "holdout"}
                    dir={sortDir}
                    onClick={() => toggleSort("holdout")}
                    className="ml-auto"
                  />
                </TableHead>
                <TableHead className="text-right">
                  <SortHeader
                    label="공개셋 평균"
                    active={sortKey === "public"}
                    dir={sortDir}
                    onClick={() => toggleSort("public")}
                    className="ml-auto"
                  />
                </TableHead>
                <TableHead className="min-w-[180px]">등급분포 (holdout)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow
                  key={r.model}
                  className={cn(r.rank === 1 && "bg-[#f7fbff] hover:bg-[#f1f7ff]")}
                >
                  <TableCell className="text-right tabular-nums text-muted-foreground">
                    <RankMark rank={r.rank} />
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="font-semibold text-primary">{r.model}</div>
                      {r.rank === 1 && <Badge variant="ok">current leader</Badge>}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {(r.pin.prompt_version || []).map((v) => (
                        <Badge variant="pin" key={"pv" + v}>
                          scaffold {v}
                        </Badge>
                      ))}
                      {(r.pin.modes || []).map((v) => (
                        <Badge key={"md" + v}>{v}</Badge>
                      ))}
                      {(r.pin.accessed_at || []).map((v) => (
                        <Badge key={"ac" + v}>측정 {v}</Badge>
                      ))}
                      {(r.pin.judge_model || []).map((v) => (
                        <Badge key={"jm" + v}>judge {v}</Badge>
                      ))}
                      {(r.pin.measurement_label || []).map((v) => (
                        <Badge variant="pin" key={"ml" + v}>
                          {v}
                        </Badge>
                      ))}
                      <Badge variant="ok">
                        <CheckCircle2 className="h-3 w-3" /> 재현 검증
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-right align-top">
                    <ScoreCell
                      score={r.holdout}
                      n={r.holdoutN}
                      modes={r.holdoutModes}
                      peer={r.public}
                      compareLabel="공개셋"
                    />
                  </TableCell>
                  <TableCell className="text-right align-top">
                    <ScoreCell
                      score={r.public}
                      n={r.publicN}
                      modes={r.publicModes}
                      peer={r.holdout}
                      compareLabel="holdout"
                    />
                  </TableCell>
                  <TableCell>
                    <GradeStrip grades={r.grades} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 차원별 히트맵 */}
      <Card className="mb-7">
        <CardHeader>
          <CardTitle>차원별 평균 (holdout)</CardTitle>
          <CardDescription>
            7차원 루브릭 — 어느 축이 약한지(환각·계산·근거).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>모델</TableHead>
                {allDims.map((d) => (
                  <TableHead className="text-center" key={d}>
                    {d}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow key={r.model}>
                  <TableCell className="font-semibold">{r.model}</TableCell>
                  {allDims.map((d) => (
                    <TableCell
                      key={d}
                      className="text-center font-semibold tabular-nums text-primary"
                      style={{ background: heat(r.dims[d]) }}
                    >
                      {fmt(r.dims[d])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 분야별 히트맵 + 도메인 토글 */}
      <Card className="mb-7">
        <CardHeader>
          <CardTitle>분야별 평균 (holdout)</CardTitle>
          <CardDescription>도메인 칩을 눌러 컬럼을 켜고 끌 수 있음.</CardDescription>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {allDomains.map((d) => {
              const on = !hiddenDomains.has(d);
              return (
                <Button
                  key={d}
                  variant={on ? "default" : "outline"}
                  size="chip"
                  onClick={() => toggleDomain(d)}
                >
                  {d}
                </Button>
              );
            })}
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>모델</TableHead>
                {shownDomains.map((d) => (
                  <TableHead className="text-center" key={d}>
                    {d}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow key={r.model}>
                  <TableCell className="font-semibold">{r.model}</TableCell>
                  {shownDomains.map((d) => (
                    <TableCell
                      key={d}
                      className="text-center font-semibold tabular-nums text-primary"
                      style={{ background: heat(r.domains[d]) }}
                    >
                      {fmt(r.domains[d])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 대표 오류 사례 */}
      <Card className="mb-7">
        <CardHeader>
          <CardTitle>대표 오류 사례</CardTitle>
          <CardDescription>
            공개셋은 문항 id 노출, holdout은 type별 카운트만(문항 비공개 — 해자
            보호).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="mb-1.5 text-[13px] font-semibold text-secondary-foreground">
              공개셋 (id 표시)
            </h3>
            <ul className="m-0 list-none p-0">
              {errorsPublic.slice(0, 12).map((e, i) => (
                <li
                  key={i}
                  className="flex flex-wrap items-center gap-x-2 gap-y-1 border-b border-border py-2 text-[13.5px] last:border-0"
                >
                  <Badge variant="error">{e.type}</Badge>
                  <strong>{e.id}</strong>
                  <span className="text-muted-foreground">
                    · {e.model}/{e.mode} — {e.detail}
                  </span>
                </li>
              ))}
              {errorsPublic.length === 0 && (
                <li className="py-2 text-[13.5px] text-muted-foreground">
                  공개셋 오류 없음
                </li>
              )}
            </ul>
          </div>
          <div>
            <h3 className="mb-1.5 text-[13px] font-semibold text-secondary-foreground">
              holdout (집계 카운트)
            </h3>
            <ul className="m-0 flex flex-wrap gap-2 p-0">
              {Object.entries(errorsHoldoutAgg.by_type || {}).map(([t, n]) => (
                <li key={t}>
                  <Badge variant="error">
                    {t} {n}건
                  </Badge>
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* 정책 */}
      <Card className="mb-7">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-accent" />
            제출·운영 정책 (ADR 0009)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="m-0 list-disc space-y-1.5 pl-5 text-[13.5px]">
            <li>
              <strong>순위는 holdout으로만</strong> — 공개셋(연습용) 점수는 별도
              표기. 두 값의 격차로 과적합을 가시화.
            </li>
            <li>
              <strong>버전핀 동결·append-only</strong> — 제출은
              model·날짜·scaffold·mode 동결. 재제출은 새 행(덮어쓰기 금지) →
              재시도 best-pick 차단.
            </li>
            <li>
              <strong>철회 불가</strong> — 게시 결과는 내릴 수 없고 supersede
              행으로만 정정. 손실 표본 은폐 차단.
            </li>
            <li>
              <strong>재현 검증 등재</strong> — 버전핀으로 재실행 재현된 결과만
              등재 (self-report 금지, judge=비self).
            </li>
            <li>
              <strong>holdout 문항 비공개</strong> —
              본문·정답·문항 id 미노출(집계값만). 채점셋 해자 보호.
            </li>
          </ul>
        </CardContent>
      </Card>

      <footer className="mt-10 text-center text-xs text-muted-foreground">
        K-TaxBench · 생성 소스: {(meta.source_files || []).join(", ")} ·
        judge·prompt·법령 기준일은 각 행 배지 참조
      </footer>
    </div>
  );
}
