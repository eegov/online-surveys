#!/usr/bin/env python3
"""Сбор метрик качества из отчётов инструментов, истории git и GitHub API.

Скрипт берёт только то, что уже есть на диске: отчёты Checkstyle, ESLint, JaCoCo,
Vitest и JUnit-XML. Чего нет, того нет в таблице, поэтому один и тот же скрипт
работает и в отдельных jobs CI (там часть отчётов), и в workflow релиза (там все).

Примеры:
    python3 scripts/collect_metrics.py --summary
    python3 scripts/collect_metrics.py --git --github --tag v0.1.0 --json metrics.json --md metrics.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "server"
CLIENT = ROOT / "client"


def pct(covered: int, total: int) -> float | None:
    return round(100.0 * covered / total, 1) if total else None


# ---------- Статический анализ ----------

def checkstyle() -> dict | None:
    path = SERVER / "target" / "checkstyle-result.xml"
    if not path.exists():
        return None
    errors = warnings = 0
    for err in ET.parse(path).getroot().iter("error"):
        if err.get("severity") == "error":
            errors += 1
        else:
            warnings += 1
    return {"errors": errors, "warnings": warnings}


def eslint() -> dict | None:
    path = CLIENT / "reports" / "eslint.json"
    if not path.exists():
        return None
    files = json.loads(path.read_text(encoding="utf-8"))
    return {
        "errors": sum(f["errorCount"] for f in files),
        "warnings": sum(f["warningCount"] for f in files),
    }


# ---------- Покрытие и сложность ----------

def _counters(element) -> dict:
    return {
        c.get("type"): (int(c.get("missed")), int(c.get("covered")))
        for c in element.findall("counter")
    }


def jacoco() -> dict | None:
    path = SERVER / "target" / "site" / "jacoco" / "jacoco.xml"
    if not path.exists():
        return None
    root = ET.parse(path).getroot()
    total = _counters(root)
    line_m, line_c = total.get("LINE", (0, 0))
    br_m, br_c = total.get("BRANCH", (0, 0))
    cx_m, cx_c = total.get("COMPLEXITY", (0, 0))
    met_m, met_c = total.get("METHOD", (0, 0))
    per_method = [sum(_counters(m).get("COMPLEXITY", (0, 0))) for m in root.iter("method")]
    methods = met_m + met_c
    return {
        "line_coverage": pct(line_c, line_m + line_c),
        "branch_coverage": pct(br_c, br_m + br_c),
        "complexity_total": cx_m + cx_c,
        "complexity_avg_per_method": round((cx_m + cx_c) / methods, 2) if methods else None,
        "complexity_max_method": max(per_method, default=None),
    }


def vitest_coverage() -> dict | None:
    path = CLIENT / "coverage" / "coverage-summary.json"
    if not path.exists():
        return None
    total = json.loads(path.read_text(encoding="utf-8"))["total"]
    return {"line_coverage": total["lines"]["pct"], "branch_coverage": total["branches"]["pct"]}


# ---------- Тесты ----------

def junit(patterns: list[str]) -> dict | None:
    files = [f for p in patterns for f in glob.glob(str(ROOT / p))]
    if not files:
        return None
    result = {"tests": 0, "failed": 0, "skipped": 0, "time_s": 0.0}
    for f in files:
        root = ET.parse(f).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        for s in suites:
            result["tests"] += int(s.get("tests", 0))
            result["failed"] += int(s.get("failures", 0)) + int(s.get("errors", 0))
            result["skipped"] += int(s.get("skipped", 0))
            result["time_s"] += float(s.get("time", 0) or 0)
    result["passed"] = result["tests"] - result["failed"] - result["skipped"]
    result["time_s"] = round(result["time_s"], 2)
    return result


# ---------- Объём кода ----------

def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def lines_of_code() -> dict | None:
    try:
        files = _git("ls-files", "server/src", "client/src").split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    code = tests = 0
    for f in files:
        if not f.endswith((".java", ".ts", ".tsx")):
            continue
        n = sum(1 for line in (ROOT / f).read_text(encoding="utf-8").splitlines() if line.strip())
        is_test = "/src/test/" in f or ".test." in f
        tests += n if is_test else 0
        code += 0 if is_test else n
    return {"code": code, "tests": tests}


# ---------- Git-метрики ----------

def previous_tag(tag: str | None) -> str | None:
    # versionsort.suffix: v0.1.0-alpha.1 считается раньше v0.1.0, как в SemVer.
    tags = _git("-c", "versionsort.suffix=-", "tag", "--list", "v*", "--sort=-v:refname").split()
    if tag in tags:
        later = tags[tags.index(tag) + 1:]
        return later[0] if later else None
    return tags[0] if tags else None


# Файлы, которые пишет инструмент, а не человек: в размер коммита не входят,
# иначе один package-lock.json даёт тысячи строк и метрика перестаёт что-то значить.
GENERATED = ("package-lock.json", "mvnw", "mvnw.cmd", "maven-wrapper.properties")


def _is_generated(path: str) -> bool:
    return path.rsplit("/", 1)[-1] in GENERATED


def git_metrics(tag: str | None) -> dict:
    prev = previous_tag(tag)
    rng = f"{prev}..HEAD" if prev else "HEAD"
    log = _git("log", rng, "--no-merges", "--numstat", "--format=@%H %ct")
    commits: list[tuple[int, int]] = []  # (timestamp, changed lines)
    for line in log.splitlines():
        if line.startswith("@"):
            commits.append((int(line.split()[1]), 0))
        elif line.strip() and commits:
            added, deleted, path = line.split("\t", 2)
            if added != "-" and not _is_generated(path):
                ts, size = commits[-1]
                commits[-1] = (ts, size + int(added) + int(deleted))
    if not commits:
        return {"range": rng, "commits": 0}
    times = [c[0] for c in commits]
    weeks = max((max(times) - min(times)) / (7 * 24 * 3600), 1.0)
    sizes = sorted(c[1] for c in commits)
    return {
        "range": rng,
        "commits": len(commits),
        "commits_per_week": round(len(commits) / weeks, 1),
        "commit_size_avg": round(sum(sizes) / len(sizes), 1),
        "commit_size_median": sizes[len(sizes) // 2],
    }


# ---------- GitHub API: CI и pull requests ----------

def _api(path: str) -> dict | list:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}{path}",
        headers={
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _ts(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def github_metrics() -> dict | None:
    if not (os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY")):
        return None
    runs = _api("/actions/workflows/ci.yml/runs?status=completed&per_page=100")["workflow_runs"]
    finished = [r for r in runs if r["conclusion"] in ("success", "failure")]
    ok = [r for r in finished if r["conclusion"] == "success"]
    durations = [(_ts(r["updated_at"]) - _ts(r["run_started_at"])).total_seconds() for r in ok]
    prs = _api("/pulls?state=all&per_page=100")
    merged = [p for p in prs if p.get("merged_at")]
    lifetimes = [(_ts(p["merged_at"]) - _ts(p["created_at"])).total_seconds() / 3600 for p in merged]
    return {
        "ci_runs": len(finished),
        "ci_success_rate": pct(len(ok), len(finished)),
        "ci_duration_avg_s": round(sum(durations) / len(durations)) if durations else None,
        "prs_open": sum(1 for p in prs if p["state"] == "open"),
        "prs_closed": sum(1 for p in prs if p["state"] == "closed"),
        "prs_merged": len(merged),
        "branch_lifetime_avg_h": round(sum(lifetimes) / len(lifetimes), 2) if lifetimes else None,
    }


# ---------- Сборка и вывод ----------

def collect(with_git: bool, with_github: bool, tag: str | None) -> dict:
    metrics = {
        "tag": tag,
        "commit": os.environ.get("GITHUB_SHA"),
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "checkstyle": checkstyle(),
        "eslint": eslint(),
        "server_coverage": jacoco(),
        "client_coverage": vitest_coverage(),
        "server_unit_tests": junit(["server/target/surefire-reports/TEST-*.xml"]),
        "server_integration_tests": junit(["server/target/failsafe-reports/TEST-*.xml"]),
        "client_tests": junit(["client/reports/junit.xml"]),
        "lines_of_code": lines_of_code(),
    }
    if with_git:
        metrics["git"] = git_metrics(tag)
    if with_github:
        metrics["github"] = github_metrics()
    return metrics


def markdown(m: dict) -> str:
    rows: list[tuple[str, object, str]] = []

    def add(name: str, value: object, source: str) -> None:
        if value is not None:
            rows.append((name, value, source))

    if m.get("checkstyle"):
        c = m["checkstyle"]
        add("Ошибки / предупреждения линтера (сервер)", f"{c['errors']} / {c['warnings']}", "Checkstyle")
    if m.get("eslint"):
        e = m["eslint"]
        add("Ошибки / предупреждения линтера (клиент)", f"{e['errors']} / {e['warnings']}", "ESLint")
    if m.get("server_coverage"):
        s = m["server_coverage"]
        add("Покрытие строк (сервер), %", s["line_coverage"], "JaCoCo")
        add("Покрытие ветвлений (сервер), %", s["branch_coverage"], "JaCoCo")
        add("Цикломатическая сложность: средняя на метод", s["complexity_avg_per_method"], "JaCoCo")
        add("Цикломатическая сложность: максимум на метод", s["complexity_max_method"], "JaCoCo")
    if m.get("client_coverage"):
        c = m["client_coverage"]
        add("Покрытие строк (клиент), %", c["line_coverage"], "Vitest (v8)")
        add("Покрытие ветвлений (клиент), %", c["branch_coverage"], "Vitest (v8)")
    for key, label, tool in (
        ("server_unit_tests", "модульные (сервер)", "JUnit 5"),
        ("server_integration_tests", "интеграционные (сервер)", "JUnit 5 + Testcontainers"),
        ("client_tests", "клиент", "Vitest"),
    ):
        t = m.get(key)
        if t:
            add(f"Тесты {label}: прошло / упало / пропущено", f"{t['passed']} / {t['failed']} / {t['skipped']}", tool)
            add(f"Время тестов {label}, с", t["time_s"], tool)
    if m.get("lines_of_code"):
        loc = m["lines_of_code"]
        add("Строк кода: программа / тесты", f"{loc['code']} / {loc['tests']}", "git ls-files")
    g = m.get("git")
    if g and g.get("commits"):
        add(f"Коммитов ({g['range']})", g["commits"], "git log")
        add("Частота коммитов, в неделю", g["commits_per_week"], "git log")
        add("Размер коммита: среднее / медиана, строк", f"{g['commit_size_avg']} / {g['commit_size_median']}", "git log")
    gh = m.get("github")
    if gh:
        add("Доля успешных запусков CI, %", gh["ci_success_rate"], f"GitHub Actions ({gh['ci_runs']} запусков)")
        add("Среднее время пайплайна CI, с", gh["ci_duration_avg_s"], "GitHub Actions")
        add("Pull requests: открыто / закрыто (из них слито)",
            f"{gh['prs_open']} / {gh['prs_closed']} ({gh['prs_merged']})", "GitHub API")
        add("Время жизни ветки (от PR до слияния), ч", gh["branch_lifetime_avg_h"], "GitHub API")

    title = f"## Метрики качества{' ' + m['tag'] if m.get('tag') else ''}\n\n"
    if not rows:
        return title + "Отчётов для метрик не найдено.\n"
    table = "| Метрика | Значение | Источник |\n|---|---|---|\n"
    table += "".join(f"| {n} | {v} | {s} |\n" for n, v, s in rows)
    return title + table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--git", action="store_true", help="метрики процесса из git log")
    parser.add_argument("--github", action="store_true", help="метрики CI и PR из GitHub API")
    parser.add_argument("--tag", help="тег релиза, для которого снимаются метрики")
    parser.add_argument("--json", help="куда записать метрики в JSON")
    parser.add_argument("--md", help="куда записать таблицу Markdown")
    parser.add_argument("--summary", action="store_true", help="добавить таблицу в сводку job GitHub Actions")
    args = parser.parse_args()

    m = collect(args.git, args.github, args.tag)
    md = markdown(m)
    if args.json:
        Path(args.json).write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.md:
        Path(args.md).write_text(md, encoding="utf-8")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.summary and summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(md + "\n")
    if not (args.json or args.md) or not summary:
        print(md)


if __name__ == "__main__":
    main()
