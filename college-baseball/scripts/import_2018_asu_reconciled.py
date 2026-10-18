#!/usr/bin/env python3
"""Strict official-source import, May 9 2018 Arizona State 12 at San Diego 7.
Uses original ASU player-table screenshots, user-reconstructed hitter strikeouts,
original scoreboard screenshot and explicitly user-confirmed substitutions.
Fails closed if any identity, total, inning, lineup or decision differs.
"""
import json
import hashlib
from pathlib import Path
from import_sidearm_pilot import slug

DATA=Path(__file__).resolve().parents[1]/"data"
GAME_ID="cb-2018-05-09-arizona-state-san-diego-att0031"
URL="https://thesundevils.com/boxscore/466"
ASU=[1,1,3,2,1,1,0,2,1]
USD=[0,0,0,0,1,0,4,0,2]
SLOTS={
"Arizona State":[
["Spencer Torkelson","Boyd Vander Kooi"],["Gage Canning"],["Carter Aldrete"],
["Lyle Lin","Luke Leisenring"],["Hunter Jump","Trevor Hauver"],
["Alika Williams"],["Hunter Bishop"],["Zach Hogueisson"],["Drew Swift"]],
"San Diego":[
["Paul Kunst"],["Jay Schuyler"],["Shane McGuire"],["Brhet Bewley"],
["Jeff Houghtby"],["Adam Kerner"],["Kevin Collard"],["Connor Doyle"],
["Trevor Rosenberg","Todd Jackson","Trevor Omahen"]]}
REPLACEMENTS={
("Arizona State","Boyd Vander Kooi","Spencer Torkelson",1),
("Arizona State","Luke Leisenring","Lyle Lin",4),
("Arizona State","Trevor Hauver","Hunter Jump",5),
("San Diego","Todd Jackson","Trevor Rosenberg",9),
("San Diego","Trevor Omahen","Todd Jackson",9)}

def check(ok,msg):
    if not ok:raise ValueError("2018 Arizona State original source: "+msg)

def outs(ip):
    i,f=map(int,str(ip).split("."))
    check(f in (0,1,2),"Invalid fractional pitching innings")
    return i*3+f

