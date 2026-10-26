#!/usr/bin/env python3
"""Collect licensed resume template sources into data/templates.

The collector is intentionally fail-closed:
* GitHub sources must expose an allow-listed SPDX license.
* Public web sources require an enabled config entry, --allow-web, and robots.txt.
* Unknown sources, missing robots.txt, login/CAPTCHA pages, and rate-limit responses
  are skipped rather than retried aggressively.
* Images are never downloaded. A preview URL is recorded only when the source
  explicitly allows a public link; an administrator still reviews it before use.

This script stores source HTML/CSS/schema for review/import. It never executes the
downloaded HTML and the API must serve it only from a sandboxed preview context.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import posixpath
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, urljoin, urlparse
from urllib.robotparser import RobotFileParser
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup


USER_AGENT = "ResumeWorkshopTemplateCollector/0.1 (+https://github.com/9898998hcx)"
ALLOWED_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "CC0-1.0"}
HTML_NAMES = {"index.html", "resume.html", "cv.html", "template.html"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class SkipSource(RuntimeError):
    """Raised when a source must be skipped to remain compliant."""


@dataclass
class FetchLimits:
    min_interval_seconds: float = 3.0
    timeout_seconds: float = 20.0
    max_bytes: int = 400_000


class HostRateLimiter:
    def __init__(self, minimum_interval: float) -> None:
        self.minimum_interval = minimum_interval
        self._last_request: dict[str, float] = {}

    def wait(self, url: str, minimum_interval: float | None = None) -> None:
        host = urlparse(url).netloc.lower()
        interval = max(self.minimum_interval, minimum_interval or 0)
        elapsed = time.monotonic() - self._last_request.get(host, 0.0)
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request[host] = time.monotonic()


class GitHubClient:
    def __init__(self, limits: FetchLimits, token: str | None = None) -> None:
        headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(timeout=limits.timeout_seconds, headers=headers, follow_redirects=True)
        self.limiter = HostRateLimiter(limits.min_interval_seconds)
        self.limits = limits

    def close(self) -> None:
        self.client.close()

    def _get_json(self, url: str) -> dict[str, Any]:
        self.limiter.wait(url)
        response = self.client.get(url)
        if response.status_code in {401, 403, 429}:
            raise SkipSource(f"GitHub access/rate limit response {response.status_code}: {url}")
        if response.status_code >= 400:
            raise SkipSource(f"GitHub response {response.status_code}: {url}")
        if len(response.content) > self.limits.max_bytes * 8:
            raise SkipSource(f"GitHub JSON response too large: {url}")
        try:
            return response.json()
        except ValueError as exc:
            raise SkipSource(f"GitHub returned invalid JSON: {url}") from exc

    def repository(self, repo: str) -> dict[str, Any]:
        return self._get_json(f"https://api.github.com/repos/{repo}")

    def license(self, repo: str) -> dict[str, Any]:
        return self._get_json(f"https://api.github.com/repos/{repo}/license")

    def commit_sha(self, repo: str, branch: str) -> str:
        data = self._get_json(f"https://api.github.com/repos/{repo}/commits/{quote(branch, safe='')}")
        return str(data.get("sha", branch))

    def tree(self, repo: str, ref: str) -> list[dict[str, Any]]:
        data = self._get_json(
            f"https://api.github.com/repos/{repo}/git/trees/{quote(ref, safe='')}?recursive=1"
        )
        if data.get("truncated"):
            raise SkipSource(f"GitHub tree was truncated; narrow the source config: {repo}")
        return [item for item in data.get("tree", []) if item.get("type") == "blob"]

    def file_bytes(self, repo: str, path: str, ref: str) -> bytes:
        url = f"https://api.github.com/repos/{repo}/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}"
        data = self._get_json(url)
        if data.get("type") != "file" or not data.get("content"):
            raise SkipSource(f"GitHub path is not a readable file: {repo}:{path}")
        try:
            content = base64.b64decode(str(data["content"]).replace("\n", ""), validate=False)
        except (ValueError, TypeError) as exc:
            raise SkipSource(f"GitHub file is not valid base64: {repo}:{path}") from exc
        if len(content) > self.limits.max_bytes:
            raise SkipSource(f"File exceeds max_bytes: {repo}:{path}")
        return content


class PublicWebFetcher:
    def __init__(self, limits: FetchLimits) -> None:
        self.client = httpx.Client(
            timeout=limits.timeout_seconds,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/css;q=0.9,*/*;q=0.1"},
            follow_redirects=True,
        )
        self.limits = limits
        self.limiter = HostRateLimiter(limits.min_interval_seconds)
        self._robots: dict[str, tuple[RobotFileParser, float]] = {}

    def close(self) -> None:
        self.client.close()

    def _load_robots(self, url: str) -> tuple[RobotFileParser, float]:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin in self._robots:
            return self._robots[origin]
        robots_url = f"{origin}/robots.txt"
        self.limiter.wait(robots_url)
        try:
            response = self.client.get(robots_url)
        except httpx.HTTPError as exc:
            raise SkipSource(f"robots.txt unavailable: {robots_url}") from exc
        if response.status_code != 200 or not response.text.strip():
            raise SkipSource(f"robots.txt missing or unavailable: {robots_url}")
        parser = RobotFileParser(robots_url)
        parser.parse(response.text.splitlines())
        crawl_delay = parser.crawl_delay(USER_AGENT) or parser.crawl_delay("*") or 0.0
        self._robots[origin] = (parser, float(crawl_delay))
        return parser, float(crawl_delay)

    def get(self, url: str) -> tuple[bytes, str]:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise SkipSource(f"unsupported web URL: {url}")
        parser, crawl_delay = self._load_robots(url)
        if not parser.can_fetch(USER_AGENT, url):
            raise SkipSource(f"robots.txt disallows URL: {url}")
        self.limiter.wait(url, crawl_delay)
        try:
            with self.client.stream("GET", url) as response:
                if response.status_code in {401, 403, 429}:
                    raise SkipSource(f"web access/rate limit response {response.status_code}: {url}")
                if response.status_code >= 400:
                    raise SkipSource(f"web response {response.status_code}: {url}")
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > self.limits.max_bytes:
                    raise SkipSource(f"web response too large: {url}")
                chunks: list[bytes] = []
                total = 0
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > self.limits.max_bytes:
                        raise SkipSource(f"web response exceeds max_bytes: {url}")
                    chunks.append(chunk)
                return b"".join(chunks), response.headers.get("content-type", "")
        except httpx.HTTPError as exc:
            raise SkipSource(f"web request failed: {url}") from exc


def decode_text(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def sanitize_css(css: str) -> str:
    css = re.sub(r"@import\s+[^;]+;", "", css, flags=re.IGNORECASE)
    css = re.sub(r"url\s*\([^)]*\)", "none", css, flags=re.IGNORECASE)
    css = re.sub(r"expression\s*\(", "", css, flags=re.IGNORECASE)
    return css.strip()


def sanitize_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    inline_css: list[str] = []
    for tag in soup.find_all("style"):
        inline_css.append(tag.get_text("\n"))
        tag.decompose()
    for tag in soup.find_all("link"):
        rel = {item.lower() for item in tag.get("rel", [])}
        if "stylesheet" in rel:
            tag.decompose()
    # Images and media are deliberately removed from the stored HTML.  The
    # catalog keeps an optional public preview URL separately, but importing
    # third-party assets into a template would make later rendering fetch
    # content that we did not collect or license.
    for tag in soup.find_all(["script", "iframe", "object", "embed", "form", "video", "audio", "img", "picture"]):
        tag.decompose()
    for tag in soup.find_all(True):
        for attribute in list(tag.attrs):
            lower_attribute = attribute.lower()
            value = tag.attrs[attribute]
            if lower_attribute.startswith("on"):
                del tag.attrs[attribute]
            elif lower_attribute == "style" and isinstance(value, str):
                tag.attrs[attribute] = sanitize_css(value)
            elif lower_attribute in {"src", "href", "action"} and isinstance(value, str):
                if value.strip().lower().startswith(("javascript:", "data:")):
                    del tag.attrs[attribute]
    return str(soup), sanitize_css("\n".join(inline_css))


def sanitize_schema(content: bytes) -> str:
    try:
        value = json.loads(decode_text(content))
    except json.JSONDecodeError as exc:
        raise SkipSource("JSON Schema is not valid JSON") from exc
    return json.dumps(value, ensure_ascii=False, indent=2)


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\-\s]+", "", value, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_]+", "-", value)[:140] or f"template-{uuid4().hex[:8]}"


def infer_category(value: str) -> str:
    lowered = value.lower()
    groups = [
        ("minimal", ("minimal", "clean", "simple", "ats")),
        ("creative", ("creative", "designer", "portfolio", "colorful", "gradient")),
        ("academic", ("academic", "research", "cv")),
        ("technical", ("developer", "tech", "mono", "engineering")),
        ("executive", ("executive", "senior", "corporate", "professional")),
        ("compact", ("compact", "dense", "one-page")),
    ]
    for category, keywords in groups:
        if any(keyword in lowered for keyword in keywords):
            return category
    return "professional"


def parse_name(html: str, fallback: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    heading = soup.find(["h1", "h2"])
    value = title or (heading.get_text(" ", strip=True) if heading else "") or fallback
    return re.sub(r"\s+", " ", value).strip()[:160]


def first_preview_path(paths: Iterable[str]) -> str | None:
    candidates = [path for path in paths if Path(path).suffix.lower() in IMAGE_SUFFIXES]
    candidates.sort(key=lambda path: (0 if any(word in path.lower() for word in ("preview", "thumbnail", "screenshot")) else 1, path))
    return candidates[0] if candidates else None


def public_record(
    *,
    name: str,
    category: str,
    description: str,
    template_type: str,
    html_content: str | None,
    css_content: str | None,
    schema_json: str | None,
    preview_image: str | None,
    source_url: str,
    source_path: str,
    source_type: str,
    source_commit: str | None,
    license_name: str,
    license_url: str,
    license_text: str | None,
) -> dict[str, Any]:
    content_for_hash = "\n".join(item or "" for item in (html_content, css_content, schema_json))
    return {
        "id": str(uuid4()),
        "name": name,
        "slug": slugify(f"{name}-{source_path}"),
        "category": category,
        "description": description,
        "template_type": template_type,
        "html_content": html_content,
        "css_content": css_content,
        "schema_json": schema_json,
        "preview_image": preview_image,
        "source_url": source_url,
        "source_path": source_path,
        "source_type": source_type,
        "source_commit": source_commit,
        "license": license_name,
        "license_url": license_url,
        "license_text": license_text,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "content_sha256": hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest(),
        "review_status": "PENDING",
        "is_active": False,
    }


def collect_github_source(source: dict[str, Any], github: GitHubClient) -> list[dict[str, Any]]:
    repo = str(source["repo"])
    branch = str(source.get("branch") or "main")
    allowlist = set(source.get("license_allowlist", [])) & ALLOWED_LICENSES
    if not allowlist:
        raise SkipSource(f"empty license allowlist: {repo}")
    metadata = github.repository(repo)
    detected_license = ((metadata.get("license") or {}).get("spdx_id") or "").strip()
    if detected_license not in allowlist:
        raise SkipSource(f"license {detected_license or 'unknown'} is not allow-listed: {repo}")
    license_data = github.license(repo)
    license_url = str(license_data.get("html_url") or metadata.get("html_url") or "")
    license_text = None
    license_file = str(license_data.get("path") or "")
    if license_file:
        try:
            license_text = decode_text(github.file_bytes(repo, license_file, branch))
        except SkipSource:
            license_text = None
    commit = github.commit_sha(repo, branch)
    tree = github.tree(repo, branch)
    paths = [str(item["path"]) for item in tree]
    kind = str(source.get("kind", "html_css"))
    max_templates = int(source.get("max_templates", 50))
    records: list[dict[str, Any]] = []

    if kind == "json_schema":
        candidates = list(source.get("paths", [])) or [path for path in paths if path.endswith(".schema.json") or path.endswith("schema.json")]
        for path in candidates[:max_templates]:
            if path not in paths:
                continue
            content = sanitize_schema(github.file_bytes(repo, path, branch))
            name = source.get("name") or f"{repo.split('/', 1)[-1]} · {Path(path).stem}"
            records.append(
                public_record(
                    name=str(name),
                    category="schema",
                    description="JSON Resume 数据结构规范，供模板适配和校验使用。",
                    template_type="json_schema",
                    html_content=None,
                    css_content=None,
                    schema_json=content,
                    preview_image=None,
                    source_url=f"https://github.com/{repo}/blob/{commit}/{path}",
                    source_path=path,
                    source_type="github",
                    source_commit=commit,
                    license_name=detected_license,
                    license_url=license_url,
                    license_text=license_text,
                )
            )
        return records

    if kind != "html_css":
        raise SkipSource(f"unsupported source kind {kind}: {repo}")

    html_paths = [
        path for path in paths
        if Path(path).suffix.lower() == ".html"
        and Path(path).name.lower() in HTML_NAMES
        and not any(part.lower() in {"node_modules", "dist", "build"} for part in Path(path).parts)
    ]
    for html_path in html_paths:
        if len(records) >= max_templates:
            break
        directory = posixpath.dirname(html_path)
        css_paths = [
            path for path in paths
            if posixpath.dirname(path) == directory and Path(path).suffix.lower() in {".css", ".less"}
        ]
        if not css_paths:
            continue
        html_raw = decode_text(github.file_bytes(repo, html_path, branch))
        html_content, inline_css = sanitize_html(html_raw)
        css_parts = [inline_css]
        for css_path in sorted(css_paths)[:4]:
            css_parts.append(sanitize_css(decode_text(github.file_bytes(repo, css_path, branch))))
        css_content = "\n\n".join(part for part in css_parts if part).strip()
        fallback = Path(directory).name.replace("-", " ").replace("_", " ").title() or repo.split("/", 1)[-1]
        name = parse_name(html_raw, fallback)
        preview_path = first_preview_path(
            path for path in paths if posixpath.dirname(path) == directory
        )
        preview_url = None
        if preview_path and bool(source.get("allow_preview_links", False)):
            preview_url = f"https://raw.githubusercontent.com/{repo}/{commit}/{quote(preview_path, safe='/')}"
        records.append(
            public_record(
                name=name,
                category=infer_category(f"{name} {html_path}"),
                description=f"来自 {repo} 的开源 HTML/CSS 模板，需审核后展示。",
                template_type="html_css",
                html_content=html_content,
                css_content=css_content,
                schema_json=None,
                preview_image=preview_url,
                source_url=f"https://github.com/{repo}/blob/{commit}/{html_path}",
                source_path=html_path,
                source_type="github",
                source_commit=commit,
                license_name=detected_license,
                license_url=license_url,
                license_text=license_text,
            )
        )
    return records


def collect_web_source(source: dict[str, Any], fetcher: PublicWebFetcher) -> list[dict[str, Any]]:
    url = str(source["url"])
    content, content_type = fetcher.get(url)
    if "html" not in content_type and not url.lower().endswith(("/", ".html", ".htm")):
        raise SkipSource(f"web source is not HTML: {url}")
    raw_html = decode_text(content)
    html_content, inline_css = sanitize_html(raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")
    css_parts = [inline_css]
    source_host = urlparse(url).netloc
    for link in soup.find_all("link"):
        if "stylesheet" not in {item.lower() for item in link.get("rel", [])}:
            continue
        href = link.get("href")
        if not href:
            continue
        css_url = urljoin(url, href)
        if urlparse(css_url).netloc != source_host:
            continue
        css_bytes, _ = fetcher.get(css_url)
        css_parts.append(sanitize_css(decode_text(css_bytes)))
    preview_image = None
    if source.get("allow_preview_links"):
        og = soup.find("meta", attrs={"property": "og:image"})
        if og and og.get("content"):
            preview_image = urljoin(url, str(og["content"]))
    name = parse_name(raw_html, str(source.get("name") or urlparse(url).netloc))
    return [
        public_record(
            name=name,
            category=infer_category(name),
            description="来自已配置公开网页的模板，需管理员审核后展示。",
            template_type="html_css",
            html_content=html_content,
            css_content="\n\n".join(part for part in css_parts if part).strip(),
            schema_json=None,
            preview_image=preview_image,
            source_url=url,
            source_path=urlparse(url).path or "/",
            source_type="web",
            source_commit=None,
            license_name=str(source["license"]),
            license_url=str(source["license_url"]),
            license_text=None,
        )
    ]


def write_records(records: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        folder = output_dir / record["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        if record.get("html_content"):
            (folder / "index.html").write_text(record["html_content"], encoding="utf-8")
        if record.get("css_content"):
            (folder / "style.css").write_text(record["css_content"], encoding="utf-8")
        if record.get("schema_json"):
            (folder / "schema.json").write_text(record["schema_json"], encoding="utf-8")
        if record.get("license_text"):
            (folder / "LICENSE.txt").write_text(record["license_text"], encoding="utf-8")
        (folder / "template.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    (output_dir / "templates.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect licensed resume templates safely.")
    parser.add_argument("--config", type=Path, default=Path("backend/scripts/template_sources.json"))
    parser.add_argument("--output", type=Path, default=Path("data/templates"))
    parser.add_argument("--max-templates", type=int, default=50)
    parser.add_argument("--min-interval", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=400_000)
    parser.add_argument("--allow-web", action="store_true", help="Enable explicitly configured public web sources.")
    parser.add_argument("--dry-run", action="store_true", help="Collect and report without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    limits = FetchLimits(args.min_interval, args.timeout, args.max_bytes)
    github = GitHubClient(limits, os.getenv("GITHUB_TOKEN"))
    web = PublicWebFetcher(limits)
    records: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, str]] = set()
    seen_hashes: set[str] = set()
    try:
        for source in config.get("github", []):
            if not source.get("enabled", False):
                print(f"SKIP disabled github source: {source.get('repo')}")
                continue
            try:
                found = collect_github_source(source, github)
            except SkipSource as exc:
                print(f"SKIP github {source.get('repo')}: {exc}")
                continue
            for record in found:
                key = (record["source_url"], record["source_path"])
                if key in seen_sources or record["content_sha256"] in seen_hashes:
                    continue
                seen_sources.add(key)
                seen_hashes.add(record["content_sha256"])
                records.append(record)
                if len(records) >= args.max_templates:
                    break
            if len(records) >= args.max_templates:
                break

        if args.allow_web and len(records) < args.max_templates:
            for source in config.get("web", []):
                if not source.get("enabled", False):
                    print(f"SKIP disabled web source: {source.get('url')}")
                    continue
                try:
                    found = collect_web_source(source, web)
                except SkipSource as exc:
                    print(f"SKIP web {source.get('url')}: {exc}")
                    continue
                for record in found:
                    key = (record["source_url"], record["source_path"])
                    if key in seen_sources or record["content_sha256"] in seen_hashes:
                        continue
                    seen_sources.add(key)
                    seen_hashes.add(record["content_sha256"])
                    records.append(record)
                    if len(records) >= args.max_templates:
                        break
                if len(records) >= args.max_templates:
                    break
        elif not args.allow_web:
            print("SKIP all web sources: pass --allow-web after reviewing ToS and robots.txt.")
    finally:
        github.close()
        web.close()

    if not args.dry_run:
        write_records(records, args.output)
        print(f"WROTE {len(records)} templates to {args.output}")
    else:
        print(f"DRY-RUN collected {len(records)} templates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
