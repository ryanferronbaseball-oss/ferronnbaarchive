#!/usr/bin/env node
/** Add one personally attended, finalized ESPN NCAAB game to Courtside Archive.
 *
 * ESPN summary is downloaded separately, so every source record is inspectable.
 * This importer checks identities, full scores, all participating player lines,
 * and team minutes before touching the archive files.
 *
 * Example:
 * node college/scripts/import_confirmed_game.mjs \
 *   --summary=/tmp/espn_401920703.json --id=96 --date=2026-11-07 \
 *   --away='SIU Edwardsville' --home=Lipscomb --arena='Allen Arena' \
 *   --venue-source=https://lipscombsports.com/sports/mbball/schedule \
 *   --attendance-confirmed
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const args=Object.fromEntries(process.argv.slice(2).filter(x=>x.startsWith('--')).map(x=>{
  const i=x.indexOf('=');return i<0?[x.slice(2),true]:[x.slice(2,i),x.slice(i+1)];
}));
const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
assert(args['attendance-confirmed']===true,'Attendance confirmation is mandatory');
for(const key of ['summary','id','date','away','home','arena','venue-source'])assert(args[key],`Missing --${key}`);
const id=String(args.id), date=args.date;
assert(/^\d+$/.test(id)&&/^\d{4}-\d{2}-\d{2}$/.test(date),'Invalid ID or date');
assert(/^https:\/\//.test(args['venue-source']),'Verified venue source must be HTTPS');
const summary=JSON.parse(fs.readFileSync(args.summary,'utf8'));
const event=summary.header?.id||summary.header?.competitions?.[0]?.id;
assert(/^\d+$/.test(String(event||'')),'ESPN event ID missing');
assert(summary.header?.competitions?.[0]?.status?.type?.completed===true,'Game not final');
const source=`https://www.espn.com/mens-college-basketball/boxscore/_/gameId/${event}`;
const comps=summary.header.competitions[0].competitors;
assert(comps?.length===2,'Expected two teams');
const bySide=Object.fromEntries(comps.map(c=>[c.homeAway,c]));
const away=bySide.away, home=bySide.home;
assert(away?.team?.displayName?.toLowerCase().startsWith(args.away.toLowerCase()),'Away team mismatch');
assert(home?.team?.displayName?.toLowerCase().startsWith(args.home.toLowerCase()),'Home team mismatch');
const localDate=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Chicago',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(summary.header.competitions[0].date));
assert(localDate===date,`ESPN event local date ${localDate} != ${date}`);
assert(summary.gameInfo?.venue?.fullName===args.arena,'ESPN venue mismatch');

const data=path.join(root,'data');
const read=name=>fs.readFileSync(path.join(data,name),'utf8');
const attendance=read('attendance.csv'), games=read('games.csv'), venueCsv=read('verified_venues.csv');
const oldPlayers=JSON.parse(read('player_boxscores_espn.json'));
const names=JSON.parse(read('team_names.json'));
const listIds=csv=>csv.trimEnd().split(/\r?\n/).slice(1).map(line=>line.split(',')[0]);
for(const [label,csv] of [['attendance',attendance],['games',games],['venues',venueCsv]]){
  assert(!listIds(csv).includes(id),`Attendance ID ${id} already in ${label}`);
}
assert(!games.includes(`,${event},`)&&!oldPlayers.some(p=>String(p.espn_event_id)===String(event)),'ESPN event already imported');
const oldIds=listIds(attendance).map(Number);
assert(Number(id)===Math.max(...oldIds)+1,'Attendance IDs must append monotonically');
assert(!Object.hasOwn(names,String(away.team.id))||names[away.team.id]===args.away,'Existing away team ID conflict');
assert(!Object.hasOwn(names,String(home.team.id))||names[home.team.id]===args.home,'Existing home team ID conflict');

const parsePair=x=>{const parts=String(x).split('-').map(Number);assert(parts.length===2&&parts.every(Number.isInteger),'Invalid shot value '+x);return parts;};
const mins=x=>{const t=String(x);if(t.includes(':')){const [m,s]=t.split(':').map(Number);assert(Number.isInteger(m)&&Number.isInteger(s)&&s<60,'Invalid minute notation '+t);return m+s/60;}const n=Number(t);assert(Number.isFinite(n)&&n>=0,'Invalid minutes '+t);return n;};
const stats=[];
for(const bucket of summary.boxscore?.players||[]){
  const tid=String(bucket.team?.id);
  const target=tid===String(away.team.id)?{name:args.away,opp:args.home}:tid===String(home.team.id)?{name:args.home,opp:args.away}:null;
  assert(target,`Unrecognized ESPN box score team ${tid}`);
  for(const group of bucket.statistics||[]){
    for(const p of group.athletes||[]){
      if(p.didNotPlay===true)continue;
      assert(p.athlete?.id&&Array.isArray(p.stats)&&p.stats.length===group.names.length,'Incomplete player line');
      const fields=Object.fromEntries(group.names.map((key,i)=>[key,p.stats[i]]));
      for(const key of ['MIN','PTS','FG','3PT','FT','REB','AST','TO','STL','BLK','OREB','DREB','PF'])assert(fields[key]!==undefined&&fields[key]!=='','Missing '+key+' for '+p.athlete.displayName);
      const [fgm,fga]=parsePair(fields.FG),[fg3m,fg3a]=parsePair(fields['3PT']),[ftm,fta]=parsePair(fields.FT);
      const v={game_id:id,espn_event_id:String(event),date,player_id:'espn:'+p.athlete.id,
        player:p.athlete.displayName,team_id:tid,minutes:fields.MIN,pts:Number(fields.PTS),
        reb:Number(fields.REB),ast:Number(fields.AST),fgm,fga,fg3m,fg3a,ftm,fta,
        oreb:Number(fields.OREB),dreb:Number(fields.DREB),stl:Number(fields.STL),
        blk:Number(fields.BLK),tov:Number(fields.TO),pf:Number(fields.PF),
        team:target.name,opponent:target.opp,source:'ESPN summary API',source_url:source,
        supplemental_official_source:false,official_override_source:false};
      assert(Object.values(v).filter(x=>typeof x==='number').every(x=>Number.isInteger(x)&&x>=0),'Invalid numeric stat');
      assert(v.fgm<=v.fga&&v.fg3m<=v.fg3a&&v.ftm<=v.fta&&v.fg3m<=v.fgm&&v.fg3a<=v.fga,'Impossible shooting line');
      assert(v.pts===2*v.fgm+v.fg3m+v.ftm,'Player point formula mismatch for '+v.player);
      assert(v.reb===v.oreb+v.dreb,'Player rebounds mismatch for '+v.player);
      assert(!oldPlayers.some(o=>o.player_id===v.player_id&&o.player!==v.player),'Existing athlete ID has a different name: '+v.player);
      stats.push(v);
    }
  }
}
assert(stats.length>0&&new Set(stats.map(p=>p.player_id)).size===stats.length,'Missing or duplicate played players');
const periods=Number(summary.header.competitions[0].status?.period||2);
const expectedMinutes=200+Math.max(0,periods-2)*25;
for(const [side,c] of [['away',away],['home',home]]){
  const lines=stats.filter(p=>p.team_id===String(c.team.id));
  assert(lines.length>0,`No ${side} players`);
  assert(lines.reduce((s,p)=>s+p.pts,0)===Number(c.score),`${side} player points do not reconcile`);
  const total=lines.reduce((s,p)=>s+mins(p.minutes),0);
  assert(Math.abs(total-expectedMinutes)<1.1,`${side} player minutes ${total} != ${expectedMinutes}`);
}
const append=(s,line)=>s.replace(/\s*$/,'')+'\n'+line+'\n';
const updated={
  'attendance.csv':append(attendance,`${id},${date},${args.away},${args.home}`),
  'games.csv':append(games,`${id},${date},${args.away},${args.home},${args.arena},${event},${away.score},${home.score},${away.team.id},${home.team.id},complete,home`),
  'verified_venues.csv':append(venueCsv,`${id},${event},${args.arena},home,${args['venue-source']},Official host-school schedule and ESPN venue`),
  'player_boxscores_espn.json':JSON.stringify([...oldPlayers,...stats])+'\n',
  'team_names.json':JSON.stringify({...names,[away.team.id]:args.away,[home.team.id]:args.home},null,2)+'\n'
};
for(const [file,content] of Object.entries(updated))fs.writeFileSync(path.join(data,file),content);
const impact=p=>p.pts+p.reb+p.ast+p.stl+p.blk-p.tov-(p.fga-p.fgm)-(p.fta-p.ftm);
const leaders=stats.slice().sort((a,b)=>impact(b)-impact(a)||b.pts-a.pts);
console.log(JSON.stringify({game_id:id,espn_event_id:event,score:`${args.away} ${away.score}, ${args.home} ${home.score}`,
  player_lines:stats.length,team_minutes:expectedMinutes,player_of_game:{name:leaders[0].player,impact:impact(leaders[0])},
  top_five:leaders.slice(0,5).map(p=>({name:p.player,team:p.team,impact:impact(p)}))},null,2));