def parse(game,row,existing_keys):
    check(game["id"]==GAME_ID and game["date"]=="2018-05-09" and
          game["source_worksheet_row"]==32 and game["season"]==2018 and
          (game["away"],game["home"])==("Arizona State","San Diego") and
          row["game_id"]==GAME_ID and row["original_date"]==game["date"] and
          row["source_workbook_row"]==32 and row["official_score"]==[12,7] and
          row.get("asu_source_reconstruction_confirmed")=="2026-10-18",
          "Unconfirmed or wrong attendance game identity")
    raw=(DATA/"2018_05_09_asu_san_diego_screenshot_evidence.json").read_bytes()
    e=json.loads(raw)
    score=e["scoreboard_source"]
    confirmed=e["user_confirmed_source_lineup"]
    check(e["game_id"]==GAME_ID and e["source_game_page"]==URL and
          score["file_id"]=="file_0000000045a081f5b589dd3a9489b970" and
          score["printed_date"]=="05/09/2018" and score["inning_columns"]==9 and
          score["printed_attendance"]==658 and
          confirmed["confirmed_on"]=="2026-10-18",
          "Scoreboard image provenance or user substitution confirmation missing")
    check({(x["team"],x["substitute"],x["replaced"],x["slot"])
        for x in confirmed["user_confirmed_substitutions"]}==REPLACEMENTS and
        len(confirmed["user_confirmed_substitutions"])==5,
        "Replacement identities differ from archive owner's five confirmations")
    for side,team,innings,run,hit,error in (
        ("away","Arizona State",ASU,12,13,0),
        ("home","San Diego",USD,7,14,1)):
        src=score[side]
        check(src["team"]==team and src["innings"]==innings and
              sum(innings)==run and len(innings)==9 and
              (src["runs"],src["hits"],src["errors"])==(run,hit,error) and
              e["verified_score"][side+"_runs"]==run and
              e["verified_score"][side+"_hits"]==hit and
              confirmed["lineups"][side]==SLOTS[team],
              "Source scoreboard R/H/E, earlier batting table or nine slots differ: "+team)
    records={}
    audits=[]
    for side,team,opponent in (("away","Arizona State","San Diego"),
                              ("home","San Diego","Arizona State")):
        bat=e["batting"][side]
        pitch=e["pitching"][side]
        source_order=[p["name"] for p in bat["players"]]
        slots=SLOTS[team]
        check(len(slots)==9 and [n for slot in slots for n in slot]==source_order
              and len(set(source_order))==len(source_order),
              "Original batting table order does not fit exact nine slots: "+team)
        lineup_order={name:(i+1,j) for i,slot in enumerate(slots)
                      for j,name in enumerate(slot)}
        for item in bat["players"]:
            name=item["name"]
            key="cb-"+slug(team)+"-"+slug(name)
            check(key not in records,"Duplicate batter identity "+name)
            slot,sub=lineup_order[name]
            check(item["batter_strikeouts_status"] in (
                    "user_transcribed_from_original_play_by_play_2026_10_17",
                    "zero_derived_from_team_strikeout_checksum_and_all_positive_user_counts"),
                    "Hitter strikeouts not source reconstructed: "+name)
            records[key]={
                "game_id":GAME_ID,"player_id":key,"player":name,"team":team,
                "source_url":URL,"source_type":"asu_source_screenshots_user_confirmed_original_lineup",
                "verification":"official_boxscore_verified",
                "position":item["position"].lower(),
                "batting_slot":slot,"batting_sub_index":sub,
                "batting_appearance_index":item["source_display_order"]-1,
                "batting":{"atBats":item["ab"],"runs":item["r"],"hits":item["h"],
                           "rbi":item["rbi"],"baseOnBalls":item["bb"],
                           "strikeOuts":item["batter_strikeouts"]}}
        team_bat=[v for v in records.values() if v["team"]==team and "batting" in v]
        for source_field,stat_field in (("ab","atBats"),("r","runs"),("h","hits"),
                                         ("rbi","rbi"),("bb","baseOnBalls"),
                                         ("so","strikeOuts")):
            check(sum(v["batting"][stat_field] for v in team_bat)==bat["team_totals"][source_field],
                  team+" batting source column "+source_field)
        for field in ("doubles","triples","hr","hbp"):
            check(sum(v[field] for v in bat["players"])==bat["team_totals"][field],
                  team+" batting "+field+" checksum")
        ps=pitch["players"]
        check(len(ps)==len(set(p["name"] for p in ps)) and len(ps)>0,
              "Pitching staff empty or has duplicate players "+team)
        for idx,p in enumerate(ps):
            name=p["name"]
            key="cb-"+slug(team)+"-"+slug(name)
            if key not in records:
                records[key]={"game_id":GAME_ID,"player_id":key,"player":name,
                    "team":team,"source_url":URL,
                    "source_type":"asu_source_screenshots_user_confirmed_original_lineup",
                    "verification":"official_boxscore_verified"}
            check("pitching" not in records[key],"Duplicate pitching line")
            records[key]["pitching"]={
                "outs":outs(p["ip"]),"hits":p["h"],"runs":p["r"],
                "earnedRuns":p["er"],"baseOnBalls":p["bb"],
                "strikeOuts":p["so"],"numberOfPitches":p["np"],
                "wins":int(p["decision"]=="W"),"losses":int(p["decision"]=="L"),
                "saves":0}
            records[key]["pitching_appearance_index"]=idx
        team_pitch=[v["pitching"] for v in records.values() if v["team"]==team and "pitching" in v]
        check(sum(p["outs"] for p in team_pitch)==27,"Pitcher outs "+team)
        for srcfield,field in (("h","hits"),("r","runs"),("er","earnedRuns"),
                               ("bb","baseOnBalls"),("so","strikeOuts"),
                               ("np","numberOfPitches")):
            check(sum(p[field] for p in team_pitch)==pitch["team_totals"][srcfield],
                  team+" pitching source checksum "+field)
        oppside="home" if side=="away" else "away"
        oppbat=e["batting"][oppside]["team_totals"]
        check(sum(p["runs"] for p in team_pitch)==score[oppside]["runs"] and
              sum(p["hits"] for p in team_pitch)==score[oppside]["hits"] and
              sum(p["baseOnBalls"] for p in team_pitch)==oppbat["bb"] and
              sum(p["strikeOuts"] for p in team_pitch)==oppbat["so"],
              team+" source pitching totals disagree with "+opponent+" hitters")
        audits.append({"team":team,"nine_starting_slots":True,
            "batter_rows":len(bat["players"]),"pitcher_rows":len(ps),
            "substitutes":len(bat["players"])-9,"owner_confirmed":"2026-10-18"})
    decisions=e["pitching_decisions"]
    check(decisions["win"]=="Sam Romero" and decisions["loss"]=="Nick Sprengel"
          and decisions["save"] is None,"Original W/L/save labels conflict")
    for label,stat in (("win","wins"),("loss","losses")):
        matched=[v for v in records.values() if v.get("pitching",{}).get(stat)==1]
        check(len(matched)==1 and matched[0]["player"]==decisions[label],
              "Pitcher "+label+" decision does not match individual game line")
    check(len(records)>=18 and
          not (set((r["game_id"],r["player_id"]) for r in records.values()) & existing_keys),
          "Missing player records or player-game collisions")
    game.update({
        "verification":"official_boxscore_verified",
        "official_boxscore_status":"verified_with_user_supplied_original_scoreboard_and_lineup",
        "score_provenance":"asu_original_gamebook_and_owner_supplied_original_scoreboard",
        "source_url":URL,"away_score":12,"home_score":7,
        "away_hits":13,"home_hits":14,"away_errors":0,"home_errors":1,
        "innings":[{"inning":i+1,"away":a,"home":b}
                   for i,(a,b) in enumerate(zip(ASU,USD))],
        "pitching_decisions":{"win":"Sam Romero","loss":"Nick Sprengel","save":None},
        "source_scoreboard_file_id":score["file_id"],
        "source_substitution_confirmation_date":"2026-10-18",
        "save_note":"Original source screenshot did not report a save. No credited save inferred."})
    result=list(records.values())
    existing_keys.update((r["game_id"],r["player_id"]) for r in result)
    return result, {
        "status":"PASS","source":URL,
        "source_evidence_sha256":hashlib.sha256(raw).hexdigest(),
        "source_scoreboard_file_id":score["file_id"],
        "source_type":"official_university_batting_pitching_plus_attendee_original_lineup_and_scoreboard",
        "player_rows":len(result),"lineup_audit":audits,
        "scoreboard":score,"pitching_decisions":game["pitching_decisions"],
        "save_provenance":"not_explicitly_labeled_in_source",
        "attendee_confirmed_substitutions":confirmed["user_confirmed_substitutions"]}
