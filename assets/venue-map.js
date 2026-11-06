(()=>{'use strict';
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const formatDate=iso=>new Date(`${iso}T12:00:00Z`).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
  const sportColors={'College Baseball':'#356447','MLB':'#1f6a82','College Basketball':'#9b6232','NBA':'#bf722e','NFL':'#7e5c88','College Football':'#8c5539','Soccer':'#617e47'};
  const sportsOrder=['College Baseball','MLB','College Basketball','NBA','College Football','NFL','Soccer'];
  const mapElement=$('venueMap');if(!mapElement)return;
  const fallback=$('venueMapLoading');

  const venuesRequest=fetch('./venues/data/venues.json').then(r=>{if(!r.ok)throw Error('venue directory unavailable');return r.json()});
  const photosRequest=fetch('./venues/data/photos.json').then(r=>r.ok?r.json():{photos:{}}).catch(()=>({photos:{}}));
  Promise.all([venuesRequest,photosRequest]).then(([data,photoData])=>{
    if(!window.L)throw Error('map library unavailable');
    const venues=data.venues,photos=photoData.photos||{};
    if(!venues.length||data.venueCount!==venues.length)throw Error('venue inventory incomplete');
    $('venueCount').textContent=venues.length.toLocaleString();
    $('venueGameCount').textContent=data.mappedGames.toLocaleString();
    $('venueSportCount').textContent=new Set(venues.map(v=>v.sport)).size;
    const map=L.map(mapElement,{minZoom:3,worldCopyJump:false,scrollWheelZoom:false,zoomControl:true});
    L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',{
      subdomains:'abc',maxZoom:19,
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a> · <a href="https://www.openstreetmap.fr/" target="_blank" rel="noopener noreferrer">OSM France</a>'
    }).addTo(map);
    const layer=typeof L.markerClusterGroup==='function' ? L.markerClusterGroup({
      showCoverageOnHover:false,spiderfyOnMaxZoom:true,disableClusteringAtZoom:16,
      maxClusterRadius:42,iconCreateFunction:c=>{
        const n=c.getChildCount(),size=n>35?51:n>10?43:36;
        return L.divIcon({html:`<div class="venue-pin-cluster" style="width:${size}px;height:${size}px">${n}</div>`,className:'',iconSize:[size,size],iconAnchor:[size/2,size/2]});
      }
    }) : L.layerGroup();
    map.addLayer(layer);
    const markers=new Map();
    venues.forEach(v=>{
      const color=sportColors[v.sport]||'#356447';
      const marker=L.marker([v.lat,v.lon],{
        title:v.name,
        icon:L.divIcon({className:'',html:`<span class="venue-sport-pin" style="--pin-color:${color}"></span>`,iconSize:[24,24],iconAnchor:[12,12]})
      });
      const photo=photos[v.id];
      const photoHtml=photo?`<img class="venue-popup-photo" src="./venues/photos/${encodeURIComponent(photo.file)}?v=2" alt="${esc(photo.alt)}" loading="lazy">`:'';
      marker.bindPopup(`<div class="venue-popup">${photoHtml}<small>${esc(v.sport)}</small><h3>${esc(v.name)}</h3><p>${esc(v.city)}</p><div class="venue-popup-facts"><span>Games attended<strong>${v.visits}</strong></span><span>First visit<strong style="font-size:12px">${formatDate(v.firstVisit)}</strong></span></div><a href="./venues/venue.html?id=${encodeURIComponent(v.id)}">View venue profile &rarr;</a></div>`,{maxWidth:290});
      markers.set(v.id,marker);
    });
    let selectedSport='All',search='';
    const buttons=$('venueFilters');
    const filters=['All',...sportsOrder.filter(s=>venues.some(v=>v.sport===s))];
    filters.forEach(s=>{
      const button=document.createElement('button');button.type='button';button.className='venue-filter';
      button.textContent=s==='All'?'All sports':s;button.setAttribute('aria-pressed',String(s==='All'));
      button.addEventListener('click',()=>{selectedSport=s;buttons.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));refresh(true);});
      buttons.append(button);
    });
    const searchInput=$('venueSearch');
    searchInput.addEventListener('input',()=>{search=searchInput.value.trim().toLowerCase();refresh(true);});
    function showVenue(v){
      const marker=markers.get(v.id);if(!marker)return;
      selectedSport='All';search='';searchInput.value='';
      buttons.querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===0)));
      refresh(false);
      map.setView([v.lat,v.lon],16,{animate:true});
      if(typeof layer.zoomToShowLayer==='function')layer.zoomToShowLayer(marker,()=>marker.openPopup());else marker.openPopup();
    }
    function refresh(zoom){
      const matching=venues.filter(v=>(selectedSport==='All'||v.sport===selectedSport)&&(!search||`${v.name} ${v.city} ${v.sport}`.toLowerCase().includes(search)));
      layer.clearLayers();matching.forEach(v=>layer.addLayer(markers.get(v.id)));
      $('venueMapResult').textContent=`Showing ${matching.length} of ${venues.length} venues`;
      $('venueMapEmpty').hidden=matching.length>0;
      if(zoom&&matching.length)map.fitBounds(L.latLngBounds(matching.map(v=>[v.lat,v.lon])).pad(.13),{maxZoom:13,animate:true});
      return matching;
    }
    const mostVisited=venues.slice().sort((a,b)=>b.visits-a.visits||a.name.localeCompare(b.name)).slice(0,6);
    const featured=$('venueFeatured');
    mostVisited.forEach(v=>{
      const b=document.createElement('button');b.type='button';b.textContent=`${v.name} · ${v.visits}`;
      b.addEventListener('click',()=>showVenue(v));featured.append(b);
    });
    refresh(false);
    const bounds=L.latLngBounds(venues.map(v=>[v.lat,v.lon]));map.fitBounds(bounds.pad(.07),{maxZoom:6});
    if(fallback)fallback.hidden=true;
    const target=new URLSearchParams(location.search).get('venue');
    if(target){const found=venues.find(v=>v.id===target);if(found)setTimeout(()=>showVenue(found),250);}
  }).catch(err=>{
    if(fallback){fallback.hidden=false;fallback.innerHTML='<div>The interactive map could not load right now. <a href="./venues/">Browse all venue profiles instead.</a></div>';}
    console.warn('Venue map:',err.message);
  });
})();
