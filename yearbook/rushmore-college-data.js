/* College Baseball Courtside Archive. Source-scoped data; no mixing MLB career lines. */
(()=>{
"use strict";
const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date=v=>{if(!v)return "Date not recorded";const d=new Date(v+"T12:00:00");return Number.isNaN(+d)?v:d.toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})};
const fmt=n=>n==null?"—":Number(n).toLocaleString("en-US",{maximumFractionDigits:2});
const stat=v=>v===null||v===undefined||v===""?null:Number.isFinite(Number(v))?Number(v):null;
const link=(s)=>{try{let u=new URL(s);return ["https:","http:"].includes(u.protocol)?u.href:null}catch{return null}};
const gameUrl=g=>"./game.html?id="+encodeURIComponent(g.id);
const playerUrl=p=>"./player.html?id="+encodeURIComponent(p.player_id);
// Preserve original source IDs and source-scoped validation; canonicalize school labels only after source matching.
const canonicalSchool=s=>s==="Cal State Northrdige"?"Cal State Northridge":s;
const unique=a=>[...new Set(a.filter(x=>x!=null&&x!==""))];
// Several official gamebooks print surnames (or entire lineups) in capitals.
// Correct only their presentation; player IDs, source names and stat lines stay intact.
const caseSensitiveSurnames={MACCALLUM:"MacCallum",DEANNA:"DeAnna"};
const preservedUpperNameParts=new Set(["II","III","IV","JR","AJ","BJ","CJ","DJ","JD","JJ","JP","JT","KJ","LJ","ND","PJ","RJ","TJ","TK","CC"]);
const scorebookNeedsCase=name=>/[A-Z]{3,}/.test(String(name||""))&&String(name).split(/[^A-Za-z]+/).some(part=>
 part.length>=3&&/^[A-Z]+$/.test(part)&&!preservedUpperNameParts.has(part) || /^Mc[A-Z]{3,}$/.test(part));
