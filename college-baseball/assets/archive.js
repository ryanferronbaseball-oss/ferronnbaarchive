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
 const links=[["index.html","Overview","home"],["game.html","Games","games"],["stats.html","Players","players"],["transfers.html","Transfers","transfers"],["coaches.html","Coaches","coaches"],["records.html","Records","records"],["mlb-alumni.html","To the MLB","mlb-alumni"]];
 return '<header class="archive-header"><a class="archive-logo" href="./index.html">COURTSIDE ARCHIVE<small>EVERY GAME HAS A STORY · COLLEGE BASEBALL</small></a>'
 +'<nav class="archive-nav" aria-label="College Baseball archive navigation">'+links.map(([href,label,name])=>'<a href="./'+href+'"'+(active===name||active==="player"&&name==="players"?' aria-current="page"':'')+'>'+label+'</a>').join("")
 +'<a href="../index.html" class="back-link">All sports ↗</a></nav></header>'
 +'<form id="cb-quick-search" class="cb-quick-search" role="search" aria-label="Search college baseball archive">'
 +'<label for="cb-quick-input">Search this archive</label><div class="cb-quick-field">'
 +'<input id="cb-quick-input" type="search" autocomplete="off" placeholder="Find players, teams or games…" aria-controls="cb-quick-results" aria-expanded="false">'
 +'<div id="cb-quick-results" class="cb-quick-results" role="region" aria-label="College baseball search matches" hidden></div>'
 +'</div><button type="submit">Search</button></form>';
}
async function json(name,fallback){const r=await fetch("./data/"+name,{cache:"no-store"});if(!r.ok)throw Error("Missing "+name+" ("+r.status+")");return r.json()}
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
 const [rawGames,rawRows,report,crosswalk,identity,nameCorrections,statBackfills,gameCorrections]=await Promise.all([json("games.json"),json("player_stats.json"),json("import_report.json"),json("mlb_crosswalk.json"),json("player_identity_crosswalk.json"),json("player_name_corrections.json"),json("source_stat_backfills.json"),json("attendance_game_corrections.json")]);
 const {games,rows:correctedRows,gameRedirects}=applyAttendanceGameCorrections(rawGames,rawRows,gameCorrections);
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
 const knownNameCases=preferredScorebookNameCases(sourceRows);
 const appliedFixes=new Set();
 const rows=sourceRows.map(source=>{
  const key=[source.game_id,source.team,source.player_id].join("\u0000");
  const fix=fixedNames.get(key);
  if(fix&&source.player!==fix.source_player_name)throw Error("Player name correction source mismatch: "+key);
  if(fix)appliedFixes.add(key);
  const r=fix?{...source,player:fix.player,player_id:fix.canonical_player_id,
   original_game_player_id:source.player_id,original_game_player_name:source.player}:source;
  const displayName=scorebookNeedsCase(r.player)?knownNameCases.get(r.player.toLowerCase())||scorebookNameCase(r.player):r.player;
  const displayed=displayName===r.player?r:{...r,player:displayName};
  const unified=scopedAliases.get(displayed.team+"\u0000"+displayed.player_id);
  return unified?{...displayed,original_school_player_id:displayed.player_id,player_id:unified}:displayed;
 });
 if(appliedFixes.size!==fixedNames.size)throw Error("Verified player name correction did not match source game rows");
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
 // A gamebook's misspelled school is one school, not a second college stint.
 // Normalize only the profile/leaderboard label, leaving sourced game rows intact.
 const displayTeams=new Map(nameCorrectionGames.filter(g=>g.team_display_name).map(g=>[g.team,g.team_display_name]));
 const players=[...byPlayer.values()].map(p=>({...p,name:displayNames.get(p.player_id)||p.name,
  teams:[...new Set([...p.teams].map(team=>displayTeams.get(team)||team))],games:[...p.games]}));
 return {games:games.slice().sort((a,b)=>b.date.localeCompare(a.date)||a.id.localeCompare(b.id)),rows,players,gameMap,gameRedirects,report,crosswalk,identity,redirects};
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
const rate=(v,n)=>v==null?"—":Number(v).toFixed(n).replace(n===3?/^0(?=\.)/:/$^/,"");
function metrics(items){return '<div class="metrics">'+items.map(([name,val])=>'<div class="metric"><strong>'+esc(val==null?"—":String(val))+'</strong><small>'+esc(name)+'</small></div>').join("")+'</div>'}
function pending(message){return '<div class="cb-empty">'+esc(message)+'</div>'}
function score(g){return g.away_score==null||g.home_score==null?"Score pending":fmt(g.away_score)+" – "+fmt(g.home_score)}
function gameLabel(g){return g.away+" @ "+g.home}
function sourceLabel(g){return g.verification==="official_boxscore_verified"?"Official player box score verified":g.verification==="official_scoreboard_verified"?"Official score & innings verified · player stats pending":g.away_score!=null?"Score from attendance list · source check pending":"Attendance logged · box score pending"}
function gameName(g){return '<a href="'+gameUrl(g)+'">'+esc(date(g.date))+" · "+esc(gameLabel(g))+'</a>'}
function gameCard(g){
 return '<article class="game-card cb-game-card"><div class="game-date">'+esc(date(g.date))
 +(g.regional_game_number?' · Regional Game '+g.regional_game_number:g.game_number?' · Game '+g.game_number:'')+'</div>'
 +'<h3>'+gameName(g)+'</h3><div class="game-score">'+esc(score(g))+'</div>'
 +'<div class="game-date">'+esc(g.ballpark||"Ballpark not recorded")+'</div>'
 +'<span class="mlb-pill '+(g.verification==="official_boxscore_verified"?"verified":"pending")+'">'+esc(sourceLabel(g))+'</span>'
 +'<a class="action-link secondary" href="'+gameUrl(g)+'">View game ↗</a></article>';
}
function htmlTable(columns,rows,whenEmpty="No verified player statistics yet"){
 return '<div class="table-wrap cb-table-wrap"><table class="cb-table"><thead><tr>'+columns.map(s=>'<th scope="col">'+esc(s)+'</th>').join("")+'</tr></thead><tbody>'
 +(rows.length?rows.join(""):'<tr><td colspan="'+columns.length+'">'+esc(whenEmpty)+'</td></tr>')+'</tbody></table></div>';
}
function chart(items){
 const max=Math.max(1,...items.map(x=>x[1]));
 return '<div class="cb-bars">'+items.map(([k,v])=>'<div class="cb-bar"><span class="cb-bar-label">'+esc(k)+'</span><span class="cb-track"><span class="cb-fill" style="display:block;width:'+(100*v/max).toFixed(1)+'%"></span></span><strong>'+fmt(v)+'</strong></div>').join("")+'</div>';
}
function counts(items){
 const m=new Map();for(const i of items)if(i)m.set(i,(m.get(i)||0)+1);
 return [...m.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
}
function gameSearch(g,q){return [g.date,g.away,g.home,g.ballpark,g.city,g.state,g.postseason_round].some(x=>String(x||"").toLowerCase().includes(q))}
function initQuickSearch(d){
 const form=$("cb-quick-search"),input=$("cb-quick-input"),results=$("cb-quick-results");
 if(!form||!input||!results)return;
 const key=s=>String(s||"").normalize("NFKD").replace(/[\u0300-\u036f]/g,"").toLowerCase();
 const programs=unique(d.games.flatMap(g=>[g.away,g.home])).sort((a,b)=>a.localeCompare(b));
 const players=d.players.map(p=>({...p,searchName:key(p.name),searchSchools:key(p.teams.join(" "))}));
 const games=d.games.map(g=>({game:g,searchText:key([g.date,date(g.date),g.away,g.home,g.ballpark,g.city,g.state,g.postseason_round].join(" "))}));
 let visible=[];
 const hide=()=>{results.hidden=true;input.setAttribute("aria-expanded","false")};
 function draw(){
  const q=key(input.value.trim());
  if(q.length<2){visible=[];hide();return}
  const schoolMatches=programs.filter(name=>key(name).includes(q)).slice(0,3).map(name=>({kind:"Team",title:name,detail:"Browse attended games",href:"./game.html?q="+encodeURIComponent(name)}));
  const playerMatches=players.filter(p=>p.searchName.includes(q)||p.searchSchools.includes(q))
   .sort((a,b)=>Number(b.searchName===q)-Number(a.searchName===q)||Number(b.searchName.startsWith(q))-Number(a.searchName.startsWith(q))||a.name.localeCompare(b.name))
   .slice(0,5).map(p=>({kind:"Player",title:p.name,detail:p.teams.join(" / "),href:playerUrl(p)}));
  const gameMatches=games.filter(g=>g.searchText.includes(q)).slice(0,4).map(({game:g})=>({kind:"Game",title:date(g.date)+" · "+gameLabel(g),detail:g.ballpark||"Attended college game",href:gameUrl(g)}));
  visible=[...schoolMatches,...playerMatches,...gameMatches];
  results.innerHTML=visible.length?visible.map(item=>'<a class="cb-quick-result" href="'+esc(item.href)+'">'
   +'<span><strong>'+esc(item.title)+'</strong><small>'+esc(item.detail)+'</small></span><em>'+esc(item.kind)+'</em></a>').join("")
   :'<p class="cb-quick-empty">No matching players, teams or attended games.</p>';
  results.hidden=false;input.setAttribute("aria-expanded","true");
 }
 input.addEventListener("input",draw);
 input.addEventListener("focus",draw);
 input.addEventListener("keydown",event=>{
  if(event.key==="Escape")hide();
  if(event.key==="ArrowDown"&&!results.hidden){const first=results.querySelector("a");if(first){event.preventDefault();first.focus()}}
 });
 form.addEventListener("submit",event=>{event.preventDefault();if(visible.length)window.location.href=visible[0].href;else input.focus()});
 document.addEventListener("pointerdown",event=>{if(!form.contains(event.target))hide()});
 if(input.value.trim())draw();
}
function renderHome(d){
 const seasons=unique(d.games.map(g=>g.season));const teams=counts(d.games.flatMap(g=>[g.home,g.away]));const parks=counts(d.games.map(g=>g.ballpark));
 $("app").innerHTML='<div class="cb-intro"><div class="eyebrow">College Baseball · Attendance history</div><h1>Your college baseball history.</h1><p class="lead">Every college game you attended—box scores, the players you witnessed, historic performances, ballparks, and the eventual road to professional baseball.</p></div>'
 +'<div class="cb-note"><strong>Independent college archive:</strong> College batting and pitching totals stay separate from MLB and Minor League Baseball. Player profiles can connect across levels only when their identity is verified.</div>'
 +metrics([["Games logged",d.games.length],["Seasons",seasons.length],["Schools seen",teams.length],["Ballparks logged",parks.length]])
 +(d.games.length?
 '<div class="cb-chart-grid"><section class="panel"><h2>Most-watched programs</h2>'+chart(teams.slice(0,8))+'</section><section class="panel"><h2>Ballpark history</h2>'+(parks.length?chart(parks.slice(0,8)):pending("Ballpark details await import."))+'</section></div>'
 +'<div class="section-heading"><h2>Recently attended games</h2><a href="./game.html" class="action-link secondary">Explore all games ↗</a></div><div class="game-grid cb-grid">'+d.games.slice(0,6).map(gameCard).join("")+'</div>'
 :pending("Ready for your first college baseball attendance list. No games have been added or invented. The import template accepts dates, teams, ballparks, tournament rounds, and doubleheader game numbers."))
 +'<div class="section-heading"><h2>Build your college baseball archive</h2></div><div class="game-grid cb-grid">'
 +'<div class="game-card cb-game-card"><h3>Games & box scores</h3><p class="cb-sub">Inning-by-inning results, lineups, batting, pitching, scoring details and pitching decisions when official sources are verified.</p><a href="./game.html" class="cb-link">View games ↗</a></div>'
 +'<div class="game-card cb-game-card"><h3>Players & leaderboards</h3><p class="cb-sub">Every player you watched, with witnessed-game career lines and hitter/pitcher summaries, including two-way players.</p><a href="./stats.html" class="cb-link">View players ↗</a></div>'
 +'<div class="game-card cb-game-card"><h3>Signature performances</h3><p class="cb-sub">Best single-game hitting and pitching performances, records, and tournament milestones; no fabricated data.</p><a href="./records.html" class="cb-link">View records ↗</a></div></div>';
}
async function renderGames(d){
 const alumniRegistry=await json("mlb_alumni_seed.json");
 const gamePhotos=await json("game_photos.json").catch(()=>({}));
 const mlbIds=new Set((alumniRegistry.players||[]).filter(p=>p.mlb_debut).map(p=>p.college_player_id));
 $("app").innerHTML='<div class="eyebrow">College Baseball · Games & box scores</div><h1>Game details.</h1>'
 +'<p class="lead">Scores, inning lines and authentic batting and pitching box scores from college games you attended, where documented in official scorebooks.</p>'
 +'<div class="toolbar"><label class="filter-label" for="cb-game-select">Attended game</label><select id="cb-game-select">'
 +'<option value="">Select an attended game</option>'+d.games.map(g=>'<option value="'+esc(g.id)+'">'+esc(date(g.date)+" · "+gameLabel(g)+(g.away_score!=null?" · "+g.away_score+"–"+g.home_score:" · Pending"))+'</option>').join("")+'</select></div>'
 +'<section id="cb-game-details" aria-live="polite"></section>'
 +'<div class="section-heading"><h2>All attended games</h2></div><div class="toolbar">'
 +'<input id="cb-game-search" type="search" aria-label="Search dates teams and parks" placeholder="Search teams, dates, venue or tournament…">'
 +'<label class="filter-label" for="cb-season-filter">Season</label><select id="cb-season-filter" aria-label="Season filter"><option value="">All seasons</option>'
 +unique(d.games.map(g=>g.season)).sort((a,b)=>b-a).map(y=>'<option>'+y+'</option>').join("")+'</select></div><div id="cb-game-list"></div>';
 const params=new URLSearchParams(location.search),chosen=params.get("id"),picker=$("cb-game-select");
 if(params.get("q"))$("cb-game-search").value=params.get("q");
 const selected=d.gameRedirects.get(chosen)||chosen;
 if(selected&&d.gameMap.has(selected))picker.value=selected;
 function showGame(){
  const g=d.gameMap.get(picker.value);
  if(!g){$("cb-game-details").innerHTML=pending(d.games.length?"Select a game to open its official scoreboard and player box score.":"No college baseball games imported yet.");return}
  const source=link(g.source_url),players=d.rows.filter(x=>x.game_id===g.id);
  const pros=new Map(players.filter(p=>mlbIds.has(p.player_id)).map(p=>[p.player_id,p.player]));
  const proSection='<section class="game-pro-alumni"><h2>Future MLB players in this game · '+pros.size+'</h2>'
   +'<p class="pro-caption">Verified MLB debuts · Click a name to open the college player profile.</p>'
   +(pros.size?'<div class="game-pro-list">'+[...pros].sort((a,b)=>a[1].localeCompare(b[1])).map(([id,name])=>'<a href="./player.html?id='+encodeURIComponent(id)+'">'+esc(scorebookNameCase(name))+' ↗</a>').join("")+'</div>':'<p class="pro-empty">No verified MLB alumni currently matched to this game’s recorded players.</p>')+'</section>';
  const actual=g.away_score!=null&&g.home_score!=null;
  const scoreContent=actual?g.away_score+" – "+g.home_score:"—";
  const decision=g.pitching_decisions;
  const person=name=>{
   if(!name)return '<span class="mlb-decision-unavailable">No save</span>';
   const p=players.find(x=>x.pitching&&(x.player===name||x.original_game_player_name===name||x.player.toLowerCase()===String(name).toLowerCase()));
   return p?'<a class="mlb-decision-name" href="'+playerUrl(p)+'">'+esc(p.player)+'</a>'
    :'<span class="mlb-decision-unavailable">'+esc(scorebookNameCase(name))+'</span>';
  };
  const decisions=decision?'<section class="panel mlb-decisions-panel" id="cb-pitching-decisions">'
   +'<div class="mlb-pregame-eyebrow">OFFICIAL COLLEGE GAME DECISIONS</div><h2>Win, Loss & Save</h2>'
   +'<div class="mlb-decision-grid">'
   +[["WIN","Winner","win"],["LOSS","Loser","loss"],["SAVE","Save","save"]].map(([heading,label,key])=>
    '<div class="mlb-decision-card" data-decision="'+key+'"><span class="mlb-decision-type">'+heading+'</span>'
    +'<div class="mlb-decision-role">'+label+'</div>'+person(decision[key]|| (key==="win"?decision.winner:key==="loss"?decision.loser:null))+'</div>').join("")
   +'</div><p class="mlb-note">Official win/loss/save credits from the original gamebook, not a custom performance award.</p></section>':"";
  const box=players.length?'<div class="mlb-nav-tabs" role="tablist" aria-label="College baseball box score category">'
   +'<button type="button" role="tab" aria-selected="true" data-cat="batting">Batting</button>'
   +'<button type="button" role="tab" aria-selected="false" data-cat="pitching">Pitching</button></div>'
   +'<section class="panel" id="cb-boxscore-panel"><h2 id="cb-stat-title">Batting box score</h2><div id="cb-box"></div></section>'
   :pending("Official college player box score not yet imported for this game. No batting or pitching lines have been fabricated.");
  const photo=typeof gamePhotos[g.id]==="string"&&/^\.\/assets\/game-photos\/[a-zA-Z0-9._-]+$/.test(gamePhotos[g.id])
   ?'<div class="cb-game-photo"><img src="'+esc(gamePhotos[g.id])+'" alt="'+esc(gameLabel(g)+' game photo')+'" loading="lazy"></div>':"";
  $("cb-game-details").innerHTML='<section class="cb-game-summary">'
   +'<div class="mlb-score" aria-label="'+esc(gameLabel(g)+", final score "+scoreContent)+'">'
   +'<div class="side">'+esc(g.away)+'</div><div class="final">'+esc(scoreContent)+'</div><div class="side">'+esc(g.home)+'</div></div>'
   +'<p class="mlb-note">'+esc(date(g.date))+' · '+esc(gameLabel(g))+' · '+esc(g.ballpark||"Ballpark pending")
   +(g.city?" · "+esc(g.city):"")+(g.state?", "+esc(g.state):"")
   +(g.regional_game_number?" · Regional Game "+esc(g.regional_game_number):"")
   +(g.game_number?" · Doubleheader Game "+esc(g.game_number):"")
   +(g.postseason_round?" · "+esc(g.postseason_round):"")+'</p>'
   +'<span class="mlb-pill '+(g.verification==="official_boxscore_verified"?"verified":"pending")+'">'+esc(sourceLabel(g))+'</span>'
   +(source?'<p class="mlb-note"><a href="'+esc(source)+'" target="_blank" rel="noopener noreferrer">Official college gamebook ↗</a></p>':"")
   +'</section>'
   +photo
   +proSection
   +(Array.isArray(g.innings)&&g.innings.length?renderInnings(g):"")
   +decisions+box;
  if(!players.length)return;
  const tabs=$("cb-game-details").querySelectorAll("[data-cat]");
  const showCategory=category=>{
   tabs.forEach(b=>b.setAttribute("aria-selected",String(b.dataset.cat===category)));
   $("cb-stat-title").textContent=(category==="batting"?"Batting":"Pitching")+" box score";
   $("cb-box").innerHTML=renderBox(g,players,category);
  };
  tabs.forEach(b=>b.addEventListener("click",()=>showCategory(b.dataset.cat)));
  showCategory("batting");
 }
 picker.addEventListener("change",()=>{
  if(picker.value)history.replaceState(null,"","?id="+encodeURIComponent(picker.value));
  else history.replaceState(null,"",location.pathname);
  showGame();
 });
 function draw(){
  const q=$("cb-game-search").value.trim().toLowerCase(),year=$("cb-season-filter").value;
  const list=d.games.filter(g=>(!year||String(g.season)===year)&&gameSearch(g,q));
  $("cb-game-list").innerHTML=list.length?htmlTable(["Date","Matchup","Score","Ballpark","Verification"],list.map(g=>'<tr><td><a href="'+gameUrl(g)+'">'+esc(date(g.date))+'</a></td><td>'+esc(gameLabel(g))+'</td><td>'+esc(score(g))+'</td><td>'+esc(g.ballpark||"—")+'</td><td>'+esc(sourceLabel(g))+'</td></tr>'))
  :pending("No matching attended games. Import your college baseball list or adjust the filters.");
 }
 $("cb-game-search").addEventListener("input",draw);
 $("cb-season-filter").addEventListener("change",draw);
 draw();showGame();
}
function renderInnings(g){
 const list=g.innings;
 const line=(team,label,total)=>'<tr><td>'+esc(label)+'</td>'+list.map(x=>'<td>'+esc(x[team]==null?"—":x[team])+'</td>').join("")+'<td><strong>'+esc(total==null?"—":total)+'</strong></td></tr>';
 return '<section class="panel"><h2>Line score by inning</h2>'
 +'<div class="table-wrap"><table class="mlb-innings"><thead><tr><th>Club</th>'
 +list.map((x,i)=>'<th>'+esc(x.inning??i+1)+'</th>').join("")+'<th>R</th></tr></thead>'
 +'<tbody>'+line("away",g.away,g.away_score)+line("home",g.home,g.home_score)+'</tbody></table></div></section>';
}
function renderBox(g,rows,category){
 const batting=category==="batting",fields=batting
 ?[["atBats","AB"],["runs","R"],["hits","H"],["doubles","2B"],["triples","3B"],["homeRuns","HR"],["rbi","RBI"],["baseOnBalls","BB"],["strikeOuts","SO"]]
 :[["outs","IP"],["hits","H"],["earnedRuns","ER"],["baseOnBalls","BB"],["strikeOuts","SO"],["numberOfPitches","Pitches"]];
 return '<div class="cb-boxscore">'+[["away",g.away],["home",g.home]].map(([side,team])=>{
  const members=rows.filter(r=>r.team===team&&r[category]!=null).slice().sort((a,b)=>batting
   ?(a.batting_slot??999)-(b.batting_slot??999)||(a.batting_sub_index??999)-(b.batting_sub_index??999)||(a.batting_appearance_index??999)-(b.batting_appearance_index??999)
   :(a.pitching_appearance_index??999)-(b.pitching_appearance_index??999)||a.player.localeCompare(b.player));
  const numbered=members.map(r=>{
   const sub=batting&&r.batting_sub_index!=null&&r.batting_sub_index>0;
   const spot=batting?(r.batting_slot??"—"):null;
   const number=batting?(spot==="—"?"—":sub?"↳":String(spot))
    :r.pitching_appearance_index==null?"—":String(r.pitching_appearance_index+1);
   const position=r.position||"",subtitle=batting?position+(sub?" · entered batting slot "+spot:""):"";
   const cells=fields.map(([key])=>{
    const value=stat(r[category]?.[key]);
    const output=key==="outs"&&value!=null?Math.floor(value/3)+"."+(value%3):value==null?"—":fmt(value);
    return '<td>'+esc(output)+'</td>';
   }).join("");
   return '<tr class="mlb-lineup-row'+(sub?" mlb-substitute":"")+'" data-player-id="'+esc(r.player_id)+'"'
    +(batting?' data-slot="'+esc(spot)+'" data-sub="'+(r.batting_sub_index??"")+'"':' data-pitcher-index="'+(r.pitching_appearance_index??"")+'"')+'>'
    +'<td class="mlb-order" data-order="'+esc(number)+'">'+esc(number)+'</td>'
    +'<td class="cb-player-cell"><a href="'+playerUrl(r)+'">'+esc(r.player||"Unknown player")+'</a>'
    +(subtitle?'<small>'+esc(subtitle)+'</small>':"")+'</td>'
    +cells+'</tr>';
  }).join("");
  const note=batting?"Official batting order · ↳ denotes a replacement in that lineup spot"
   :"Official pitching appearance order · #1 starting pitcher, followed by relievers";
  return '<section class="mlb-team-box" data-side="'+side+'" data-category="'+category+'">'
   +'<div class="mlb-team-heading"><h3>'+esc(team)+'</h3><span>'+side.toUpperCase()+'</span></div>'
   +'<p class="mlb-team-caption">'+note+'</p>'
   +'<div class="table-wrap cb-boxscore-table"><table class="mlb-sticky cb-roster-table"><thead><tr>'
   +'<th scope="col">Order</th><th scope="col">Player</th>'+fields.map(([,key])=>'<th scope="col">'+esc(key)+'</th>').join("")+'</tr></thead>'
   +'<tbody>'+(numbered||'<tr><td colspan="'+(fields.length+2)+'">No verified '+esc(category)+' statistics available.</td></tr>')+'</tbody></table></div></section>';
 }).join("")+'</div>';
}
function renderPlayers(d){
 $("app").innerHTML='<div class="eyebrow">College Baseball · Witnessed players</div><h1>Players & leaderboards</h1><p class="lead">College box-score statistics only. When players reach professional baseball, their college lines will remain independent and can connect to separate verified MLB profiles.</p>'
 +'<div class="mlb-filters cb-player-filters"><label for="cb-player-search">Find a player<input id="cb-player-search" type="search" placeholder="Search player or college…" aria-label="Player name or school"></label>'
 +'<label for="cb-role">Statistical group<select id="cb-role" aria-label="Player role"><option value="hit">Batting</option><option value="pitch">Pitching</option></select></label>'
 +'<label for="cb-sort">Sort leaderboard<select id="cb-sort" aria-label="Sort statistical leaderboard"></select></label></div>'
 +'<section class="panel cb-leaderboard-panel"><h2>Player leaderboard</h2><p id="cb-board-note" class="mlb-note"></p><div id="cb-player-board"></div></section>';
 const hitColumns=[["games","Games"],["plateAppearances","PA"],["atBats","AB"],["runs","R"],["hits","H"],["doubles","2B"],["triples","3B"],["homeRuns","HR"],["rbi","RBI"],["walks","BB"],["strikeouts","K"],["average","BA"],["obp","OBP"],["slg","SLG"],["ops","OPS"],["walkPct","BB%"],["strikeoutPct","K%"]];
 const pitchColumns=[["games","Games"],["starts","GS"],["innings","IP"],["battersFaced","BF"],["hits","H"],["earnedRuns","ER"],["walks","BB"],["strikeouts","K"],["era","ERA"],["whip","WHIP"],["walkPct","BB%"],["strikeoutPct","K%"]];
 const roles={hit:hitColumns,pitch:pitchColumns};
 let role="hit";
 function options(){const sel=$("cb-sort");sel.innerHTML=roles[role].map(([key,label])=>'<option value="'+key+'">'+label+'</option>').join("");sel.value=role==="hit"?"hits":"strikeouts"}
 function draw(){
  const field=$("cb-sort").value,q=$("cb-player-search").value.trim().toLowerCase();
  const rows=d.players.map(p=>({...p,stats:role==="hit"?bat(p.rows):pitch(p.rows)}))
  .filter(p=>p.name.toLowerCase().includes(q)||p.teams.join(" ").toLowerCase().includes(q))
  .filter(p=>p.stats[field]!=null)
  .sort((a,b)=>(["era","whip"].includes(field)?a.stats[field]-b.stats[field]:b.stats[field]-a.stats[field])||a.name.localeCompare(b.name)).slice(0,200);
  $("cb-board-note").textContent="Statistics cover only games attended. A dash means the source data cannot establish that total; pitching BF, BB% and K% require verified batters-faced data. Click the sort menu to rank by any column.";
  if(!d.players.length){$("cb-player-board").innerHTML=pending("No college player box scores have been imported yet. This leaderboard will populate as official college gamebooks are verified.");return}
  const columns=roles[role];
  const cols=["Player / school",...columns.map(([,label])=>label)];
  const body=rows.map(p=>{
   const s=p.stats;
   const vals=columns.map(([key])=>{
    const v=s[key];if(v==null)return "—";
    if(["average","obp","slg","ops"].includes(key))return rate(v,3);
    if(["era","whip"].includes(key))return rate(v,2);
    if(["walkPct","strikeoutPct"].includes(key))return v.toFixed(1)+"%";
    return key==="innings"?v:fmt(v);
   });
   return '<tr><td><a href="'+playerUrl(p)+'">'+esc(p.name)+'</a><div class="cb-card-meta">'+esc(p.teams.join(" / "))+'</div></td>'+vals.map(x=>'<td>'+esc(x)+'</td>').join("")+'</tr>';
  });
  $("cb-player-board").innerHTML=htmlTable(cols,body,"No players have recorded statistics in this category.");
 }
 $("cb-role").addEventListener("change",()=>{role=$("cb-role").value;options();draw()});
 $("cb-sort").addEventListener("change",draw);$("cb-player-search").addEventListener("input",draw);
 options();draw();
}
async function renderPlayer(d){
 const requestedId=new URLSearchParams(location.search).get("id");
  const id=d.redirects.get(requestedId)||requestedId;
  const p=d.players.find(x=>String(x.player_id)===id);
 if(!p){$("app").innerHTML='<div class="eyebrow">College Baseball · Player profile</div><h1>Player profile</h1>'+pending("No verified college baseball player profile is available for this ID. Players appear after official gamebook imports.");return}
 const [alumniRegistry,draftRegistry,nationalAwardsRegistry,baseballAmericaRegistry,championshipRegistry,conferenceAwardsRegistry,allConferenceRegistry,verifiedConferenceLinks]=await Promise.all([json("mlb_alumni_seed.json"),json("draft_profile_tags.json"),json("national_award_profile_tags.json"),json("baseball_america_all_american_tags.json"),json("college_world_series_recognitions.json"),json("conference_award_profile_tags.json"),json("all_conference_profile_tags.json"),json("all_conference_verified_links_2026_11_05.json")]);
 const milbLinks=await fetch("../milb/data/college_links.json",{cache:"no-store"})
   .then(async res=>res.ok?res.json():[])
   .catch(error=>{console.warn("College to MiLB identity links unavailable",error);return []});
 const matchedMiLB=Array.isArray(milbLinks)?milbLinks.find(x=>x.verified===true&&x.college_player_id===id):null;
 const championships=(championshipRegistry.champions||[]).filter(c=>(c.verified_archive_player_ids||[]).includes(id));
 const cwsAllTournament=(championshipRegistry.all_tournament_team||[]).filter(a=>a.college_player_id===id);
 const cwsMops=(championshipRegistry.most_outstanding_players||[]).filter(a=>a.college_player_id===id);
 const nationalAwards=(nationalAwardsRegistry.awards||[]).filter(a=>a.college_player_id===id);
 const conferenceAwards=(conferenceAwardsRegistry.awards||[]).filter(a=>a.college_player_id===id);
 const conferenceAwardKey=a=>[a.conference,a.year,a.team,a.name,a.school].join("|");
 const uniqueConferenceAwards=new Map();
 for(const award of [...(allConferenceRegistry.selections||[]),...(verifiedConferenceLinks.selections||[])])if(award.college_player_id===id)uniqueConferenceAwards.set(conferenceAwardKey(award),award);
 const allConference=[...uniqueConferenceAwards.values()].sort((a,b)=>b.year-a.year||a.team.localeCompare(b.team));
 const baseballAmericaHonors=(baseballAmericaRegistry.honors||[]).filter(a=>a.college_player_id===id);
 if(!Array.isArray(alumniRegistry.players))throw Error("Invalid verified MLB alumni registry");
 if(!Array.isArray(draftRegistry.picks))throw Error("Missing verified college draft tags");
 const draftIds=new Set();
 for(const entry of draftRegistry.picks){
  if(!entry.college_player_id||!entry.name||!Number.isInteger(entry.draft_year)||
     !String(entry.draft_round||"").trim()||!Number.isInteger(entry.draft_pick)||!entry.draft_team||
     draftIds.has(entry.college_player_id)||d.players.some(x=>x.player_id===entry.college_player_id&&x.name.toLowerCase()!==entry.name.toLowerCase()))
   throw Error("Invalid or unmatched verified draft selection: "+entry.college_player_id);
  draftIds.add(entry.college_player_id);
 }
 const alumnus=alumniRegistry.players.find(x=>x.college_player_id===id&&Number.isInteger(x.mlb_player_id)&&x.mlb_debut);
 const newDraft=draftRegistry.picks.find(x=>x.college_player_id===id);
 if(newDraft&&alumnus&&["draft_year","draft_round","draft_pick","draft_team"].some(k=>String(newDraft[k])!==String(alumnus[k])))
  throw Error("Conflicting MLB draft history for "+p.name);
 const draft=newDraft||alumnus;
 const draftTag=draft&&draft.draft_pick!=null
  ?`${draft.draft_year} – Round ${draft.draft_round} – Pick ${draft.draft_pick} – ${draft.draft_team}`:"";
 const b=bat(p.rows),pi=pitch(p.rows),qualifiedHit=p.rows.some(x=>x.batting!=null),qualifiedPitch=p.rows.some(x=>x.pitching!=null);
 const teamLogoIds=await json("team_logo_ids.json").catch(()=>({}));
 const normTeam=s=>String(s||"").toLowerCase().replace(/[^a-z0-9]/g,"");
 const logoIds=new Map(Object.entries(teamLogoIds).map(([name,teamId])=>[normTeam(name),teamId]));
 const witnessedSchools=p.teams.length>1?[...new Set(p.rows.map(r=>r.team))].map(name=>{
  const rows=p.rows.filter(r=>r.team===name),first=rows.reduce((earliest,r)=>{
   const day=d.gameMap.get(r.game_id)?.date||"9999-99-99";return day<earliest?day:earliest;
  },"9999-99-99");
  return {name,first,rows,b:bat(rows),pi:pitch(rows)};
 }).sort((a,b)=>a.first.localeCompare(b.first)||a.name.localeCompare(b.name)):[];
 const transferSection=witnessedSchools.length>1?'<section class="panel cb-transfer-profile"><h2>Seen at Multiple Schools</h2>'
  +'<p class="mlb-note">Only schools where you personally watched this player. Statistics include only those attended college games.</p>'
  +'<div class="cb-transfer-path">'+witnessedSchools.map((s,i)=>{
   const logoId=logoIds.get(normTeam(s.name));return (i?'<span class="cb-transfer-arrow" aria-hidden="true">→</span>':'')
    +'<div class="cb-transfer-school">'+(logoId?'<img src="https://a.espncdn.com/i/teamlogos/ncaa/500/'+encodeURIComponent(logoId)+'.png" alt="'+esc(s.name)+' logo" loading="lazy">':'')
    +'<span><strong>'+esc(s.name)+'</strong><small>First seen '+esc(s.first.slice(0,4))+'</small></span></div>';
  }).join('')+'</div>'
  +(witnessedSchools.some(s=>s.b.games)?'<h3>Hitting</h3>'+htmlTable(["School","Games","AVG","HR","RBI"],witnessedSchools.filter(s=>s.b.games).map(s=>'<tr><td>'+esc(s.name)+'</td><td>'+s.b.games+'</td><td>'+rate(s.b.average,3)+'</td><td>'+fmt(s.b.homeRuns)+'</td><td>'+fmt(s.b.rbi)+'</td></tr>')):'')
  +(witnessedSchools.some(s=>s.pi.games)?'<h3>Pitching</h3>'+htmlTable(["School","Games","IP","ERA","K"],witnessedSchools.filter(s=>s.pi.games).map(s=>'<tr><td>'+esc(s.name)+'</td><td>'+s.pi.games+'</td><td>'+esc(s.pi.innings??'—')+'</td><td>'+rate(s.pi.era,2)+'</td><td>'+fmt(s.pi.strikeouts)+'</td></tr>')):'')
  +'<p class="mlb-note"><a href="./transfers.html">Explore the college baseball Transfers page →</a></p></section>':'';
 const cross=d.crosswalk.find(x=>x.verified===true&&String(x.college_player_id)===id);
 const tripleLevel=Boolean(cross&&matchedMiLB&&String(cross.mlb_player_id)===String(matchedMiLB.milb_id));
 const entries=unique(p.rows.map(x=>x.game_id)).map(game_id=>d.gameMap.get(game_id)).filter(Boolean).sort((a,b)=>b.date.localeCompare(a.date)||b.id.localeCompare(a.id));
 const logRows=p.rows.slice().sort((a,b)=>(d.gameMap.get(b.game_id)?.date||"").localeCompare(d.gameMap.get(a.game_id)?.date||"")||b.game_id.localeCompare(a.game_id));
 const initials=p.name.split(/\s+/).map(x=>x[0]).slice(0,2).join("").toUpperCase();
 const roleStats=(label,groups)=>'<section class="cb-profile-role"><h2>'+esc(label)+'</h2><div class="cb-profile-stat-rows">'
  +groups.map(items=>'<div class="cb-profile-stat-row" style="--cb-columns:'+items.length+'">'
   +items.map(([title,value])=>'<div class="metric mlb-profile-stat"><small>'+esc(title)+'</small><strong>'+esc(value==null?"—":value)+'</strong></div>').join("")
   +'</div>').join("")+'</div></section>';
 const percent=v=>v==null?"—":v.toFixed(1)+"%";
 const hitter=qualifiedHit?roleStats("Hitting in games you attended",[
  [["Games",b.games],["Plate Appearances",fmt(b.plateAppearances)],["At Bats",fmt(b.atBats)],["Runs",fmt(b.runs)],["Hits",fmt(b.hits)]],
  [["Doubles",fmt(b.doubles)],["Triples",fmt(b.triples)],["Home Runs",fmt(b.homeRuns)],["RBI",fmt(b.rbi)],["Walks",fmt(b.walks)],["Strikeouts",fmt(b.strikeouts)]],
  [["BA",rate(b.average,3)],["OBP",rate(b.obp,3)],["SLG",rate(b.slg,3)],["OPS",rate(b.ops,3)],["BB%",percent(b.walkPct)],["K%",percent(b.strikeoutPct)]]
 ]):"";
 const pitcher=qualifiedPitch?roleStats("Pitching in games you attended",[
  [["Games",pi.games],["Games Started",pi.starts],["Innings",pi.innings],["Batters Faced",fmt(pi.battersFaced)]],
  [["Hits Allowed",fmt(pi.hits)],["Earned Runs",fmt(pi.earnedRuns)],["Walks",fmt(pi.walks)],["Strikeouts",fmt(pi.strikeouts)]],
  [["ERA",rate(pi.era,2)],["WHIP",rate(pi.whip,2)],["BB%",percent(pi.walkPct)],["K%",percent(pi.strikeoutPct)]]
 ]):"";
 $("app").innerHTML='<div class="eyebrow">College Baseball · Player profile</div>'
 +'<section class="mlb-profile-hero mlb-profile-head cb-profile-hero">'
 +'<div class="mlb-profile-photo cb-profile-initials" aria-hidden="true">'+esc(initials)+'</div>'
 +'<div class="mlb-profile-identity"><div class="mlb-profile-team-name">'+esc(p.teams.join(" / "))+'</div>'
 +'<h1>'+esc(p.name)+'</h1>'
 +(alumnus||draftTag||cross||matchedMiLB||nationalAwards.length||conferenceAwards.length||allConference.length||baseballAmericaHonors.length||championships.length||cwsAllTournament.length||cwsMops.length?'<div class="mlb-profile-achievements">'
  +(alumnus?'<a class="mlb-profile-badge cb-mlb-alumnus" href="https://www.mlb.com/player/'+encodeURIComponent(alumnus.mlb_player_id)+'" target="_blank" rel="noopener noreferrer" title="Verified MLB debut: '+esc(date(alumnus.mlb_debut))+'">★ MLB ALUMNUS ↗</a>':"")
  +(draftTag?'<span class="mlb-profile-badge cb-mlb-draft" title="MLB draft year, round, overall pick and drafting team">'+esc(draftTag)+'</span>':"")
  +(cross?'<a class="mlb-profile-badge cb-dual-level" href="../mlb/player.html?id='+encodeURIComponent(cross.mlb_player_id)+'" title="You attended this player’s college and MLB games">★ SEEN IN COLLEGE + MLB ↗</a>':"")
  +(tripleLevel?'<a class="mlb-profile-badge cb-triple-level" href="../milb/player.html?id='+encodeURIComponent(matchedMiLB.milb_id)+'" title="You attended this player’s college, minor-league and MLB games">★ SEEN IN COLLEGE + MiLB + MLB ↗</a>':"")
  +(matchedMiLB?'<a class="mlb-profile-badge cb-dual-level" href="../milb/player.html?id='+encodeURIComponent(matchedMiLB.milb_id)+'" title="You attended this player’s college and minor-league baseball games">★ SEEN IN COLLEGE + MiLB ↗</a>':"")
  +championships.map(c=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(c.school+' · '+c.year+' NCAA Division I national champions · Verified championship roster')+'">🏆 '+esc(c.year+' NATIONAL CHAMPION')+'</span>').join('')
  +cwsMops.map(a=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(a.school+' · '+a.year+' College World Series Most Outstanding Player')+'">🏆 '+esc(a.year+' CWS MOST OUTSTANDING PLAYER')+'</span>').join('')
  +cwsAllTournament.map(a=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(a.school+' · '+a.year+' College World Series All-Tournament Team')+'">★ '+esc(a.year+' CWS ALL-TOURNAMENT TEAM')+'</span>').join('')
  +nationalAwards.map(a=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(a.school+' · '+a.year)+'">★ '+esc(a.year+' '+a.award)+'</span>').join('')
  +conferenceAwards.map(a=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(a.school+' · '+a.year+' '+a.conference+' '+a.award)+'">★ '+esc(a.year+' '+a.conference+' '+a.award)+'</span>').join('')
  +allConference.map(a=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(a.school+' · '+a.year+' '+a.conference+' '+a.team+' All-Conference')+'">★ '+esc(a.year+' All-'+a.conference+' '+a.team)+'</span>').join('')
  +baseballAmericaHonors.map(a=>'<span class="mlb-profile-badge cb-national-award" title="'+esc(a.school+' · '+a.position)+'">★ '+esc(a.year+' Baseball America '+a.team+' All-American')+'</span>').join('')+'</div>':"")
 +'<p class="mlb-profile-seen">'+p.games.length+' game'+(p.games.length===1?"":"s")+' witnessed · College baseball</p>'
 +'</div></section>'
 +'<p class="mlb-note">Only college baseball appearances from games you attended appear here; professional seasons are never added to college totals.</p>'
 +transferSection+hitter+pitcher
 +'<div class="section-heading"><h2>Last 3 games witnessed</h2></div><div class="game-grid cb-grid cb-profile-games">'+entries.slice(0,3).map(gameCard).join("")+'</div>'
 +'<section class="panel cb-player-game-log"><h2>Recorded college game logs</h2>'
 +htmlTable(["Date","Matchup","AB","R (hitting)","H","HR","RBI","IP","H (allowed)","R (pitching)","BB","K"],logRows.map(r=>{
  const g=d.gameMap.get(r.game_id);
  return '<tr><td><a href="'+gameUrl(g)+'">'+esc(date(g.date))+'</a></td><td>'+esc(gameLabel(g))+'</td>'
  +[stat(r.batting?.atBats),stat(r.batting?.runs),stat(r.batting?.hits),stat(r.batting?.homeRuns),stat(r.batting?.rbi),r.pitching?.outs!=null?Math.floor(r.pitching.outs/3)+"."+(r.pitching.outs%3):null,stat(r.pitching?.hits),stat(r.pitching?.runs),stat(r.pitching?.baseOnBalls),stat(r.pitching?.strikeOuts)].map(x=>'<td>'+esc(x==null?"—":x)+'</td>').join("")+'</tr>';
 }))+'</section>';
}
function renderRecords(d){
 const defs=[["Hits","batting","hits"],["Home runs","batting","homeRuns"],["RBI","batting","rbi"],["Strikeouts","pitching","strikeOuts"],["Outs pitched","pitching","outs"],["Stolen bases","batting","stolenBases"]];
 $("app").innerHTML='<div class="eyebrow">College Baseball · Historical records</div><h1>Signature Performances</h1><p class="lead">Best single-game performances you witnessed, drawn strictly from imported and source-verified college box scores.</p>'
 +'<p class="mlb-note">The top witnessed performance is not necessarily a season or school record. We never infer missing stats from incomplete scorebooks.</p>'
 +(d.rows.length?'<div class="mlb-records-grid cb-grid cb-records-grid">'+defs.map(([label,category,key])=>{
  const list=d.rows.map(r=>({r,val:stat(r[category]?.[key])})).filter(x=>x.val!=null&&d.gameMap.has(x.r.game_id));
  list.sort((a,b)=>b.val-a.val||a.r.player.localeCompare(b.r.player));
  if(!list.length)return '<article class="mlb-record cb-record"><small>'+esc(label)+'</small><strong>—</strong><p>Not available in verified gamebooks</p></article>';
  const best=list[0],g=d.gameMap.get(best.r.game_id);
  return '<article class="mlb-record cb-record"><small>'+esc(label+' · single game')+'</small><strong>'+esc(key==="outs"?Math.floor(best.val/3)+"."+(best.val%3)+" IP":fmt(best.val))+'</strong><p><a href="'+playerUrl(best.r)+'" class="cb-link">'+esc(best.r.player)+'</a></p><p>'+gameName(g)+'</p></article>';
 }).join("")+'</div>'
 +defs.map(([label,category,key])=>{
  const list=d.rows.map(r=>({r,val:stat(r[category]?.[key])})).filter(x=>x.val!=null&&d.gameMap.has(x.r.game_id));
  list.sort((a,b)=>b.val-a.val||a.r.player.localeCompare(b.r.player));
  return '<h2>Top '+esc(label.toLowerCase())+' games</h2>'+htmlTable(["#","Player","Performance","Date / matchup"],list.slice(0,10).map(({r,val},i)=>'<tr><td>'+(i+1)+'</td><td><a href="'+playerUrl(r)+'">'+esc(r.player)+'</a></td><td>'+esc(key==="outs"?Math.floor(val/3)+"."+(val%3)+" IP":fmt(val))+'</td><td>'+gameName(d.gameMap.get(r.game_id))+'</td></tr>'));
 }).join("")
 :pending("Individual-game batting and pitching records will appear after your attendance list is matched to official college baseball scorebooks. No records have been fabricated."));
}
function render(){
 const page=document.body.dataset.page||"home",app=$("app");
 $("navigation").innerHTML=nav(page);
 const archive=cachedLoad();
 archive.then(initQuickSearch).catch(()=>{const results=$("cb-quick-results");if(results){results.innerHTML='<p class="cb-quick-empty">Archive search is temporarily unavailable.</p>';results.hidden=false}});
 if(page==="mlb-alumni")return;
 app.innerHTML=pending("Loading college baseball attendance records…");
 archive.then(async d=>{
  if(page==="games")await renderGames(d);
  else if(page==="players")renderPlayers(d);
  else if(page==="records")renderRecords(d);
  else if(page==="player")await renderPlayer(d);
  else renderHome(d);
 }).catch(e=>{app.innerHTML=pending("Unable to load college baseball data: "+e.message)});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",render,{once:true});
else render();
window.CollegeBaseballArchive={load:cachedLoad,bat,pitch};
})();
