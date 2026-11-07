/* Chronological milestones across the same eight collections as the homepage total. */
(()=>{'use strict';
 const target=document.getElementById('milestoneGrid');if(!target)return;
 const markers=[1,10,25,50,100,150,200,500];
 const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const prettyDate=v=>new Date(v+'T12:00:00Z').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
 const json=async path=>{const r=await fetch(path);if(!r.ok)throw Error('Archive game list unavailable');return r.json()};
 const csv=async path=>{const r=await fetch(path);if(!r.ok)throw Error('Archive game list unavailable');const text=await r.text();
  const lines=text.replace(/\r/g,'').trim().split('\n'),parse=line=>{let fields=[],field='',quoted=false;for(let i=0;i<line.length;i++){const ch=line[i];if(ch==='"'){if(quoted&&line[i+1]==='"'){field+='"';i++}else quoted=!quoted}else if(ch===','&&!quoted){fields.push(field);field=''}else field+=ch}fields.push(field);return fields};
  const names=parse(lines.shift());return lines.filter(Boolean).map(line=>Object.fromEntries(parse(line).map((v,i)=>[names[i],v])));
 };
 const sources=[
  ['NBA','./data/games.csv',csv,'./nba/game.html?id='],
  ['College Basketball','./college/data/games.csv',csv,'./college/game.html?id='],
  ['NFL','./nfl/data/games.json',json,'./nfl/game.html?id='],
  ['College Football','./cfb/data/games.json',json,'./cfb/game.html?id='],
  ['Soccer','./soccer/data/matches.json',json,'./soccer/game.html?id='],
  ['MLB','./mlb/data/attendance.json',json,'./mlb/game.html?id='],
  ['MiLB','./milb/data/games.json',json,'./milb/game.html?id='],
  ['College Baseball','./college-baseball/data/games.json',json,'./college-baseball/game.html?id=']
 ];
 Promise.all(sources.map(async ([sport,path,loader,prefix],sourceIndex)=>{
  const records=await loader(path);
  return records.filter(g=>sport!=='College Baseball'||g.verification!=='attendance_only').map((g,recordIndex)=>({
   sport,date:g.date,away:g.away||g.away_team,home:g.home||g.home_team,
   href:prefix+encodeURIComponent(sport==='MLB'?g.attendance_id:g.id),sourceIndex,recordIndex
  }));
 })).then(parts=>{
  const games=parts.flat().filter(g=>/^\d{4}-\d{2}-\d{2}$/.test(g.date)).sort((a,b)=>a.date.localeCompare(b.date)||a.sourceIndex-b.sourceIndex||a.recordIndex-b.recordIndex);
  target.innerHTML=markers.map(n=>{
   const game=games[n-1];if(!game)return '<div class="milestone-card"><div class="milestone-card-number"><strong>'+n+'</strong>th game</div><div class="milestone-card-matchup">Not reached yet</div></div>';
   const day=games.filter(g=>g.date===game.date),tie=day.length>1;
   return '<a class="milestone-card" href="'+escapeHTML(game.href)+'" aria-label="Game '+n+': '+escapeHTML(game.away+' at '+game.home)+'">'
    +'<div class="milestone-card-number"><strong>'+n+'</strong><span>'+(n===1?'st':n===10?'th':n===25?'th':'th')+' game</span></div>'
    +'<div class="milestone-card-date">'+escapeHTML(prettyDate(game.date))+'</div>'
    +'<div class="milestone-card-matchup">'+escapeHTML(game.away)+' at '+escapeHTML(game.home)+'</div>'
    +'<div class="milestone-card-sport">'+escapeHTML(game.sport)+(tie?' · Same-day order provisional':'')+'</div><span class="milestone-card-link">View game ↗</span></a>';
  }).join('');
  const note=document.getElementById('milestoneNote');if(note)note.textContent+=' '+games.length.toLocaleString()+' eligible games currently indexed. Same-day games are sorted by archive and source order when exact start times are unavailable.';
 }).catch(()=>{target.innerHTML='<p class="milestone-loading">Milestone games could not be loaded. Please try again later.</p>'});
})();
