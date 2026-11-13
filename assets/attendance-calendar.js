/* Historical attendance calendar — automatically indexes all nine archive datasets. */
(()=>{'use strict';
 const root=document.getElementById('calendarGrid');if(!root)return;
 const months=['January','February','March','April','May','June','July','August','September','October','November','December'];
 const sports=[
  {name:'NBA',color:'#b66b37',path:'./data/games.csv',kind:'csv',url:'./nba/game.html?id='},
  {name:'College Basketball',color:'#8357a6',path:'./college/data/games.csv',kind:'csv',url:'./college/game.html?id='},
  {name:'NFL',color:'#b44e59',path:'./nfl/data/games.json',url:'./nfl/game.html?id='},
  {name:'College Football',color:'#577bba',path:'./cfb/data/games.json',url:'./cfb/game.html?id='},
  {name:'Soccer',color:'#339b85',path:'./soccer/data/matches.json',url:'./soccer/game.html?id='},
  {name:'MLB',color:'#c89a35',path:'./mlb/data/attendance.json',url:'./mlb/game.html?id='},
  {name:'MiLB',color:'#3a92b7',path:'./milb/data/games.json',url:'./milb/game.html?id='},
  {name:'College Baseball',color:'#658d4c',path:'./college-baseball/data/games.json',url:'./college-baseball/game.html?id='},
  {name:'NHL',color:'#6a689a',path:'./nhl/data/games.json',url:'./nhl/game.html?id='}
 ];
 const today=new Date();let year=today.getFullYear(),month=today.getMonth(),selected=null,filter='All',games=[],loaded=false;
 const byId=id=>document.getElementById(id),escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const parseCSV=txt=>{const rows=txt.replace(/\r/g,'').trim().split('\n');const parse=line=>{const out=[];let token='',quote=false;for(let i=0;i<line.length;i++){const ch=line[i];if(ch==='"'){if(quote&&line[i+1]==='"'){token+='"';i++}else quote=!quote}else if(ch===','&&!quote){out.push(token);token=''}else token+=ch}out.push(token);return out};const headers=parse(rows.shift());return rows.filter(Boolean).map(row=>Object.fromEntries(parse(row).map((v,i)=>[headers[i],v])))};
 const getRecords=async sport=>{const r=await fetch(sport.path,{cache:'no-store'});if(!r.ok)throw Error(sport.path);return sport.kind==='csv'?parseCSV(await r.text()):r.json()};
 const dateKey=(y,m,d)=>`${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
 const filtered=()=>games.filter(g=>filter==='All'||g.sport===filter);
 const setMonth=(y,m)=>{const d=new Date(y,m,1);year=d.getFullYear();month=d.getMonth();selected=null;render()};
 const monthSelect=byId('calendarMonth'),yearSelect=byId('calendarYear');months.forEach((name,i)=>monthSelect.add(new Option(name,i)));
 const oldest=2000,newest=Math.max(today.getFullYear(),2026);for(let y=newest;y>=oldest;y--)yearSelect.add(new Option(y,y));
 byId('calendarPrev').addEventListener('click',()=>setMonth(year,month-1));byId('calendarNext').addEventListener('click',()=>setMonth(year,month+1));byId('calendarToday').addEventListener('click',()=>setMonth(today.getFullYear(),today.getMonth()));
 monthSelect.addEventListener('change',()=>setMonth(year,Number(monthSelect.value)));yearSelect.addEventListener('change',()=>setMonth(Number(yearSelect.value),month));
 const filters=byId('calendarFilters');
 const renderFilters=()=>{filters.innerHTML=[{name:'All',color:'#284d3c'},...sports].map(s=>`<button type="button" class="calendar-filter" data-sport="${escape(s.name)}" aria-pressed="${filter===s.name}"><span class="calendar-filter-dot" style="--dot:${s.color}"></span>${escape(s.name)}</button>`).join('')};
 filters.addEventListener('click',e=>{const button=e.target.closest('button[data-sport]');if(!button)return;filter=button.dataset.sport;render()});
 root.addEventListener('click',e=>{const day=e.target.closest('button[data-date]');if(!day)return;selected=day.dataset.date;render()});
 const details=byId('calendarDetails');
 const renderDetails=items=>{if(!selected){details.innerHTML='<p>Select a marked date to see its games.</p>';return}const d=new Date(selected+'T12:00:00');const events=items.filter(g=>g.date===selected);details.innerHTML=`<h3>${escape(d.toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'}))}</h3>`+(events.length?events.map(g=>`<div class="calendar-game"><div class="calendar-game-info"><span class="calendar-dot" style="--dot:${g.color};margin-top:5px"></span><div><div class="calendar-game-sport">${escape(g.sport)}</div><div class="calendar-game-name">${escape(g.away)} at ${escape(g.home)}</div>${g.score?`<div class="calendar-game-meta">${escape(g.score)}</div>`:''}${g.venue?`<div class="calendar-game-meta">${escape(g.venue)}</div>`:''}</div></div><a href="${escape(g.url)}">View game ↗</a></div>`).join(''):'<p>No archived games for this date with the current filter.</p>')};
 const render=()=>{monthSelect.value=month;yearSelect.value=year;renderFilters();const items=filtered(),first=new Date(year,month,1).getDay(),days=new Date(year,month+1,0).getDate(),cells=Math.ceil((first+days)/7)*7;const perDay=new Map();for(const g of items){if(g.date.slice(0,7)!==dateKey(year,month,1).slice(0,7))continue;if(!perDay.has(g.date))perDay.set(g.date,[]);perDay.get(g.date).push(g)}
  root.innerHTML=Array.from({length:cells},(_,i)=>{const day=i-first+1;if(day<1||day>days)return '<span class="calendar-day-outside" aria-hidden="true"></span>';const key=dateKey(year,month,day),events=perDay.get(key)||[],isToday=key===dateKey(today.getFullYear(),today.getMonth(),today.getDate());return `<button type="button" class="calendar-day${isToday?' is-today':''}" data-date="${key}" aria-pressed="${selected===key}" aria-label="${escape(months[month])} ${day}: ${events.length} ${events.length===1?'game':'games'}"><span class="calendar-day-number">${day}</span><span class="calendar-day-dots">${events.slice(0,15).map(g=>`<span class="calendar-dot" style="--dot:${g.color}"></span>`).join('')}${events.length>15?'<small>+ '+(events.length-15)+'</small>':''}</span></button>`}).join('');const count=[...perDay.values()].reduce((n,a)=>n+a.length,0);byId('calendarCount').textContent=loaded?`${count} ${count===1?'game':'games'} in ${months[month]} ${year}`:'Loading games…';renderDetails(items)};
 render();Promise.allSettled(sports.map(async sport=>{const records=await getRecords(sport);return records.filter(g=>sport.name!=='College Baseball'||g.verification!=='attendance_only').map(g=>({sport:sport.name,color:sport.color,date:g.date,away:g.away||g.away_team||'Away',home:g.home||g.home_team||'Home',score:g.away_score!=null&&g.home_score!=null?`${g.away_score}–${g.home_score}`:'',venue:g.arena||g.venue||g.stadium||'',url:sport.url+encodeURIComponent(sport.name==='MLB'?g.attendance_id:g.id)})).filter(g=>/^\d{4}-\d{2}-\d{2}$/.test(g.date))})).then(results=>{games=results.filter(r=>r.status==='fulfilled').flatMap(r=>r.value).sort((a,b)=>a.date.localeCompare(b.date));loaded=true;render();const failed=results.filter(r=>r.status==='rejected');if(failed.length){byId('calendarCount').textContent+=` · ${failed.length} archive ${failed.length===1?'source':'sources'} unavailable`}});
})();
