#!/usr/bin/env python
"""Match logo files in logos/inbox/ to our team names and publish them for the site.

    python scripts/import_logos.py

File names are `country_team-name.ext` (or `country/team-name.ext`). A file matches
a team only by exact name or a team_names.yaml alias (ignoring case, accents,
punctuation and words like FC/AC), within that country's leagues; anything else
needs an entry in logos/names.yaml (file stem -> our team name, or `skip`). Unmatched files
are listed, never guessed.

Output: web/public/teams/<slug>.webp (128px) and web/data/team_logos.json; competition logos
(e.g. england_premier-league.svg) go to web/public/leagues/<code>.webp and web/data/league_logos.json.
Safe to re-run; only new or changed files are converted.
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import pandas as pd
import yaml

from predictor.config import load_config, project_path

COUNTRY_LEAGUES = {
    "england": ["E0", "E1"], "scotland": ["SC0"], "germany": ["D1", "D2"], "italy": ["I1", "I2"],
    "spain": ["SP1", "SP2"], "france": ["F1", "F2"], "netherlands": ["N1"], "belgium": ["B1"],
    "portugal": ["P1"], "turkey": ["T1"], "greece": ["G1"], "austria": ["AUT"], "switzerland": ["SWZ"],
    "denmark": ["DNK"], "romania": ["ROU"], "poland": ["POL"],
    "liechtenstein": ["SWZ"],  # Vaduz plays in the Swiss leagues
}
# Competition logos: file name (normalised) -> league code, per country.
LEAGUE_FILES = {
    "england": {"premierleague": "E0", "englishpremierleague": "E0", "epl": "E0",
                "championship": "E1", "eflchampionship": "E1", "skybetchampionship": "E1"},
    "germany": {"bundesliga": "D1", "2bundesliga": "D2", "bundesliga2": "D2", "zweitebundesliga": "D2"},
    "italy": {"seriea": "I1", "serieb": "I2"},
    "spain": {"laliga": "SP1", "laligaeasports": "SP1", "primeradivision": "SP1",
              "laliga2": "SP2", "laligahypermotion": "SP2", "segundadivision": "SP2", "segunda": "SP2"},
    "france": {"ligue1": "F1", "ligue2": "F2"},
    "netherlands": {"eredivisie": "N1"},
    "belgium": {"belgianproleague": "B1", "proleague": "B1", "jupilerproleague": "B1"},
    "portugal": {"primeiraliga": "P1", "ligaportugal": "P1", "ligaportugalbetclic": "P1"},
    "turkey": {"superlig": "T1", "turkishsuperlig": "T1"},
    "greece": {"superleague": "G1", "superleague1": "G1", "superleaguegreece": "G1", "greeksuperleague": "G1"},
    "scotland": {"premiership": "SC0", "scottishpremiership": "SC0"},
    "austria": {"bundesliga": "AUT", "austrianbundesliga": "AUT", "austrianfootballbundesliga": "AUT"},
    "switzerland": {"superleague": "SWZ", "swissfootballleague": "SWZ", "swisssuperleague": "SWZ"},
    "denmark": {"superliga": "DNK", "danishsuperliga": "DNK"},
    "romania": {"superliga": "ROU", "liga1": "ROU", "romaniansuperliga": "ROU"},
    "poland": {"ekstraklasa": "POL"},
}
EXTS = {".svg", ".png", ".webp", ".jpg", ".jpeg"}
FILLER = {"fc", "afc", "cf", "sc", "ac", "as", "cd", "sk", "fk", "sv", "ssc", "club", "calcio", "the", "kv", "krc"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return "".join(t for t in re.split(r"[^a-z0-9]+", s) if t and t not in FILLER)


def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def parse(path: Path, inbox: Path) -> tuple[str | None, str]:
    rel = path.relative_to(inbox)
    if len(rel.parts) > 1 and rel.parts[0].lower() in COUNTRY_LEAGUES:
        return rel.parts[0].lower(), path.stem
    stem = re.sub(r"[_-]\d+x\d+$", "", path.stem)  # e.g. vaduz_128x128
    country, _, team = stem.partition("_")
    return (country.lower(), team) if country.lower() in COUNTRY_LEAGUES else (None, path.stem)


def main() -> int:
    cfg = load_config()
    root = project_path(".")
    inbox = root / "logos" / "inbox"
    out_dir = root / "web" / "public" / "teams"
    manifest_path = root / "web" / "data" / "team_logos.json"
    league_dir = root / "web" / "public" / "leagues"
    league_manifest_path = root / "web" / "data" / "league_logos.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    league_dir.mkdir(parents=True, exist_ok=True)

    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    teams = {lg: set(g["home"]) | set(g["away"]) for lg, g in matches.groupby("league")}
    latest = matches.groupby("league")["season"].max()
    current = {lg: set(g["home"]) | set(g["away"])
               for lg, g in matches[matches["season"] == matches["league"].map(latest)].groupby("league")}
    aliases = (yaml.safe_load(project_path(cfg["fixtures"]["team_names"]).read_text()) or {}).get("football") or {}
    names_file = root / "logos" / "names.yaml"
    overrides = (yaml.safe_load(names_file.read_text()) or {}) if names_file.exists() else {}

    plan, manifest, league_manifest, unmatched = [], {}, {}, []
    for f in sorted(p for p in inbox.rglob("*") if p.suffix.lower() in EXTS):
        country, team = parse(f, inbox)
        code = LEAGUE_FILES.get(country or "", {}).get(norm(team))
        if code:
            dest = league_dir / f"{code.lower()}.webp"
            plan.append({"src": str(f), "dest": str(dest)})
            league_manifest[code] = f"/leagues/{dest.name}"
            continue
        leagues = COUNTRY_LEAGUES.get(country) if country else list(teams)
        pool = set().union(*(teams.get(lg, set()) for lg in leagues))
        hit = overrides.get(f.stem)
        if hit == "skip":  # deliberately unused (e.g. a competition we don't cover)
            continue
        if hit is not None and hit not in pool:
            unmatched.append((f.name, f"names.yaml target {hit!r} not found in {leagues}"))
            continue
        if hit is None:
            keys: dict[str, set[str]] = {}
            for t in pool:
                keys.setdefault(norm(t), set()).add(t)
            for a, t in aliases.items():
                if t in pool:
                    keys.setdefault(norm(str(a)), set()).add(t)
            found = keys.get(norm(team), set())
            if len(found) == 1:
                hit = next(iter(found))
            else:
                why = f"ambiguous {sorted(found)}" if found else "suggestions " + str(
                    difflib.get_close_matches(team.replace("-", " "), sorted(pool), n=3, cutoff=0.3))
                unmatched.append((f.name, why))
                continue
        if hit in manifest:
            unmatched.append((f.name, f"duplicate: {hit} already has a logo"))
            continue
        dest = out_dir / f"{slug(hit)}.webp"
        plan.append({"src": str(f), "dest": str(dest)})
        manifest[hit] = f"/teams/{dest.name}"

    if plan:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(plan, tmp)
        r = subprocess.run(["node", "scripts/convert-logos.mjs", tmp.name], cwd=root / "web")
        if r.returncode:
            return r.returncode
    manifest_path.write_text(json.dumps(dict(sorted(manifest.items())), indent=1, ensure_ascii=False) + "\n")
    league_manifest_path.write_text(json.dumps(dict(sorted(league_manifest.items())), indent=1) + "\n")

    print(f"\n{len(manifest)} logos matched -> {manifest_path.relative_to(root)}")
    print(f"{len(league_manifest)} league logos: {', '.join(sorted(league_manifest))}")
    if unmatched:
        print(f"\nNOT MATCHED ({len(unmatched)}) - rename the file or add `stem: Team Name` to logos/names.yaml:")
        for name, why in unmatched:
            print(f"  {name}: {why}")
    print("\nCoverage this season (teams with a logo):")
    for lg in cfg["football_data"]["leagues"]:
        have = current.get(lg, set())
        n = len([t for t in have if t in manifest])
        print(f"  {lg:4} {n:2}/{len(have)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
