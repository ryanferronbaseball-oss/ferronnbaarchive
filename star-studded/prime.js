/* Award-year evidence for Star-Studded Games, distinct from lifetime career legacy.
   Scores are relative era proximity indicators, NOT real performance metrics. */
(()=>{'use strict';
const year=v=>{
 if(v==null)return null;
 if(typeof v==='number'&&v>=1900&&v<2100)return v;
 const s=String(v);
 const span=s.match(/\b(19\d\d|20\d\d)\s*[-–]\s*(\d{2,4})\b/);
 if(span){const from=Number(span[1]),tail=span[2];return tail.length===4?Number(tail):Math.floor(from/100)*100+Number(tail)+(Number(tail)<from%100?100:0);}
 const full=s.match(/\b(19\d\d|20\d\d)\b/);
 return full?Number(full[1]):null;
};
const yearOf=(sport,date)=>{
 const y=Number(String(date).slice(0,4)),m=Number(String(date).slice(5,7));
 if(!Number.isInteger(y)||y<1900)return null;
 if(['NBA','NHL','College Basketball'].includes(sport))return m>=7?y+1:y;
 if(['NFL','College Football'].includes(sport))return m<=2?y-1:y;
 // Soccer honors commonly use season-end years; calendar years remain usable.
 if(sport==='Soccer')return m>=8?y+1:y;
 return y;
};
const signal=(value,weight,title)=>{
 const y=year(value);
 return y===null||weight<=0?null:{year:y,weight,title:String(title||'Award-year evidence')};
};
const list=(items,weight,title,select=v=>v)=>{
 if(!Array.isArray(items))return [];
 return items.map(item=>signal(select(item),weight,typeof title==='function'?title(item):title)).filter(Boolean);
};
function assess(sport,date,items){
 const season=yearOf(sport,date);
 const evidence=(items||[]).filter(x=>x&&Number.isFinite(x.year)&&x.year>=1900&&x.year<=2100&&x.weight>0);
 if(season===null||!evidence.length)return{score:null,label:'Not rated',tier:'unknown',detail:'No dated individual honors in the reviewed files',season,referenceYear:null,assessed:false};
 const annual=new Map();
 for(const e of evidence){
  const rec=annual.get(e.year)||{points:0,labels:[]};
  rec.points+=e.weight;rec.labels.push(e.title);annual.set(e.year,rec);
 }
 // Avoid counting an award twice when the same source is included in two files.
 const all=[...annual].sort((a,b)=>a[0]-b[0]);
 const peak=Math.max(...all.map(([y,v])=>v.points));
 const weighted=all.map(([y,v])=>({
  year:y,raw:v.points,
  weighted:v.points*([1,.7,.32][Math.abs(y-season)]??0),
  labels:v.labels
 })).sort((a,b)=>b.weighted-a.weighted||Math.abs(a.year-season)-Math.abs(b.year-season));
 const nearest=all.reduce((best,[y,v])=>
  best===null||Math.abs(y-season)<Math.abs(best.year-season)?{year:y,points:v.points,labels:v.labels}:best,null);
 const current=annual.get(season)?.points||0;
 const best=weighted[0];
 // An isolated minor award is evidence of recognition, not proof of a peak season.
 // An eight-point baseline requires more than one low-weight honor for a high score.
 const score=Math.max(0,Math.min(100,Math.round(100*best.weighted/Math.max(8,peak))));
 const recent=(nearest.year-season);
 let tier,label;
 const activeThreshold=sport==='College Basketball'?4:5;
 if(current>=activeThreshold&&score>=70){tier='prime';label='Peak-era';}
 else if(current>=activeThreshold){tier='prime';label='Prime-level season';}
 else if(best.raw>=5&&Math.abs(best.year-season)<=1){tier='prime';label='Near documented peak';}
 else if(current>=2){tier='near';label='Award-winning season';}
 else if(recent>=2){tier='rising';label='Before award peak';}
 else if(recent<=-2){tier='past';label='After award peak';}
 else if(score>=20){tier='near';label='Near award window';}
 else{tier='unknown';label='Limited evidence';}
 const referenceYear=best?.weighted>0?best.year:nearest.year;
 const source=best?.weighted>0?best:nearest;
 const detail=source.labels[0]+' · '+referenceYear+(referenceYear!==season?' (retrospective proximity)':' (same season)');
 return {score,label,tier,detail,season,referenceYear,assessed:true,signalCount:evidence.length};
}
window.CourtsidePrime={year,yearOf,signal,list,assess};
})();