function scorebookNameCase(name){
 return String(name||"").replace(/[A-Za-z]+/g,word=>{
  if(preservedUpperNameParts.has(word))return word;
  if(caseSensitiveSurnames[word])return caseSensitiveSurnames[word];
  if(/^Mc[A-Z]{2,}$/.test(word))return "Mc"+word[2]+word.slice(3).toLowerCase();
  if(!/^[A-Z]{2,}$/.test(word))return word;
  if(word.startsWith("MC")&&word.length>2)return "Mc"+word[2]+word.slice(3).toLowerCase();
  return word[0]+word.slice(1).toLowerCase();
 });
}
function preferredScorebookNameCases(rows){
 const known=new Map();
 const score=name=>(/[a-z][A-Z]/.test(name)?10:0)+(/['’][A-Z]/.test(name)?4:0)+(/\b(?:AJ|BJ|CJ|DJ|JD|JJ|JP|JT|KJ|LJ|PJ|RJ|TJ|TK)\b/.test(name)?2:0);
 for(const row of rows){
  const name=row.player;
  if(typeof name!=="string"||scorebookNeedsCase(name))continue;
  const key=name.toLowerCase(),old=known.get(key);
  if(!old||score(name)>score(old))known.set(key,name);
 }
 return known;
}
function nav(active){
 const links=[["index.html","Overview","home"],["game.html","Games","games"],["stats.html","Players","players"],["transfers.html","Transfers","transfers"],["cws.html","College World Series","cws"],["best-pitching-matchups.html","Pitching Matchups","best-pitching"],["coaches.html","Coaches","coaches"],["records.html","Records","records"],["mlb-alumni.html","To the MLB","mlb-alumni"]];
 return '<header class="archive-header"><a class="archive-logo" href="./index.html">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · COLLEGE BASEBALL</small></a>'
 +'<nav class="archive-nav" aria-label="College Baseball archive navigation">'+links.map(([href,label,name])=>'<a href="./'+href+'"'+(active===name||active==="player"&&name==="players"?' aria-current="page"':'')+'>'+label+'</a>').join("")
 +'<a href="../index.html" class="back-link">All sports ↗</a></nav></header>'
 +'<form id="cb-quick-search" class="cb-quick-search" role="search" aria-label="Search college baseball archive">'
 +'<label for="cb-quick-input">Search this archive</label><div class="cb-quick-field">'
 +'<input id="cb-quick-input" type="search" autocomplete="off" placeholder="Find players, teams or games…" aria-controls="cb-quick-results" aria-expanded="false">'
 +'<div id="cb-quick-results" class="cb-quick-results" role="region" aria-label="College baseball search matches" hidden></div>'
 +'</div><button type="submit">Search</button></form>';
}
async function json(name,fallback){const r=await fetch("../college-baseball/data/"+name,{cache:"no-store"});if(!r.ok)throw Error("Missing "+name+" ("+r.status+")");return r.json()}
function applyAttendanceGameCorrections(sourceGames,sourceRows,manifest){
 if(!manifest||!Array.isArray(manifest.games))throw Error("Missing verified attendance game corrections");
 const games=sourceGames.slice(),removed=new Set(),added=[],gameRedirects=new Map();
 const slug=s=>String(s).normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
 const battingKeys=["atBats","runs","hits","rbi","baseOnBalls","strikeOuts"];
 const battingEventKeys=["doubles","triples","homeRuns","stolenBases","caughtStealing","hitByPitch","sacBunts","sacFlies"];
 const pitchingKeys=["outs","hits","runs","earnedRuns","baseOnBalls","strikeOuts","battersFaced","numberOfPitches"];
 const pitchingEventKeys=["hitBatsmen","wildPitches","balks"];
 const total=(rows,category,key)=>rows.reduce((n,r)=>n+(r[category]?.[key]||0),0);
 for(const correction of manifest.games){
  const oldId=correction.replaces_game_id,newId=correction.game?.id;
  if(!oldId||!newId||removed.has(oldId)||games.some(g=>g.id===newId)||sourceRows.some(r=>r.game_id===newId))throw Error("Invalid attendance game replacement: "+oldId);
  const index=games.findIndex(g=>g.id===oldId),old=games[index];
  if(index<0||!old||!sourceRows.some(r=>r.game_id===oldId)||!correction.source_url)throw Error("Missing original attendance game: "+oldId);
  if(!correction.game.date||!Array.isArray(correction.game.innings)||Object.keys(correction.batting||{}).length!==2||Object.keys(correction.pitching||{}).length!==2)throw Error("Incomplete corrected box score: "+newId);
  const game={...old,...correction.game,source_url:correction.source_url,source_type:correction.source_type||"official_university_pdf_scorebook",notes:old.notes+" "+correction.verification_note};
  const teams=[game.away,game.home],participants=new Map(),battingNames=new Set(),pitchingNames=new Set();
  const makeRow=(team,player)=>({game_id:newId,player_id:"cb-"+slug(team)+"-"+slug(player),player,team,source_url:correction.source_url,source_type:correction.source_type||"official_university_pdf_scorebook",verification:"official_boxscore_verified"});
  const key=(team,player)=>team+"\u0000"+player;
  for(const team of teams){
   const lineup=correction.batting[team],pitchers=correction.pitching[team];
   if(!Array.isArray(lineup)||!Array.isArray(pitchers)||!lineup.length||!pitchers.length)throw Error("Missing corrected team lineup: "+team);
   const slotCounts=new Map();let previousSlot=0;
   for(const [appearance,line] of lineup.entries()){
    if(!Array.isArray(line)||line.length!==9)throw Error("Invalid corrected batter row: "+team);
    const [slot,player,position,...numbers]=line;
    if(!Number.isInteger(slot)||slot<1||slot>9||slot<previousSlot||!player||!position||numbers.some(n=>!Number.isInteger(n)||n<0)||battingNames.has(player))throw Error("Invalid corrected batting order: "+player);
    previousSlot=slot;battingNames.add(player);
    const extras=correction.batting_events?.[player]||{};
    if(Object.keys(extras).some(k=>!battingEventKeys.includes(k))||Object.values(extras).some(n=>!Number.isInteger(n)||n<0))throw Error("Invalid corrected batting event: "+player);
    const batting=Object.fromEntries(battingKeys.map((k,i)=>[k,numbers[i]]));
    for(const k of battingEventKeys)batting[k]=extras[k]??0;
    if(batting.doubles+batting.triples+batting.homeRuns>batting.hits)throw Error("Extra-base hits exceed hits: "+player);
    const r={...makeRow(team,player),position,batting_slot:slot,batting_sub_index:slotCounts.get(slot)||0,batting_appearance_index:appearance,batting};
    slotCounts.set(slot,(slotCounts.get(slot)||0)+1);participants.set(key(team,player),r);
   }
   if(slotCounts.size!==9)throw Error("Corrected batting order has fewer than nine slots: "+team);
   for(const [appearance,line] of pitchers.entries()){
    if(!Array.isArray(line)||line.length!==9)throw Error("Invalid corrected pitcher row: "+team);
    const [player,...numbers]=line;
    if(!player||numbers.some(n=>!Number.isInteger(n)||n<0)||pitchingNames.has(player))throw Error("Invalid corrected pitcher: "+player);
    pitchingNames.add(player);
    const extras=correction.pitching_events?.[player]||{};
    if(Object.keys(extras).some(k=>!pitchingEventKeys.includes(k))||Object.values(extras).some(n=>!Number.isInteger(n)||n<0))throw Error("Invalid corrected pitching event: "+player);
    const pitching=Object.fromEntries(pitchingKeys.map((k,i)=>[k,numbers[i]]));
    for(const k of pitchingEventKeys)pitching[k]=extras[k]??0;
    pitching.wins=Number(game.pitching_decisions?.win===player);
    pitching.losses=Number(game.pitching_decisions?.loss===player);
    pitching.saves=Number(game.pitching_decisions?.save===player);
    const id=key(team,player),prior=participants.get(id)||makeRow(team,player);
    participants.set(id,{...prior,position:prior.position||"p",pitching,pitching_appearance_index:appearance});
   }
   const expected=correction.expected?.[team];
   const teamRows=[...participants.values()].filter(r=>r.team===team),batters=teamRows.filter(r=>r.batting),arms=teamRows.filter(r=>r.pitching);
   const checks={batting_rows:batters.length,pitching_rows:arms.length,atBats:total(batters,"batting","atBats"),runs:total(batters,"batting","runs"),hits:total(batters,"batting","hits"),rbi:total(batters,"batting","rbi"),walks:total(batters,"batting","baseOnBalls"),strikeouts:total(batters,"batting","strikeOuts"),plateAppearances:batters.reduce((n,r)=>n+["atBats","baseOnBalls","hitByPitch","sacBunts","sacFlies"].reduce((v,k)=>v+r.batting[k],0),0),pitching_outs:total(arms,"pitching","outs"),battersFaced:total(arms,"pitching","battersFaced")};
   if(!expected||Object.entries(checks).some(([k,v])=>expected[k]!==v))throw Error("Official corrected totals do not reconcile: "+team);
   if(checks.runs!==Number(team===game.away?game.away_score:game.home_score))throw Error("Corrected batting score mismatch: "+team);
  }
  if(Object.keys(correction.batting_events||{}).some(name=>!battingNames.has(name))||Object.keys(correction.pitching_events||{}).some(name=>!pitchingNames.has(name)))throw Error("Unmatched corrected box-score event");
  if(correction.expected[game.away].plateAppearances!==correction.expected[game.home].battersFaced||correction.expected[game.home].plateAppearances!==correction.expected[game.away].battersFaced)throw Error("Corrected PA does not match opponent BF");
  if([game.away,game.home].some(team=>total([...participants.values()].filter(r=>r.team===team&&r.pitching),"pitching","runs")!==Number(team===game.away?game.home_score:game.away_score)))throw Error("Corrected pitching runs do not match opponent score");
  games[index]=game;removed.add(oldId);gameRedirects.set(oldId,newId);added.push(...participants.values());
 }
 return {games,rows:[...sourceRows.filter(r=>!removed.has(r.game_id)),...added],gameRedirects};
}
function applyStatBackfills(sourceRows,manifest){
 if(!manifest||!Array.isArray(manifest.games))throw Error("Missing verified college game stat backfills");
 const patches=new Map(),seenGames=new Set();
 for(const game of manifest.games){
  if(!game.game_id||seenGames.has(game.game_id))throw Error("Invalid or repeated stat backfill game");
  seenGames.add(game.game_id);
  const participants=sourceRows.filter(r=>r.game_id===game.game_id);
  const batting=participants.filter(r=>r.batting),pitching=participants.filter(r=>r.pitching);
  if(batting.length!==game.expected_batting_rows||pitching.length!==game.expected_pitching_rows)throw Error("Stat backfill row count mismatch: "+game.game_id);
  const batIds=new Set(batting.map(r=>r.player_id)),pitchIds=new Set(pitching.map(r=>r.player_id));
  if(batIds.size!==batting.length||pitchIds.size!==pitching.length)throw Error("Ambiguous stat backfill player ID");
  const categories=[["hit_by_pitch",batIds],["sac_bunts",batIds],["sac_flies",batIds],["catcher_interference",batIds],["batters_faced",pitchIds]];
  for(const [key,ids] of categories){
   if(key==="catcher_interference"&&game[key]==null)continue;
   if(!game[key]||typeof game[key]!=="object")throw Error("Missing stat backfill category: "+key);
   for(const [id,n] of Object.entries(game[key]))if(!ids.has(id)||!Number.isInteger(n)||n<0)throw Error("Invalid stat backfill entry: "+id);
  }
  // Optional, single-game official scoring-summary backfill. An omitted
  // player in these complete maps had zero extra-base hits in that game.
  const extra=game.extra_base_hits;
  if(extra){
   const fields=["doubles","triples","home_runs"];
   if(Object.keys(extra).length!==fields.length||fields.some(k=>!extra[k]||typeof extra[k]!=="object"||Array.isArray(extra[k])))throw Error("Incomplete extra-base-hit gamebook backfill");
   for(const key of fields)for(const [id,n] of Object.entries(extra[key]))
    if(!batIds.has(id)||!Number.isInteger(n)||n<0)throw Error("Invalid source-scoped extra-base hit: "+id);
  }
  if(Object.keys(game.batters_faced).length!==pitching.length)throw Error("Incomplete pitcher BF backfill");
  const teamPA=new Map(),teamBF=new Map();
  for(const r of batting){
   const id=r.player_id,b=r.batting;
   const values={hitByPitch:game.hit_by_pitch[id]??0,sacBunts:game.sac_bunts[id]??0,sacFlies:game.sac_flies[id]??0,catcherInterference:game.catcher_interference?.[id]??0,
    ...(extra?{doubles:extra.doubles[id]??0,triples:extra.triples[id]??0,homeRuns:extra.home_runs[id]??0}:{})};
   for(const [key,n] of Object.entries(values))if(b[key]!=null&&b[key]!==n)throw Error("Stat backfill disagrees with existing batting data: "+id);
   if(extra&&(stat(b.hits)==null||values.doubles+values.triples+values.homeRuns>stat(b.hits)))throw Error("Extra-base-hit backfill exceeds verified hits: "+id);
   if(stat(b.atBats)==null||stat(b.baseOnBalls)==null)throw Error("Missing AB or BB in stat backfill: "+id);
   const pa=stat(b.atBats)+stat(b.baseOnBalls)+values.hitByPitch+values.sacBunts+values.sacFlies+values.catcherInterference;
   teamPA.set(r.team,(teamPA.get(r.team)||0)+pa);
   const rowKey=[r.game_id,r.team,id].join("\u0000");
   patches.set(rowKey,{...(patches.get(rowKey)||{}),batting:values});
  }
  for(const r of pitching){
   const bf=game.batters_faced[r.player_id];
   if(r.pitching.battersFaced!=null&&r.pitching.battersFaced!==bf)throw Error("Stat backfill disagrees with existing BF: "+r.player_id);
   teamBF.set(r.team,(teamBF.get(r.team)||0)+bf);
   const rowKey=[r.game_id,r.team,r.player_id].join("\u0000");
   patches.set(rowKey,{...(patches.get(rowKey)||{}),pitching:{battersFaced:bf}});
  }
  const teams=[...teamPA.keys()];
  if(teams.length!==2||teamBF.size!==2||teamPA.get(teams[0])!==teamBF.get(teams[1])||teamPA.get(teams[1])!==teamBF.get(teams[0]))throw Error("Stat backfill PA does not reconcile with opponent BF: "+game.game_id);
 }
 return sourceRows.map(r=>{
  const fix=patches.get([r.game_id,r.team,r.player_id].join("\u0000"));
  return fix?{...r,...(fix.batting?{batting:{...r.batting,...fix.batting}}:{}),...(fix.pitching?{pitching:{...r.pitching,...fix.pitching}}:{})}:r;
 });
}
async function load(){
 const [rawGames,rawRows,report,crosswalk,identity,nameCorrections,statBackfills,gameCorrections,recapRegistry]=await Promise.all([json("games.json"),json("player_stats.json"),json("import_report.json"),json("mlb_crosswalk.json"),json("player_identity_crosswalk.json"),json("player_name_corrections.json"),json("source_stat_backfills.json"),json("attendance_game_corrections.json"),json("game_recaps.json")]);
 const {games:sourceGames,rows:correctedRows,gameRedirects}=applyAttendanceGameCorrections(rawGames,rawRows,gameCorrections);
 const sourceRows=applyStatBackfills(correctedRows,statBackfills);
 if(!identity||!Array.isArray(identity.merges))throw Error("Missing verified player identity merge manifest");
 // Keep the original SDSU corrections and allow additional, strictly scoped games.
 const nameCorrectionGames=[nameCorrections,...(nameCorrections?.games||[])];
 if(nameCorrectionGames.some(g=>!g||!Array.isArray(g.corrections)||!g.game_id||!g.team))throw Error("Missing verified game-specific player name corrections");
 // Preserve official source rows: scoped corrections restore names and link
 // known person profiles without rewriting any original box-score statistics.
 const fixedNames=new Map();
 for(const game of nameCorrectionGames){
  for(const fix of game.corrections){
   if(!fix.source_player_id||!fix.source_player_name||!fix.canonical_player_id||!fix.player)throw Error("Incomplete verified player name correction");
   const key=[game.game_id,game.team,fix.source_player_id].join("\u0000");
   if(fixedNames.has(key))throw Error("Duplicate player name correction: "+key);
   fixedNames.set(key,fix);
  }
 }
 // Apply source-scoped team+player ID aliases in browser memory, never to
 // the preserved original gamebook rows. Existing game team attribution stays intact.
 const scopedAliases=new Map(),redirects=new Map();
 for(const m of identity.merges){
  if(!m.canonical_id||!Array.isArray(m.pairs)||!Array.isArray(m.source_player_ids))throw Error("Malformed transfer identity crosswalk");
  for(const pair of m.pairs){
   const key=pair.team+"\u0000"+pair.source_player_id;
   if(scopedAliases.has(key)&&scopedAliases.get(key)!==m.canonical_id)throw Error("Conflicting transfer identity aliases");
   scopedAliases.set(key,m.canonical_id);
  }
  for(const sourceId of m.source_player_ids){
   if(redirects.has(sourceId)&&redirects.get(sourceId)!==m.canonical_id)throw Error("Conflicting transfer deep-link redirects");
   redirects.set(sourceId,m.canonical_id);
  }
 }
 for(const fix of nameCorrectionGames.flatMap(g=>g.corrections)){
  if(redirects.has(fix.source_player_id)&&redirects.get(fix.source_player_id)!==fix.canonical_player_id)throw Error("Conflicting name correction profile redirect");
  redirects.set(fix.source_player_id,fix.canonical_player_id);
 }
 const mergedRowDisplayNames=new Map(identity.merges.filter(m=>m.display_name).map(m=>[m.canonical_id,m.display_name]));
 const knownNameCases=preferredScorebookNameCases(sourceRows);
 const appliedFixes=new Set();
 const matchedRows=sourceRows.map(source=>{
  const key=[source.game_id,source.team,source.player_id].join("\u0000");
  const fix=fixedNames.get(key);
  if(fix&&source.player!==fix.source_player_name)throw Error("Player name correction source mismatch: "+key);
  if(fix)appliedFixes.add(key);
  const r=fix?{...source,player:fix.player,player_id:fix.canonical_player_id,
   original_game_player_id:source.player_id,original_game_player_name:source.player}:source;
  const displayName=scorebookNeedsCase(r.player)?knownNameCases.get(r.player.toLowerCase())||scorebookNameCase(r.player):r.player;
  const displayed=displayName===r.player?r:{...r,player:displayName};
  const unified=scopedAliases.get(displayed.team+"\u0000"+displayed.player_id);
  return unified?{...displayed,original_school_player_id:displayed.player_id,player_id:unified,
   player:mergedRowDisplayNames.get(unified)||displayed.player}:displayed;
 });
 if(appliedFixes.size!==fixedNames.size)throw Error("Verified player name correction did not match source game rows");
 // The February 21, 2023 source typo is not a separate program. Keep game IDs, source player IDs and statistics unchanged.
 const rows=matchedRows.map(r=>canonicalSchool(r.team)===r.team?r:{...r,team:canonicalSchool(r.team)});
 const games=sourceGames.map(g=>canonicalSchool(g.away)===g.away&&canonicalSchool(g.home)===g.home?g:{...g,away:canonicalSchool(g.away),home:canonicalSchool(g.home)});
 if(!Array.isArray(games)||!Array.isArray(rows)||!Array.isArray(crosswalk))throw Error("Unexpected college baseball data structure");
 const gameMap=new Map(games.map(g=>[g.id,g]));
 if(gameMap.size!==games.length)throw Error("Duplicate college baseball game IDs");
 if(rows.some(r=>!gameMap.has(r.game_id)))throw Error("Unmatched player-stat game ID");
 const byPlayer=new Map();
 for(const r of rows){
  const id=String(r.player_id||"");
  if(!id)continue;
  let p=byPlayer.get(id);
  if(!p){p={player_id:id,name:r.player||"Player",teams:new Set(),games:new Set(),rows:[]};byPlayer.set(id,p)}
  if(r.team)p.teams.add(r.team);
  p.games.add(r.game_id);
  p.rows.push(r);
 }
 // Optional owner-approved display name for abbreviated source lineups;
 // raw scorebook names, school attribution, and original IDs stay untouched.
 const displayNames=new Map(identity.merges.filter(m=>m.display_name).map(m=>[m.canonical_id,m.display_name]));
 const formerNames=new Map();
 for(const alias of identity.display_aliases||[]){
  if(!alias.player_id||!alias.display_name||!Array.isArray(alias.former_names)||!alias.former_names.length||
     !byPlayer.has(alias.player_id)||displayNames.has(alias.player_id))
   throw Error("Invalid verified player display alias: "+alias.player_id);
  displayNames.set(alias.player_id,alias.display_name);
  formerNames.set(alias.player_id,alias.former_names);
 }
 // A gamebook's misspelled school is one school, not a second college stint.
 // Normalize only the profile/leaderboard label, leaving sourced game rows intact.
 const displayTeams=new Map(nameCorrectionGames.filter(g=>g.team_display_name).map(g=>[g.team,g.team_display_name]));
 const players=[...byPlayer.values()].map(p=>({...p,name:displayNames.get(p.player_id)||p.name,former_names:formerNames.get(p.player_id)||[],
  teams:[...new Set([...p.teams].map(team=>displayTeams.get(team)||team))],games:[...p.games]}));
 const playerIds=new Set(rows.map(r=>String(r.player_id||"")));
 // Recaps are optional editorial content, not a prerequisite for loading the archive.
 // A stale player ID must never blank the overview, search or unrelated game pages.
 const recaps=new Map();
 if(recapRegistry?.version===1&&recapRegistry.recaps&&typeof recapRegistry.recaps==="object"&&!Array.isArray(recapRegistry.recaps)){
  for(const [gameId,entry] of Object.entries(recapRegistry.recaps)){
   if(!gameMap.has(gameId)||!entry||!Array.isArray(entry.paragraphs)||entry.paragraphs.length!==3||entry.paragraphs.some(p=>typeof p!=="string"||!p.trim())){
    console.warn("Skipping malformed college baseball recap:",gameId);
    continue;
   }
   const pog=entry.player_of_game;
   const pogId=redirects.get(String(pog?.player_id||""))||String(pog?.player_id||"");
   if(!pog||!playerIds.has(pogId)||!pog.name||!pog.team||!pog.line){
    console.warn("Skipping recap with invalid Player of Game:",gameId);
    continue;
   }
   // Preserve the recap narrative, but show an unlinked name if a historical
   // player ID is no longer valid after an identity/name reconciliation.
   const paragraphs=entry.paragraphs.map(paragraph=>paragraph.replace(/\[\[([a-z0-9-]+)\|([^\]\|]+)\]\]/g,(token,id,label)=>{
    const canonical=redirects.get(id)||id;
    if(!playerIds.has(canonical)){
     console.warn("Rendering unlinked recap player:",gameId,id);
     return label;
    }
    return "[["+canonical+"|"+label+"]]";
   }));
   recaps.set(gameId,{...entry,paragraphs,player_of_game:{...pog,player_id:pogId}});
  }
 }else console.warn("College baseball recaps unavailable; core archive will still load");
 return {games:games.slice().sort((a,b)=>b.date.localeCompare(a.date)||a.id.localeCompare(b.id)),rows,players,gameMap,gameRedirects,report,crosswalk,identity,redirects,recaps};
}
let cachedArchivePromise;
function cachedLoad(){return cachedArchivePromise||(cachedArchivePromise=load())}
function sum(rows,category,key){
 const values=rows.map(r=>stat(r[category]?.[key])).filter(v=>v!=null);
 return values.length?values.reduce((a,b)=>a+b,0):null;
}
function bat(rows){
 const ab=sum(rows,"batting","atBats"),h=sum(rows,"batting","hits"),d=sum(rows,"batting","doubles"),t=sum(rows,"batting","triples"),hr=sum(rows,"batting","homeRuns");
 const bb=sum(rows,"batting","baseOnBalls"),hbp=sum(rows,"batting","hitByPitch"),sf=sum(rows,"batting","sacFlies");
 const appearances=rows.filter(r=>r.batting!=null);
 const pa=appearances.length&&appearances.every(r=>["atBats","baseOnBalls","hitByPitch","sacFlies","sacBunts"].every(k=>stat(r.batting[k])!=null))
  ?appearances.reduce((total,r)=>total+["atBats","baseOnBalls","hitByPitch","sacFlies","sacBunts"].reduce((n,k)=>n+Number(r.batting[k]),0)+(stat(r.batting.catcherInterference)??0),0):null;
 const singles=h!=null&&d!=null&&t!=null&&hr!=null?h-d-t-hr:null;
 const tb=singles==null?null:singles+2*d+3*t+4*hr;
 const obDen=ab!=null&&bb!=null&&hbp!=null&&sf!=null?ab+bb+hbp+sf:null;
 return {games:new Set(appearances.map(r=>r.game_id)).size,plateAppearances:pa,atBats:ab,hits:h,runs:sum(rows,"batting","runs"),doubles:d,triples:t,homeRuns:hr,rbi:sum(rows,"batting","rbi"),
   walks:bb,strikeouts:sum(rows,"batting","strikeOuts"),stolenBases:sum(rows,"batting","stolenBases"),
  walkPct:pa>0&&bb!=null?100*bb/pa:null,strikeoutPct:pa>0?100*sum(rows,"batting","strikeOuts")/pa:null,
   average:ab>0&&h!=null?h/ab:null,
   obp:obDen>0&&h!=null?(h+bb+hbp)/obDen:null,
   slg:ab>0&&tb!=null?tb/ab:null,
   ops:obDen>0&&ab>0&&tb!=null&&h!=null?(h+bb+hbp)/obDen+tb/ab:null};
}
function pitch(rows){
 const outs=sum(rows,"pitching","outs"),earnedRuns=sum(rows,"pitching","earnedRuns"),h=sum(rows,"pitching","hits"),walks=sum(rows,"pitching","baseOnBalls");
 const appearances=rows.filter(r=>r.pitching!=null);
 // A zero-based pitching appearance index identifies the starting pitcher.
 const starts=new Set(appearances.filter(r=>r.pitching_appearance_index===0).map(r=>r.game_id)).size;
 const battersFaced=appearances.length&&appearances.every(r=>stat(r.pitching.battersFaced)!=null)?sum(rows,"pitching","battersFaced"):null;
 return {games:new Set(appearances.map(r=>r.game_id)).size,starts,battersFaced,outs,innings:outs==null?null:Math.floor(outs/3)+"."+(outs%3),strikeouts:sum(rows,"pitching","strikeOuts"),
  hits:h,walks,earnedRuns,era:outs>0&&earnedRuns!=null?27*earnedRuns/outs:null,
  whip:outs>0&&h!=null&&walks!=null?3*(h+walks)/outs:null,
  walkPct:battersFaced>0&&walks!=null?100*walks/battersFaced:null,
  strikeoutPct:battersFaced>0?100*sum(rows,"pitching","strikeOuts")/battersFaced:null,
  wins:sum(rows,"pitching","wins"),losses:sum(rows,"pitching","losses"),saves:sum(rows,"pitching","saves")};
}
window.CARushmoreCollegeData={load:cachedLoad};
})();
