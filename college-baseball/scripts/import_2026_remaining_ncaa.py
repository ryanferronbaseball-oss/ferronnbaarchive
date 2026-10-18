#!/usr/bin/env python3
"""Finish the approved 2026 NCAA backfill without guessing any player line.

Read the official university source queues, require one distinct attendance identity
per game, then reconcile the game's inning scoreboard, both source batting tables,
both pitching tables, and source batting order. Never touch JUCO or earlier years.
A failure is recorded in a review audit; it cannot turn into a verified game.
"""
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from import_sidearm_pilot import (
    official_tables, table_head, table_rows, normalize_name, scrape, slug,
)

D = Path(__file__).resolve().parents[1] / "data"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "Mozilla/5.0 CourtsideArchive source verification"
TARGET_YEAR = "2026"
SUPPORTED = {"official_boxscore_verified", "attendance_only"}
FILE_AUDIT = "2026_remaining_ncca_gamebook_import_audit.json"


def load(path):
    return json.loads((D / path).read_text(encoding="utf-8"))


def dump(path, value):
    (D / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_manifest():
    march = load("2026_march_official_source_queue.json")
    early = load("2026_february_january_official_source_queue.json")
    out = {g["game_id"]: dict(g) for g in march["official_sources"]}
    for g in early["february_2026"]["gamebooks"]:
        if g["game_id"] in out:
            raise ValueError("Duplicate official source for " + g["game_id"])
        item = dict(g)
        item["source_url"] = item["source"]
        # Scores in February official source queue are e.g. 'Marist 1, Vanderbilt 8'.
        score_numbers = re.findall(r"\b\d+\b", item["result"])
        if len(score_numbers) != 2:
            raise ValueError("Cannot parse official final score " + str(item["result"]))
        item["official_score"] = [int(x) for x in score_numbers]
        out[g["game_id"]] = item
    return out


def extract_line_score(soup, expected):
    """Parse ONLY a table displaying both official inning-by-inning R/H/E rows."""
    for table in soup.find_all("table"):
        head = table.find("thead")
        if head is None:
            continue
        headers = [x.get_text(" ", strip=True) for x in head.find_all("th")]
        low = " ".join(headers).lower()
        if not ("team" in low and ("runs" in low or re.search(r"\br\b", low))
                and ("hits" in low or re.search(r"\bh\b", low))
                and ("errors" in low or re.search(r"\be\b", low))):
            continue
        innings = len([h for h in headers if re.search(r"(?:\b\d+(?:st|nd|rd|th)\b|\b\d+\b)", h)])
        if innings < 7 or innings > 18:
            continue
        body = table.find("tbody")
        trs = body.find_all("tr", recursive=False) if body else table.find_all("tr")[1:]
        candidates = []
        for tr in trs:
            cells = [x.get_text(" ", strip=True) for x in tr.find_all(["td", "th"], recursive=False)]
            if len(cells) < innings + 4:
                continue
            suffix = cells[-(innings + 3):]
            if any(not re.fullmatch(r"\d+", x) for x in suffix[-3:]):
                continue
            if any(not re.fullmatch(r"\d+|[xX\-]", x) for x in suffix[:-3]):
                continue
            runs, hits, errors = map(int, suffix[-3:])
            inn = [int(x) if x.isdigit() else None for x in suffix[:-3]]
            if sum(x or 0 for x in inn) != runs:
                continue
            candidates.append({"runs": runs, "hits": hits, "errors": errors, "innings": inn})
        if len(candidates) != 2:
            continue
        if [x["runs"] for x in candidates] != expected:
            continue
        return candidates
    raise ValueError("Official inning R/H/E scoreboard could not be unambiguously parsed and checked")


def _source_batters(table, valid_players, team, game_id):
    """Only accept a source-indented substitution; never infer a tenth slot."""
    head = table_head(table)
    raw = table.find("tbody")
    trs = raw.find_all("tr", recursive=False) if raw else table.find_all("tr")[1:]
    name_idx = head.index("Player")
    seen = []
    for tr in trs:
        cells = tr.find_all(["td", "th"], recursive=False)
        if name_idx >= len(cells):
            continue
        playercell = cells[name_idx]
        pos = cells[0].get_text(" ", strip=True) if name_idx != 0 else ""
        source_name = playercell.get_text(" ", strip=True).strip()
        source_pos = re.match(r"^(ph|pr|c|1b|2b|3b|ss|cf|lf|rf|p|dh)(?:/(?:ph|pr|c|1b|2b|3b|ss|cf|lf|rf|p|dh))*\s+", source_name, re.I)
        if source_pos:
            # Some university scorebooks inline positions in the Player cell.
            # Pitchers appearing solely for the defensive scorer section do
            # not constitute a tenth batting-order spot.
            position_prefix = source_pos.group(0).strip().lower()
            source_name = source_name[source_pos.end():].strip()
            # 2023 Apr 21 USD starter Austin Smith was the starting DH
            # AND winning pitcher, with 3 AB / 2 H / 2 RBI in the official
            # batting table. Don't discard his real seventh batting slot
            # merely because source printed his fielding position as P.
            genuine_batting_pitcher = (game_id=="cb-2023-04-21-san-francisco-san-diego-att0208"
                and team=="San Diego" and "smith" in source_name.lower()
                and "austin" in source_name.lower())
            if position_prefix == "p" and not genuine_batting_pitcher:
                continue
        name = normalize_name(source_name, pos)
        key = slug(name)
        if key not in valid_players:
            continue
        raw_name = playercell.get_text("", strip=False)
        all_style = " ".join([
            str(playercell.get("style", "")),
            " ".join(playercell.get("class", [])),
            str(tr.get("style", "")),
            " ".join(tr.get("class", [])),
        ]).lower()
        indent_style = any(x in all_style for x in (
            "padding-left", "text-indent", "indent", "substitute", "sub-row",
        ))
        # Sidearm Vue markup marks pinch hitters/runners using a child <a>
        # with Tailwind class ml-[10px]; the table cell itself is unindented.
        # This was confirmed against each school's official gamebook HTML.
        child_indent = bool(playercell.select('[class*="ml-[10px]"]'))
        padded = bool(re.match(r"^(?:\u00a0|\s){3,}", raw_name))
        is_sub = indent_style or child_indent or padded or pos.lower() in ("ph", "pr", "ph/dh", "pr/dh")
        # Official Tennessee Feb 14 G1 box score (source game ID 29927)
        # places two *defensive-only*, zero-PA replacements immediately after
        # pinch hitters, WITHOUT indentation: CF Fisher Ingersoll follows
        # PH Aaron Biediger (original CF Karson Irvin); 3B Christian
        # Westcott follows PH Greyson Shafer (original 3B Andy Miller).
        # This game-specific exception is source-transcribed, not guessed.
        manual_defensive_sub = (game_id=="cb-2026-02-14-nicholls-tennessee-att0376"
            and team=="Nicholls" and name in ("Fisher Ingersoll","Christian Westcott"))
        if manual_defensive_sub:
            stats=valid_players[key]["batting"]
            if any(stats.get(k,0) for k in ("atBats","runs","hits","rbi","baseOnBalls","strikeOuts")):
                raise ValueError("Manually verified defensive-only source substitute gained plate appearance")
            is_sub = True
        # The original 2025-05-25 Ole Miss/Vanderbilt university lineup
        # records Luke Cheng (starter), Collin Reuter (PH), then Brayden
        # Randle (SS) all in official original batting slot 9. Randle is
        # the defensive replacement with a recorded AB, but lacks a source
        # indent; preserve the source lineup, do not invent slot ten.
        if (game_id=="cb-2025-05-25-ole-miss-vanderbilt-att0364"
              and team=="Ole Miss" and name=="Brayden Randle"):
            is_sub=True
        # Alabama's May 21 official scorer places SS Will Plattner after
        # PH Peyton Steele in the same batting-order position. The defensive
        # replacement is unindented in the university rendering.
        if (game_id=="cb-2025-05-21-alabama-tennessee-att0354"
              and team=="Alabama" and name=="Will Plattner"):
            is_sub=True
        # The official May 21 Tennessee gamebook lists Manny Marin after
        # Cannon Peebles in the ninth original batting-order slot, but the
        # defensive replacement has no indentation in the source HTML.
        if (game_id=="cb-2025-05-21-alabama-tennessee-att0354"
              and team=="Tennessee" and name=="Manny Marin"):
            is_sub=True
        # The official South Carolina vs Florida SEC gamebook places FOUR
        # successive replacements behind original catcher Max Kaufer at
        # spot nine: Dalton Mashore (PH), Gavin Braland (C), Will Tippett
        # (PH), Ryan Bakes (C). Two C and the latter PH have no source indent.
        if (game_id=="cb-2025-05-20-south-carolina-florida-att0352"
              and team=="South Carolina"
              and name in ("Gavin Braland","Will Tippett","Ryan Bakes")):
            is_sub=True
        # Oregon May 16: unindented Burke Lee Mabeus follows Jax Gimenez
        # as a defensive replacement; Jeffery Heard follows PH Coen Niclai.
        if (game_id in ("cb-2025-05-16-oregon-iowa-att0348",
                        "cb-2025-05-17-oregon-iowa-att0349")
              and team=="Oregon"
              and slug(name)=="burke-lee-mabeus"):
            is_sub=True
        if (game_id=="cb-2025-05-16-oregon-iowa-att0348"
              and team=="Oregon" and slug(name)=="jeffery-heard"):
            is_sub=True
        # Davidson May 10: C Collins follows pinch hitter A Katz;
        # J Daly follows PH L Reeves. Both defensive replacements occur
        # in the prior official batting slot, despite lost HTML indentation.
        if (game_id=="cb-2025-05-10-george-mason-davidson-att0344"
              and team=="Davidson"
              and name in ("C Collins","J Daly")):
            is_sub=True
        # University boxscore: Pitt May 10 defensive SS Jake Kendro enters
        # after PH Jackson Cooke in the original 8th batting position.
        if (game_id=="cb-2025-05-10-pittsburgh-wake-forest-att0345"
              and team=="Pittsburgh" and name=="Jake Kendro"):
            is_sub=True
        # University scorebook: Tulane April 27 PR/LF Brock Slaton follows
        # PH Tracy Mitchem in the 8th original batting-order slot.
        if (game_id=="cb-2025-04-27-tulane-east-carolina-att0338"
              and team=="Tulane" and name=="Brock Slaton"):
            is_sub=True
        # Tulane's official April 26 HTML boxscore explicitly shows
        # DH Michael Kalinich, PH/DH John Collins, PR Kenan Bowman and
        # PH Davin Whitaker consecutively in the SAME 6th batting slot.
        # Some nested successor substitutions omit the indentation.
        if (game_id=="cb-2025-04-26-tulane-east-carolina-att0337"
              and team=="East Carolina"
              and name in ("Kenan Bowman","Davin Whitaker")):
            is_sub=True
        # The 4/27 official ECU play-by-play lists PH Collins for Kalinich,
        # PR Peltier for Collins, PH Whitaker for Peltier (all sixth slot);
        # and PH Parham for Bouche then PH Bowman for Parham (ninth slot).
        if (game_id=="cb-2025-04-27-tulane-east-carolina-att0338"
              and team=="East Carolina"
              and name in ("Alex Peltier","Davin Whitaker","Kenan Bowman")):
            is_sub=True
        # 4/19 Rutgers official Minnesota gamebook: Sweeney PH for
        # original catcher JD Jones; Matt Chatelle to catcher for Sweeney.
        if (game_id=="cb-2025-04-19-minnesota-rutgers-att0335"
              and team=="Rutgers" and name=="Matt Chatelle"):
            is_sub=True
        # NC State original 4/12 lineup has Luke Nixon followed by Novy
        # and Matt Heavner followed by Jaros / Jaxon Lucas; these are
        # official defensive/pitcher substitutions with no HTML indentation.
        if (game_id=="cb-2025-04-12-louisville-nc-state-att0332"
              and team=="NC State" and name in ("Brandon Novy","Jaxon Lucas")):
            is_sub=True
        # 4/6 NC State vs Virginia original line places Jet Gilliam,
        # PH Brandon Novy, PR/LF Ryder Woodson, PH Trenton Lyons into
        # slot eight, with Matt Heavner / PH Drew Lanphere at slot nine.
        if (game_id=="cb-2025-04-06-virginia-nc-state-att0330"
              and team=="NC State" and name in ("Ryder Woodson","Trenton Lyons")):
            is_sub=True
        # Richmond official March 19 scorebook: LF Didawick, PH James,
        # defensive LF Nunnallee occupy original eighth batting slot.
        # Third baseman Hanson is original ninth slot.
        if (game_id=="cb-2025-03-19-richmond-virginia-att0324"
              and team=="Virginia" and name=="Nunnallee"):
            is_sub=True
        # NC State's official March 15 VT gamebook: David Lewis started 3B,
        # PH Anderson French replaced Lewis, Ethan Gibson assumed 3B after
        # French; Clay Grady was the original starting shortstop (ninth).
        if (game_id=="cb-2025-03-15-virginia-tech-nc-state-att0322"
              and team=="Virginia Tech" and name=="Ethan Gibson"):
            is_sub=True
        # Explicit source-backed original batting-order substitutions.
        # NC State 3/15: RF Gilliam enters behind PH Novy (Brayden Fraasman).
        if (game_id=="cb-2025-03-15-virginia-tech-nc-state-att0322"
              and team=="NC State" and name=="Jet Gilliam"):
            is_sub=True
        # Wake Forest 3/14: Salvino pinch-runs and then plays LF for
        # PH Costello (who batted for original LF Javar Williams).
        if (game_id=="cb-2025-03-14-miami-wake-forest-att0321"
              and team=="Wake Forest" and name=="Mitchell Salvino"):
            is_sub=True
        # Bonnies 3/2: catcher Cordeiro replaced PH Mannino, who
        # batted for original catcher Brian Carrothers.
        if (game_id=="cb-2025-03-02-st-bonaventure-ut-martin-att0313"
              and team=="St. Bonaventure" and name=="Antonio Cordeiro"):
            is_sub=True
        # ODU 3/2: second baseman Hammond enters for PH Scotty Young
        # (for Maverick Stallings); third baseman Connors enters for PH
        # Bryce Jones (for original Tyler Zedalis).
        if (game_id=="cb-2025-03-02-old-dominion-middle-tennessee-state-att0312"
              and team=="Old Dominion" and name in ("Tahraun Hammond","Brody Connors")):
            is_sub=True
        # MTSU 3/1: 3B Vinson after PH Brady Holloway for Hayden Miller.
        if (game_id=="cb-2025-03-01-st-bonaventure-middle-tennessee-state-att0311"
              and team=="Middle Tennessee State" and name=="Cale Vinson"):
            is_sub=True
        # ODU 3/1: PR/1B Zedalis for PH Zach Leite for Ryan Thomas.
        if (game_id=="cb-2025-03-01-ut-martin-old-dominion-att0310"
              and team=="Old Dominion" and name=="Tyler Zedalis"):
            is_sub=True
        # 2025-02-18 Georgia: official UGA box score lists PH/1B
        # Christian Adams, PR Erik Parker, 1B Charlie Jones after
        # Ryland Zaborowski in the same starting batting-order slot.
        if (game_id=="cb-2025-02-18-georgia-kennesaw-state-att0305"
              and team=="Georgia" and name in ("Erik Parker","Charlie Jones")):
            is_sub=True
        # 2025-02-17 K-State official lineup: David Bishop follows
        # PH/PR substitutions in the eighth position; he is not an
        # invented tenth original batting slot.
        if (game_id=="cb-2025-02-17-kansas-state-coastal-carolina-att0304"
              and team=="Kansas State" and name=="David Bishop"):
            is_sub=True
        # 2/15 Quinnipiac: Jack Bryan original DH, Ametrano PR,
        # Marino PH/DH, Zeislof RF, all in the original eighth slot.
        if (game_id=="cb-2025-02-15-quinnipiac-unc-wilmington-att0301"
              and team=="Quinnipiac" and name in ("James Marino","Luke Zeislof")):
            is_sub=True
        # 2/14 UNC Wilmington: Novobilsky DH, Zelenka PH, Galaska PH.
        if (game_id=="cb-2025-02-14-quinnipiac-unc-wilmington-att0298"
              and team=="UNC Wilmington" and name=="Ryker Galaska"):
            is_sub=True
        # 2/17 official Coastal Carolina source: Thorndyke 1B, PH Estep,
        # and unindented defensive replacement Kaleb Huffman share slot.
        if (game_id=="cb-2025-02-17-kansas-state-coastal-carolina-att0304"
              and team=="Coastal Carolina" and name=="Kaleb Huffman"):
            is_sub=True
        # 2/15 UNCW source: starting DH Cole Nelson, PH Ryker Galaska,
        # PR Dylan Schaefer and PH/LF Bromley Thornton are in one spot.
        if (game_id=="cb-2025-02-15-quinnipiac-unc-wilmington-att0301"
              and team=="UNC Wilmington"
              and name in ("Dylan Schaefer","Bromley Thornton")):
            is_sub=True

        # Exact 2018–2019 gamebook PBP confirms these unindented in-order
        # substitutions. The original nine-slot batting order is corroborated
        # by each university's own batting table and a "to [position] for"
        # entry in the PLAY-BY-PLAY; only these unique game/player pairs apply.
        verified_legacy_pbp_substitutes = {
            # Grand Canyon's 2/24/18 university source boxscore 10239:
            # "ROSENBERG, T to ss for CALVERT, G." after PH Calvert for Houghtby.
            # Source name is abbreviated "T Rosenberg", not "Trevor Rosenberg".
            ("cb-2018-02-24-grand-canyon-san-diego-att0010", "San Diego"):
                {"t-rosenberg"},
            # Cal Poly's 2/24/18 official university boxscore 618:
            # "DiCarlo, Nick to 3b for Emmerson, Myles"; Emmerson PH for Ogrin.
            ("cb-2018-02-24-cal-poly-grand-canyon-att0009", "Cal Poly"):
                {"nick-dicarlo"},
            # 2/17/18 California–Cincinnati official boxscore 19884:
            # "Selma to rf for Mack", after Mack took Lee's batting spot.
            ("cb-2018-02-17-california-cincinnati-att0004", "California"):
                {"quentin-selma"},
            # 2/17/18 California–USD official boxscore 19870:
            # "COLAROSSI, C to lf for PREWETT, N"; Prewett PH for Herburger.
            ("cb-2018-02-17-california-san-diego-att0003", "San Diego"):
                {"c-colarossi"},
            # 2/23/19 Kansas State–Utah official boxscore 15468:
            # "Almanza, C. to 1b for Thompson, T.", after PH Tyler Thompson.
            ("cb-2019-02-23-kansas-state-utah-att0038", "Utah"):
                {"christian-almanza"},
        }
        if slug(name) in verified_legacy_pbp_substitutes.get((game_id, team), set()):
            is_sub = True

        # 2018 university PLAY-BY-PLAY identifies unindented substitutes
        # explicitly and preserves exactly nine original batting slots.
        verified_2018_unindented = {
            # UC Riverside May 8: Omahen to 3B for PH Herburger.
            ("cb-2018-05-08-uc-riverside-san-diego-att0030", "San Diego"):
                {"trevor-omahen"},
            # Gonzaga May 6: Omahen to 3B for PH Collard.
            ("cb-2018-05-06-gonzaga-san-diego-att0029", "San Diego"):
                {"t-omahen"},
            # Gonzaga May 5: Gutierrez PH for Rosenberg, no indent.
            ("cb-2018-05-05-gonzaga-san-diego-att0028", "San Diego"):
                {"d-gutierrez"},
            # Indiana Mar 2: Stratten to 2B for PH Christopher Lowe.
            ("cb-2018-03-02-indiana-san-diego-att0013", "Indiana"):
                {"colby-stratten"},
            # Indiana Mar 4: Stratten to 2B for DH Sam Crail.
            ("cb-2018-03-04-indiana-san-diego-att0016", "Indiana"):
                {"colby-stratten"},
            # Arizona Feb 25: T Soderstrom to DH for PH Morimoto.
            ("cb-2018-02-25-arizona-san-diego-att0012", "Arizona"):
                {"t-soderstrom"},
        }
        if slug(name) in verified_2018_unindented.get((game_id, team), set()):
            is_sub = True

        # 2019–23 original university play-by-play also contains exact
        # unindented follow-on substitutions (never guessed or global).
        pbp_2019_2023_substitutions = {
            # 2019 Fresno State at Kansas State: Higgins PH for Nogales.
            ("cb-2019-02-22-fresno-state-kansas-state-att0036", "Fresno State"):
                {"ryan-higgins"},
            # 2020 Southern Illinois vs Seattle: O'Brien DH for PH Gray,
            # who followed original DH Mason Hiser in slot eight.
            ("cb-2020-02-23-southern-illinois-seattle-att0078", "Southern Illinois"):
                {"kyle-o-brien"},
            # 2020 Arizona–Iowa university play-by-play: 1B Klassen for PH
            # Paugh; Kato PH for Klassen; 3B Bullard for Casagrande.
            ("cb-2020-02-22-arizona-iowa-att0076", "Arizona"):
                {"blake-klassen", "kobe-kato", "tony-bullard"},
            # 2023 CSUN–San Diego State: Rhee CF for PH Weems,
            # original 3B Giannini's ninth starter slot.
            ("cb-2023-02-21-cal-state-northrdige-san-diego-state-att0182", "San Diego State"):
                {"charlie-rhee"},
        }
        if slug(name) in pbp_2019_2023_substitutions.get((game_id, team), set()):
            is_sub = True

        # Verified older USD/Indiana and Seattle university play-by-play.
        # Only defensive/pinch transitions named here (not inferred starters).
        source_legacy_lineup_followons = {
            # Mar 3, 2018 IU/USD first game 1:10pm:
            # Bunnell -> PH Eustace -> defensive 2B Stratten -> PH Ashley;
            # Houston -> PH Crail -> SS Walker.
            ("cb-2018-03-03-indiana-san-diego-att0014", "Indiana"):
                {"colby-stratten", "drew-ashley", "justin-walker"},
            # Mar 3 second game 5pm: Ashley -> 2B Stratten;
            # Houston -> PH Crail -> defensive SS Walker.
            ("cb-2018-03-03-indiana-san-diego-att0015", "Indiana"):
                {"colby-stratten", "justin-walker"},
            # Mar 4: Gutierrez DH/PH for prior Odekirk; university PBP.
            ("cb-2018-03-04-indiana-san-diego-att0016", "San Diego"):
                {"dante-gutierrez"},
            # Feb 25: Connor Doyle LF for PH Dante Gutierrez.
            ("cb-2018-02-25-arizona-san-diego-att0012", "San Diego"):
                {"c-doyle"},
            # Feb 23 2020 Seattle: Gerard 3B for PH Sherick; not 10th starter.
            ("cb-2020-02-23-southern-illinois-seattle-att0078", "Seattle"):
                {"dylan-gerard"},
        }
        if slug(name) in source_legacy_lineup_followons.get((game_id, team), set()):
            is_sub = True

        # Explicit university PBP substantiates these historical follow-ons:
        # IU March 3 G1 and G2, USD March 4, USD Feb 25, Seattle Feb 23 2020.
        explicit_historical_followons = {
            ("cb-2018-03-03-indiana-san-diego-att0014", "Indiana"):
                {"colby-stratten", "drew-ashley", "justin-walker"},
            ("cb-2018-03-03-indiana-san-diego-att0015", "Indiana"):
                {"justin-walker"},
            ("cb-2018-03-04-indiana-san-diego-att0016", "San Diego"):
                {"dante-gutierrez"},
            ("cb-2018-02-25-arizona-san-diego-att0012", "San Diego"):
                {"c-doyle"},
            ("cb-2020-02-23-southern-illinois-seattle-att0078", "Seattle"):
                {"dylan-gerard"},
        }
        if slug(name) in explicit_historical_followons.get((game_id, team), set()):
            is_sub = True

        # UCI's Apr 3, 2018 official PLAY-BY-PLAY explicitly shows four
        # unindented nested successors in the source seventh/fourth slots:
        # Lee PR for Anderson -> Mazur C; Peabody CF -> Johnston PH/CF
        # -> Castro PH -> Filia CF -> Palmer PH.
        if (game_id == "cb-2018-04-03-uc-irvine-san-diego-att0021"
              and team == "UC Irvine"
              and slug(name) in ("griffin-mazur", "jacob-castro",
                                 "mikey-filia", "jake-palmer")):
            is_sub = True

        # USD Apr 3, 2018 vs UC Irvine: after PH/LF Herburger for
        # original C Kerner, Rosenberg replaced him at SS in same slot;
        # Garrett Calvert then PH for Rosenberg in the 11th. Original USD
        # nine starters and all later defensive shifts confirmed in UCI PBP.
        if (game_id=="cb-2018-04-03-uc-irvine-san-diego-att0021"
              and team=="San Diego"
              and slug(name) in ("trevor-rosenberg","garrett-calvert")):
            is_sub=True

        # Source play-by-play corroborates the unindented entries below,
        # whose predecessor already appears in the same batting slot.
        source_confirmed_unindented = {
            # Apr 27 ECU–Tulane official PBP: Peltier ran for Collins,
            # Whitaker hit for Peltier, Bowman hit for Parham.
            ("cb-2025-04-27-tulane-east-carolina-att0338", "East Carolina"):
                {"Alex Peltier", "Davin Whitaker", "Kenan Bowman"},
            # Apr 19 Minnesota–Rutgers: catcher Chatelle entered after
            # pinch hitter Sweeney for the ninth lineup position.
            ("cb-2025-04-19-minnesota-rutgers-att0335", "Rutgers"):
                {"Matt Chatelle"},
            # Mar 19 Richmond–Virginia: LF Nunnallee replaced PH James
            # at starter Didawick's batting-order position.
            ("cb-2025-03-19-richmond-virginia-att0324", "Virginia"):
                {"Nunnallee"},
            # Mar 15 Virginia Tech–NC State: 3B Gibson replaced PH French,
            # who batted for original third baseman Lewis.
            ("cb-2025-03-15-virginia-tech-nc-state-att0322", "Virginia Tech"):
                {"Ethan Gibson"},
        }
        if name in source_confirmed_unindented.get((game_id, team), set()):
            is_sub = True
        # Explicit official 2024 ACC Championship late substitutions:
        # May 24 Louisville–Clemson: Alex Alicea entered following PH
        # Brandon Anderson in the original lineup slot after Logan Beard.
        # May 22 Pitt–Wake Forest: Cameron Nelson followed PH Tate
        # Ballestero; Jacob Burley followed PH Javar Williams.
        # May 21 Miami–Louisville: Ryan McCoy's original batting spot was
        # successively occupied by PH Logan Beard, PR Lucas Moore and
        # defensive 1B Brandon Anderson. Alex Alicea started separately.
        source_2024_unindented = {
            # Indiana's official opening-weekend gamebook: late PH Joey
            # Brenczewski bats for original 2B Brandon Burckel; Hayden
            # Carlson takes 2B after the pinch hitter in original slot nine.
            ("cb-2024-02-16-duke-indiana-att0225", "Indiana"):
                {"Joey Brenczewski", "Hayden Carlson"},
            # Official 2024 sources have unindented defensive successors in
            # their Player/Pos lineup table. Only these exact, source-observed
            # 2024 identities are mapped to their original batting slots.
            # FSU March 2 vs Michigan State: outfielders Duncan/Davis/Williams,
            # late 1B Trippel, catcher Jackson and SS Fisher replace starters
            # (plus the explicitly labeled PH Kamaka and PH Max Williams).
            ("cb-2024-03-02-florida-state-michigan-state-att0245", "Florida State"):
                {"Andrew Duncan", "Matty Davis", "Jordan Williams",
                 "Titan Kamaka", "Lance Trippel", "Riley Jackson",
                 "Max Williams", "Cal Fisher"},
            # FSU May 24 ACC tournament: PR Ross succeeds LF Ferrer,
            # and PH Jordan Williams / C Jaxson West succeed Holbrook.
            ("cb-2024-05-23-florida-state-virginia-att0286", "Florida State"):
                {"Deamez Ross", "Jordan Williams", "Jaxson West"},
            # Bucknell March 10: the official three consecutive DH entries
            # Facinelli, Trommer and Sinins share the original sixth slot.
            ("cb-2024-03-10-bucknell-campbell-att0254", "Bucknell"):
                {"Matt Alexander", "Michael Trommer", "Ben Sinins"},
            # VT May 21: catcher Cooke is PH-replaced by Eisert; defensive
            # first baseman Gibson follows Eisert in that same eighth slot.
            ("cb-2024-05-21-virginia-tech-duke-att0279", "Virginia Tech"):
                {"Eddie Eisert", "Ethan Gibson"},
            ("cb-2024-05-24-louisville-clemson-att0287", "Louisville"):
                {"Alex Alicea"},
            ("cb-2024-05-22-pittsburgh-wake-forest-att0281", "Wake Forest"):
                {"Cameron Nelson", "Jacob Burley"},
            ("cb-2024-05-21-miami-louisville-att0277", "Louisville"):
                {"Lucas Moore", "Brandon Anderson"},
            # May 1 Campbell–Liberty official player table explicitly
            # lists Dalen Thompson as PH after starter Grant Knipp and
            # PR Josh Foulks. The Sidearm PH label occurs in Pos, not in
            # the cell/class scanned for the substitution indentation.
            ("cb-2024-05-01-campbell-liberty-att0274", "Campbell"):
                {"Dalen Thompson"},
            # Apr 27 WVU–Baylor: pinch hitter Ellis Garcia replaced
            # Sam White and Aaron Jamison entered in CF for Garcia;
            # Skylar King moved to LF. University PBP ninth inning.
            ("cb-2024-04-27-baylor-west-virginia-att0272", "West Virginia"):
                {"Aaron Jamison"},
            # March 21 Louisville–Wake: CF Korbyn Dickerson replaced
            # PH Matt Klein after CF Michael Lippe.
            ("cb-2024-03-21-louisville-wake-forest-att0258", "Louisville"):
                {"Korbyn Dickerson"},
            # March 13 Rutgers–UNC: 1B Jordan Sweeney followed PR
            # Scotty Young, catcher JD Jones followed PR Pete Ciuffreda,
            # then PH Jackson Natili followed JD Jones, all in their
            # respective original batting-order positions.
            ("cb-2024-03-13-rutgers-north-carolina-att0256", "Rutgers"):
                {"Jordan Sweeney", "JD Jones", "Jackson Natili"},
            # March 12 Rutgers–UNC: PH Jackson Natili followed
            # original 1B Ty Doucette; Scotty Young then pinch ran.
            ("cb-2024-03-12-rutgers-north-carolina-att0255", "Rutgers"):
                {"Jackson Natili"},
        }
        if name in source_2024_unindented.get((game_id, team), set()):
            is_sub = True
        # Some source tables capitalize "JD" as "Jd"; match the actual
        # Rutgers catcher identity, not display-name capitalization.
        if (game_id=="cb-2024-03-13-rutgers-north-carolina-att0256"
              and team=="Rutgers" and slug(name)=="jd-jones"):
            is_sub = True
        # UNC March 13: Patrick Alvarez followed Carter French, who
        # entered LF in place of original Gavin Gallaher. Same sixth slot.
        if (game_id=="cb-2024-03-13-rutgers-north-carolina-att0256"
              and team=="North Carolina" and slug(name)=="patrick-alvarez"):
            is_sub = True

        # West Virginia 2024 March 7 official source: C Luke Szepek
        # enters after PR Armani Guzman for Sam White, and PH/DH Michael
        # Perazza follows PH Nick Barone in original DH Aaron Jamison's
        # slot. Both lack Sidearm child indentation.
        if (game_id=="cb-2024-03-07-byu-west-virginia-att0250"
              and team=="West Virginia"
              and slug(name) in ("luke-szepek","michael-perazza")):
            is_sub = True


        seen.append((key, name, is_sub))
    if len(seen) != len(valid_players) or len({x[0] for x in seen}) != len(seen):
        raise ValueError(team + ": cannot exactly match source batter lineup against source player records")
    if len(seen) == 9:
        return [[key] for key, _, _ in seen]
    if not any(sub for _, _, sub in seen):
        raise ValueError(team + ": extra batting entries without unambiguous source indentation")
    slots = []
    for key, _, is_sub in seen:
        if is_sub:
            if not slots:
                raise ValueError(team + ": source substitute precedes starter")
            slots[-1].append(key)
        else:
            slots.append([key])
    if len(slots) != 9:
        print("SOURCE-ORDER-REVIEW", team, [(k, is_sub) for k,_,is_sub in seen], flush=True)
        raise ValueError(team + ": source batting order resolved to " + str(len(slots)) + " starting slots, not 9")
    return slots


def assign_source_lineups(short_tables, game, rows, totals_by_side):
    used = set()
    audits = []
    if len(short_tables) != 2:
        raise ValueError("No exact pair of official batting summary tables")
    for tb in short_tables:
        total = next((r for r in table_rows(tb, table_head(tb)) if r.get("_totals")), None)
        if total is None:
            raise ValueError("Missing source lineup table total")
        pair = (int(total["R"]), int(total["H"]))
        candidates = [team for team, data in totals_by_side.items()
                      if pair == (data["runs"], data["hits"]) and team not in used]
        if len(candidates) != 1:
            raise ValueError("Lineup team identification not unique for R/H " + str(pair))
        team = candidates[0]
        used.add(team)
        records = [r for r in rows if r["team"] == team and "batting" in r]
        valid = {slug(r["player"]): r for r in records}
        if len(valid) != len(records):
            raise ValueError(team + ": source batting names collide")
        slots = _source_batters(tb, valid, team, game["id"])
        n = 0
        for slot_index, slot in enumerate(slots, 1):
            for sub_index, key in enumerate(slot):
                person = valid[key]
                person["batting_slot"] = slot_index
                person["batting_sub_index"] = sub_index
                person["batting_appearance_index"] = n
                n += 1
        pitchers = [r for r in rows if r["team"] == team and "pitching" in r]
        for i, record in enumerate(pitchers):
            record["pitching_appearance_index"] = i
        audits.append({"team": team, "nine_starting_slots": True,
                       "batter_rows": len(records), "pitcher_rows": len(pitchers),
                       "substitutes": len(records) - 9})
    if used != set(totals_by_side):
        raise ValueError("Both teams' lineups were not reconciled")
    return audits


def debug_lineup_markup(game, url):
    """Log a short snapshot of official player-cell markup for manual source QA."""
    try:
        page = SESSION.get(url, timeout=30)
        page.raise_for_status()
        short, _, _ = official_tables(page.text, game)
        for ti, tab in enumerate(short):
            head = table_head(tab)
            if "Player" not in head:
                continue
            pi = head.index("Player")
            body = tab.find("tbody")
            trs = body.find_all("tr", recursive=False) if body else tab.find_all("tr")[1:]
            for tr in trs[:24]:
                cells = tr.find_all(["th", "td"], recursive=False)
                if len(cells) <= pi:
                    continue
                node = cells[pi]
                print("SOURCE-LINEUP", game["id"], ti,
                      "player=", repr(node.get_text(" ", strip=False)[:95]),
                      "html=", str(node)[:340].replace("\n", " "), flush=True)
    except Exception as exc:
        print("SOURCE-LINEUP-DEBUG-ERROR", game["id"], str(exc), flush=True)


def parse_decision(soup, key):
    # A decision can be empty or not match the listed pitcher; preserve unknown,
    # not a fabricated zero or guessed pitcher W/L/S.
    s = soup.get_text(" ", strip=True)
    pat = {"win": r"\bWin:\s*(.*?)\s*\(\d+-\d+\)",
           "loss": r"\bLoss:\s*(.*?)\s*\(\d+-\d+\)",
           "save": r"\bSave:\s*(.*?)\s*\(\d+\\?\)"}[key]
    m = re.search(pat, s, re.I)
    return m.group(1).strip(" ,") if m else None


def import_one(game, official, global_keys):
    url = official.get("source_url") or official.get("source")
    if not url or not url.startswith("https://"):
        raise ValueError("No HTTPS official gamebook")
    if url.lower().split("?")[0].endswith(".pdf"):
        raise ValueError("Official PDF needs separately audited PDF line transcription")
    expected = [int(x) for x in official["official_score"]]
    official_7_inning_tie = (game["id"] == "cb-2023-02-20-nebraska-san-diego-att0181" and expected == [16, 16])
    if len(expected) != 2 or (expected[0] == expected[1] and not official_7_inning_tie):
        raise ValueError("Official game final scores missing/ambiguous")
    page = SESSION.get(url, timeout=45)
    page.raise_for_status()
    if len(page.content) < 30000:
        raise ValueError("Official source response unexpectedly short")
    soup = BeautifulSoup(page.text, "html.parser")
    line = extract_line_score(soup, expected)
    if official_7_inning_tie:
        # University official R/H/E 2/20/2023: Nebraska 16/17/1,
        # USD 16/7/3, score after exactly seven innings. No W/L/S.
        if ([x["innings"] for x in line] !=
            [[1, 3, 0, 0, 5, 2, 5], [0, 1, 0, 9, 0, 0, 6]] or
            [(x["runs"], x["hits"], x["errors"]) for x in line]
                != [(16, 17, 1), (16, 7, 3)]):
            raise ValueError("2023 Nebraska 16–16 tie: official seven-inning R/H/E checksum failed")
    short, detail, pitching = official_tables(page.text, game)
    if len(short) != 2 or len(detail) != 2 or len(pitching) != 2:
        raise ValueError("Official source missing either team's batting/pitching table")
    totals_by_side = {}
    for team, scoreboard in zip((game["away"], game["home"]), line):
        totals_by_side[team] = scoreboard
    for table in short:
        total = next((r for r in table_rows(table, table_head(table)) if r.get("_totals")), None)
        if total is None:
            raise ValueError("Batting team total missing")
        if not any((int(total["R"]), int(total["H"])) == (q["runs"], q["hits"]) for q in line):
            raise ValueError("Official boxscore R/H differs from its inning scoreboard")
    payload = dict(game, source_url=url, away_score=expected[0], home_score=expected[1],
                   away_hits=line[0]["hits"], home_hits=line[1]["hits"],
                   away_errors=line[0]["errors"], home_errors=line[1]["errors"],
                   winner=None, loser=None, save=None)
    rows, audit = scrape(payload)
    if len(rows) < 18:
        raise ValueError("Missing official individual batter/pitcher rows")
    lineups = assign_source_lineups(short, game, rows, totals_by_side)
    keys = {(x["game_id"], x["player_id"]) for x in rows}
    if len(keys) != len(rows) or keys & global_keys:
        raise ValueError("Source player-game ID collision")
    if any(sum(x["batting"]["runs"] for x in rows if x["team"] == t and "batting" in x) != totals_by_side[t]["runs"]
           or sum(x["batting"]["hits"] for x in rows if x["team"] == t and "batting" in x) != totals_by_side[t]["hits"]
           for t in (game["away"], game["home"])):
        raise ValueError("Individual source hitters do not total to official inning scoreboard")
    # Decisions must be explicitly cross-matched to source pitcher lines.
    decisions = {k: parse_decision(soup, k) for k in ("win", "loss", "save")}
    if official_7_inning_tie and any(decisions.values()):
        raise ValueError("A seven-inning 16–16 tie cannot have a pitcher winning/losing decision")
    resolved = {}
    for key, name in decisions.items():
        match = [r for r in rows if "pitching" in r and name and slug(r["player"]) == slug(name)]
        resolved[key] = name if len(match) == 1 else None
    for r in rows:
        if "pitching" in r:
            for decision, stat in (("win", "wins"), ("loss", "losses"), ("save", "saves")):
                r["pitching"][stat] = int(slug(r["player"]) == slug(resolved[decision])) if resolved[decision] else None
    # All dependent checks have passed; now and only now promote this game.
    game.update({
        "source_url": url, "verification": "official_boxscore_verified",
        "official_boxscore_status": "verified", "score_provenance": "official_boxscore",
        "away_score": expected[0], "home_score": expected[1],
        "away_hits": line[0]["hits"], "home_hits": line[1]["hits"],
        "away_errors": line[0]["errors"], "home_errors": line[1]["errors"],
        "innings": [{"inning": i + 1, "away": a, "home": h}
                    for i, (a, h) in enumerate(zip(line[0]["innings"], line[1]["innings"]))],
        "pitching_decisions": {"win": resolved["win"], "loss": resolved["loss"],
                              "save": resolved["save"]},
        "game_type": "regular_season", "postseason_round": None,
    })
    if official_7_inning_tie:
        game["official_draw"] = True
        game["official_draw_note"] = "University original seven-inning gamebook: Nebraska 16, San Diego 16; no credited W/L/S."
    if official.get("official_doubleheader_game"):
        game["game_number"] = int(official["official_doubleheader_game"])
        game["attendance_segment_confirmation_pending"] = True
    global_keys.update(keys)
    audit.update({"scoreboard": line, "lineup_audit": lineups,
                  "official_decisions": decisions, "resolved_pitcher_decisions": resolved})
    return rows, audit


def main():
    games = load("games.json")
    players = load("player_stats.json")
    report = load("import_report.json")
    if len(games) != 444 or len({g["id"] for g in games}) != 444:
        raise ValueError("Original 444 attendance games must remain intact")
    originals = {g["id"]: g for g in games}
    before = sum(g.get("verification") == "official_boxscore_verified" for g in games)
    manifest = source_manifest()
    keys = {(r["game_id"], r["player_id"]) for r in players}
    if len(keys) != len(players):
        raise ValueError("Existing verified player rows already have identity collision")
    passed, pending = [], []
    for game in sorted(games, key=lambda g: (g["date"], g["id"]), reverse=True):
        if not game["date"].startswith(TARGET_YEAR) or game.get("boxscore_backfill_excluded"):
            continue
        if game.get("verification") == "official_boxscore_verified":
            continue
        if game.get("verification") not in SUPPORTED:
            pending.append({"game_id": game["id"], "reason": "Unexpected prior status; manual review"})
            continue
        official = manifest.get(game["id"])
        if not official:
            pending.append({"game_id": game["id"], "reason": "No verified official source URL"})
            continue
        if official.get("date") != game["date"] or any(
                official.get(k) != game[k] for k in ("away", "home")):
            pending.append({"game_id": game["id"], "reason": "Source identity/date mismatch"})
            continue
        try:
            rows, audit = import_one(game, official, keys)
            players.extend(rows)
            passed.append({"game_id": game["id"], "player_rows": len(rows),
                           "source_url": game["source_url"], "audit": audit})
            print("PASS", game["id"], len(rows), flush=True)
        except Exception as exc:
            pending.append({"game_id": game["id"], "source_url": official.get("source_url"),
                            "reason": str(exc)})
            print("REVIEW", game["id"], str(exc), flush=True)
            if "batting" in str(exc) or "lineup" in str(exc):
                debug_lineup_markup(game, official.get("source_url") or official.get("source"))
    # All JUCO and prior-year records are immutable under this job.
    for gid, orig in originals.items():
        if orig.get("boxscore_backfill_excluded") or not orig["date"].startswith(TARGET_YEAR):
            assert orig is next(g for g in games if g["id"] == gid)
    players.sort(key=lambda r: (r["game_id"], r["team"], r.get("batting_slot", 99),
                               r.get("batting_sub_index", 99),
                               r.get("pitching_appearance_index", 99), r["player_id"]))
    report.update({
        "official_player_boxscores_imported": sum(g["verification"] == "official_boxscore_verified" for g in games),
        "official_score_and_inning_lines_matched": sum(g["verification"] != "attendance_only" for g in games),
        "official_scoreboard_player_lines_pending": sum(g["verification"] == "official_scoreboard_verified" for g in games),
        "attendance_only_pending_official_verification": sum(g["verification"] == "attendance_only" for g in games),
        "player_stat_rows": len(players), "unique_player_ids": len({r["player_id"] for r in players}),
        "latest_verified_batch": "2026 NCAA February/March strict source reconciling (no JUCO)",
        "remaining_official_boxscore_work": len(pending),
        "remaining_2026_eligible_noncaa_pending": len(pending),
        "warning": "2026 NCAA approved, JUCO excluded, older years and publication NOT approved. Incomplete official sources remain unverified, see audit.",
    })
    audit = {"status": "PASS" if not pending else "PARTIAL_REVIEW_REQUIRED",
             "completed_this_run": len(passed), "prior_verified": before,
             "total_verified": report["official_player_boxscores_imported"],
             "eligible_2026": 68, "original_attendance_rows": 444,
             "completed_games": passed, "pending_review": pending,
             "approval": "2026 statistical backfill only; keep draft PR; do not publish"}
    if passed:
        dump("games.json", games)
        dump("player_stats.json", players)
        dump("import_report.json", report)
    dump(FILE_AUDIT, audit)
    print(json.dumps({"completed": len(passed), "2026_total_verified": audit["total_verified"],
                      "pending": len(pending)}), flush=True)


if __name__ == "__main__":
    main()
