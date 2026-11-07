(()=>{'use strict';
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmtDate=iso=>new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric',timeZone:'UTC'});
  const fmtShort=iso=>new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
  const sportRoutes={'NBA':'../nba/','College Basketball':'../college/','NFL':'../nfl/','College Football':'../cfb/','Soccer':'../soccer/','MiLB':'../milb/','MLB':'../mlb/','College Baseball':'../college-baseball/'};
  const sportOrder=['College Baseball','MLB','MiLB','College Basketball','NBA','College Football','NFL','Soccer'];
  const venueSports=v=>Array.isArray(v.sports)&&v.sports.length?v.sports:[v.sport];
  const hasSport=(v,s)=>venueSports(v).includes(s);
  const profileHref=v=>`./venue.html?id=${encodeURIComponent(v.id)}`;
  const score=g=>g.awayScore==null||g.homeScore==null?'—':`${g.awayScore}–${g.homeScore}`;
  const page=document.body.dataset.venuePage;
  const venuesRequest=fetch('./data/venues.json').then(r=>{if(!r.ok)throw Error('venue data unavailable');return r.json()});
  const photosRequest=fetch('./data/photos.json').then(r=>r.ok?r.json():{photos:{}}).catch(()=>({photos:{}}));
  Promise.all([venuesRequest,photosRequest]).then(([data,photoData])=>{
    if(!Array.isArray(data.venues)||data.venues.length===0||data.venueCount!==data.venues.length)throw Error('venue inventory incomplete');
    if(page==='directory')renderDirectory(data.venues);
    else if(page==='profile')renderProfile(data.venues,photoData.photos||{});
  }).catch(err=>{
    const target=page==='directory'?$('venueDirectory'):$('venueProfile');
    if(target)target.innerHTML=`<div class="vp-empty">Venue information is temporarily unavailable. <a href="../">Return to Courtside Archive</a>.</div>`;
    console.warn('Venue directory:',err.message);
  });

  function renderDirectory(venues){
    const list=$('venueDirectory'),query=$('venueDirectorySearch'),sport=$('venueDirectorySport');
    for(const name of sportOrder.filter(s=>venues.some(v=>hasSport(v,s)))){
      const option=document.createElement('option');option.value=name;option.textContent=name;sport.append(option);
    }
    const sorted=venues.slice().sort((a,b)=>b.visits-a.visits||a.name.localeCompare(b.name));
    function update(){
      const q=query.value.trim().toLowerCase(),chosen=sport.value;
      const found=sorted.filter(v=>(chosen==='All'||hasSport(v,chosen))&&(!q||`${v.name} ${v.city}`.toLowerCase().includes(q)));
      $('venueDirectoryStatus').textContent=`Showing ${found.length} of ${venues.length} venues · ${dataGameTotal(venues).toLocaleString()} linked games`;
      list.innerHTML=found.length?found.map(v=>`<a class="vp-venue" href="${profileHref(v)}"><small>${esc(venueSports(v).join(' + '))}</small><strong>${esc(v.name)}</strong><span>${esc(v.city)}</span><em>${v.visits} ${v.visits===1?'game':'games'} attended · First ${fmtShort(v.firstVisit)} →</em></a>`).join(''):'<div class="vp-empty">No venues match this search.</div>';
    }
    query.addEventListener('input',update);sport.addEventListener('change',update);update();
  }
  function dataGameTotal(venues){return venues.reduce((n,v)=>n+v.visits,0);}

  function renderProfile(venues,photos){
    const id=new URLSearchParams(window.location.search).get('id');
    const v=venues.find(x=>x.id===id),target=$('venueProfile');
    if(!v){target.innerHTML='<div class="vp-intro"><h1>Venue not found.</h1><p>Try the <a href="./">complete venue directory</a> or the <a href="../#venues">interactive map</a>.</p></div>';return;}
    document.title=`${v.name} | Courtside Archive`;
    $('venueCrumb').textContent=v.name;
    const first=v.games[0],activeSports=venueSports(v),years=new Set(v.games.map(g=>g.date.slice(0,4))).size;
    const photoLabel=v.sport.includes('Basketball')||v.sport==='NBA'?'Arena profile':v.sport.includes('Football')||v.sport==='NFL'?'Stadium profile':'Ballpark profile';
    const photo=photos[v.id];
    const photoFile=photo?`./photos/${encodeURIComponent(photo.file)}?v=2`:'';
    const photoMarkup=photo?`<figure class="vp-photo-figure"><a href="${esc(photoFile)}" target="_blank" rel="noopener noreferrer" aria-label="View full-size photograph of ${esc(v.name)}"><img src="${esc(photoFile)}" alt="${esc(photo.alt)}" loading="eager" decoding="async"></a><figcaption>Photo: ${esc(photo.credit)} <a href="${esc(photoFile)}" target="_blank" rel="noopener noreferrer">View full image ↗</a></figcaption></figure>`:`<div class="vp-photo-placeholder" aria-label="Stadium photography will be added later"><span>Courtside Archive</span><strong>${esc(photoLabel)}</strong></div>`;
    const sources=v.sources.map((url,i)=>`<li><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Venue reference ${i+1} ↗</a></li>`).join('');
    target.innerHTML=`
      <section class="vp-profile-head">
        <div>
          <span class="vp-sport">${esc(activeSports.join(" + "))}</span>
          <h1>${esc(v.name)}</h1>
          <p class="vp-place">📍 ${esc(v.city)}</p>
          <p style="font-size:15px;color:#657467;line-height:1.7;max-width:620px">The first recorded Courtside Archive visit was ${fmtDate(v.firstVisit)}. Explore the venue's history, key facts, and all ${v.visits} attended ${v.visits===1?'game':'games'}.</p>
          <div class="vp-profile-actions">
            <a href="../?venue=${encodeURIComponent(v.id)}#venues">Locate on interactive map ↗</a>
            ${activeSports.map(s=>`<a class="secondary" href="${esc(sportRoutes[s]||'../')}">Explore ${esc(s)} archive ↗</a>`).join("")}
          </div>
        </div>
        ${photoMarkup}
      </section>
      <section class="vp-stats" aria-label="Personal attendance overview">
        <div class="vp-stat"><span>Games attended</span><strong>${v.visits.toLocaleString()}</strong></div>
        <div class="vp-stat"><span>First visit</span><strong>${fmtShort(v.firstVisit)}</strong></div>
        <div class="vp-stat"><span>Most recent visit</span><strong>${fmtShort(v.lastVisit)}</strong></div>
      </section>
      <div class="vp-content">
        <div>
          <section class="vp-panel"><h2>About the venue</h2><div class="vp-facts">
            <div><small>Address / access point</small><strong>${esc(v.address||v.city)}</strong></div>
            <div><small>Opened / venue era</small><strong>${esc(v.opened)}</strong></div>
            <div><small>Capacity / seating context</small><strong>${esc(v.capacity)}</strong></div>
            <div><small>Primary occupants</small><strong>${esc(v.occupants)}</strong></div>
          </div>${v.factNote?`<p class="vp-note">${esc(v.factNote)}</p>`:''}</section>
          <section class="vp-panel"><h2>Venue history and names</h2><p>${esc(v.history)}</p></section>
          <section class="vp-panel" id="attended-games"><div class="vp-games-head"><h2>My games here</h2><small>${v.visits} games across ${years} ${years===1?'year':'years'}</small></div>
            <div class="vp-table-scroll"><table class="vp-table"><thead><tr><th scope="col">Date</th><th scope="col">Matchup</th><th scope="col">Score</th><th scope="col">Game</th></tr></thead><tbody id="venueGamesRows"></tbody></table></div>
            <button class="vp-show-more" id="venueGamesMore" type="button" hidden>Show more games</button>
          </section>
        </div>
        <aside>
          <section class="vp-panel"><h2>First time here</h2><p><strong style="color:#284d3c">${fmtDate(v.firstVisit)}</strong></p><p style="margin-top:10px">${esc(first.away)} at ${esc(first.home)}${score(first)!=='—'?` · ${score(first)}`:''}</p><p style="margin-top:15px"><a href="${esc(first.url)}">View my first game here →</a></p></section>
          <section class="vp-panel"><h2>Location</h2><p>${esc(v.address||v.city)}</p><p style="margin-top:9px"><a target="_blank" rel="noopener noreferrer" href="https://www.openstreetmap.org/?mlat=${encodeURIComponent(v.lat)}&amp;mlon=${encodeURIComponent(v.lon)}#map=16/${encodeURIComponent(v.lat)}/${encodeURIComponent(v.lon)}">Open venue location ↗</a></p></section>
          ${sources?`<section class="vp-panel"><h2>Venue references</h2><ul class="vp-sources">${sources}</ul></section>`:''}
        </aside>
      </div>
      <a class="vp-return" href="./">← Explore all venues</a>`;

    const rows=$('venueGamesRows'),more=$('venueGamesMore');
    const games=v.games.slice().reverse();let visible=Math.min(15,games.length);
    function showGames(){
      rows.innerHTML=games.slice(0,visible).map(g=>`<tr><td><a href="${esc(g.url)}">${fmtShort(g.date)}</a></td><td>${esc(g.away)} at ${esc(g.home)}</td><td>${score(g)}</td><td><a href="${esc(g.url)}">Game ↗</a></td></tr>`).join('');
      more.hidden=visible>=games.length;
      more.textContent=`Show more games (${Math.min(25,games.length-visible)} of ${games.length-visible} remaining)`;
    }
    more.addEventListener('click',()=>{visible=Math.min(games.length,visible+25);showGames();});showGames();
  }
})();
