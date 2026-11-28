"""Recover UTSA historical portraits from labeled official media roster PDFs."""
import hashlib, io, json, re, unicodedata
from pathlib import Path
import fitz
import requests
from PIL import Image
from audit_player_portraits import load, save, ROOT

SOURCES=[
    ("2018-19","https://storage.googleapis.com/goutsa-prod/2023/08/02/AG9FtVcu553tbFxgMBUkwK017FEXRgtBS8ui7Wey.pdf",
     ["Charlotte Ellmore","Evelyn Omemmah","Tasharian Robinson","Ryann Stearns","Deja Cousin","Timea Toth","Kourtney Kekec","Marie Benson","Tija Hawkins","Barbara Benson","Karrington Donald","Mandi Cooks"],
     ["Tasharian Robinson","Timea Toth","Kourtney Kekec","Marie Benson","Tija Hawkins","Barbara Benson","Karrington Donald"]),
    ("2016-17","https://tulanegreenwave.com/documents/download/2016/11/24/UTSA_Notes.pdf",
     ["Kasia Kiedjrowska","Alexus Dukes","Crystal Chidomere","Deja Cousin","Timea Toth","Kourtney Kekec","Marie Benson","Tija Hawkins","Tesha Smith","Carlie Heineman","Loryn Goodwin","Billie Marlow"],
     ["Crystal Chidomere","Carlie Heineman","Billie Marlow"])
]
def norm(s):
    return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).lower())
def labels(page,names):
    result={}
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            spans=line.get('spans',[])
            s=' '.join(x['text'] for x in spans)
            for n in names:
                if norm(n) in norm(s) and len(norm(s))<=len(norm(n))+15:
                    # Name-only lines, including a jersey number and position.
                    result.setdefault(n,[]).append(fitz.Rect(line['bbox']))
    for n in names:
        if n not in result:
            for alias in [n,n.replace('Toth','Tóth'),n.replace('Kiedjrowska','Kiejdrowska')]:
                rr=page.search_for(alias)
                if rr:result[n]=rr;break
    return result
def select_images(page,names):
    ls=labels(page,names)
    imgs=[]
    for inf in page.get_image_info(xrefs=True):
        r=fitz.Rect(inf['bbox'])
        if r.width<38 or r.height<45 or r.width>page.rect.width*.32 or r.height>page.rect.height*.26:continue
        if r.width/r.height>1.45 or r.width/r.height<.38:continue
        if not any(abs(r.x0-q.x0)<1 and abs(r.y0-q.y0)<1 and abs(r.x1-q.x1)<1 and abs(r.y1-q.y1)<1 for q in imgs):imgs.append(r)
    chosen={}
    for name in names:
        candidates=[]
        for label in ls.get(name,[]):
            for im in imgs:
                dx=abs((label.x0+label.x1-im.x0-im.x1)/2)
                gap=label.y0-im.y1
                if dx<=im.width*.48 and -5<=gap<=45 and im.y0<label.y0-32:
                    candidates.append((abs(gap)+dx*.8,im))
        candidates.sort(key=lambda x:x[0])
        if not candidates:continue
        score,rect=candidates[0]
        if len(candidates)>1 and candidates[1][0]-score<2 and candidates[1][1]!=rect:continue
        chosen[name]=rect
    # Require a coherent roster: at least 10 distinct labels and photographs.
    if len(chosen)<10 or len({tuple(r) for r in chosen.values()})!=len(chosen):
        raise ValueError('Roster image-label alignment not uniquely verified: '+str(list(chosen)))
    # Confirm the expected printed order independently.
    ordered=sorted(chosen,key=lambda n:(round(chosen[n].y0/15),chosen[n].x0))
    expected=[n for n in names if n in chosen]
    if ordered!=expected:
        # Images within the same row may have slightly differing top positions.
        rows=[]
        for n in sorted(chosen,key=lambda n:chosen[n].y0):
            if not rows or abs(chosen[n].y0-chosen[rows[-1][0]].y0)>20:rows.append([n])
            else:rows[-1].append(n)
        ordered=[n for row in rows for n in sorted(row,key=lambda n:chosen[n].x0)]
        if ordered!=expected:raise ValueError('Unexpected portrait row order: '+str(ordered))
    return chosen
def main():
    data=load('college-women/data/player_headshots.json',{'players':{}})
    reg=data['players'];targets=load('college-women/data/school_portrait_targets.json',{})
    audit=load('college-women/reports/school_portrait_audit.json',{})
    report={'targeted':10,'added':[],'preserved':[],'missing':[],'sources':[]}
    root=ROOT/'college-women/assets/portraits/utsa';root.mkdir(parents=True,exist_ok=True)
    for year,url,all_names,wanted in SOURCES:
        try:
            response=requests.get(url,timeout=60,headers={'User-Agent':'Mozilla/5.0'})
            response.raise_for_status()
            doc=fitz.open(stream=response.content,filetype='pdf')
            matches=[]
            diagnostics=[]
            for page in doc:
                text=norm(page.get_text())
                count=sum(norm(n) in text for n in all_names)
                if count<10:continue
                try:
                    aligned=select_images(page,all_names)
                    if all(n in aligned for n in wanted):matches.append((page.number,aligned))
                except Exception as exc:diagnostics.append({'page':page.number+1,'names':count,'error':str(exc)})
            if len(matches)!=1:raise ValueError('Expected one fully aligned portrait roster, found '+str(len(matches))+'; '+str(diagnostics))
            page_index,aligned=matches[0]
            page=doc[page_index]
            page_number=page_index+1
            report['sources'].append({'url':url,'season':year,'page':page_number,'aligned':list(aligned)})
            seen=set()
            for n in wanted:
                pid=next((p for p,t in targets.items() if p.startswith('school:utsa:') and norm(t['names'][0])==norm(n)),None)
                if not pid:raise ValueError('Missing target '+n)
                if pid in reg:report['preserved'].append(pid);continue
                if n not in aligned:report['missing'].append({'id':pid,'name':n,'reason':'No unique portrait rectangle'});continue
                rect=aligned[n]
                pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=rect,alpha=False)
                im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
                if min(im.size)<100:raise ValueError('Portrait resolution too small')
                digest=hashlib.sha256(im.tobytes()).hexdigest()
                if digest in seen:raise ValueError('Duplicate portrait')
                seen.add(digest)
                im.thumbnail((450,550))
                file=pid.rsplit(':',1)[-1]+'.jpg'
                im.save(root/file,quality=92,optimize=True)
                reg[pid]={'image_url':'./assets/portraits/utsa/'+file,'source_url':url,'provider':'official school','source_page':page_number,'source_season':year,'source_type':'official media roster PDF'}
                report['added'].append({'id':pid,'name':n,'source_url':url,'page':page_number,'season':year,'bbox':list(rect)})
        except Exception as ex:
            report['sources'].append({'url':url,'season':year,'error':str(ex)})
            for n in wanted:
                pid=next((p for p,t in targets.items() if p.startswith('school:utsa:') and norm(t['names'][0])==norm(n)),None)
                if pid and pid not in reg and not any(m['id']==pid for m in report['missing']):
                    report['missing'].append({'id':pid,'name':n,'reason':str(ex)})
    report['verified_total']=sum(p.startswith('school:utsa:') for p in reg)
    audit['verified_total']=sum(p in reg for p in targets)
    audit['missing']=[m for m in audit.get('missing',[]) if m['id'] not in reg]
    audit['utsa_pdf_recovery']=report
    save('college-women/data/player_headshots.json',data)
    save('college-women/reports/school_portrait_audit.json',audit)
    save('college-women/reports/utsa_portrait_recovery.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
