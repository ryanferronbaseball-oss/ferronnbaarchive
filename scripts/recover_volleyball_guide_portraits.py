"""Extract only visually inspected, labeled headshot cells from official guides."""
import hashlib, io, re
from pathlib import Path
import fitz
from PIL import Image, ImageStat
import requests
from audit_player_portraits import load
def norm(s):return re.sub(r'[^a-z0-9]','',s.lower())
def recover(reg,targets):
    added=[];errors={}
    for g in load('college-volleyball/data/portrait_pdf_sources.json',[]):
        todo={pid:box for pid,box in g['crops'].items() if pid not in reg and pid in targets}
        if not todo:continue
        try:
            r=requests.get(g['url'],headers={'User-Agent':'Mozilla/5.0'},timeout=(10,90));r.raise_for_status()
            with fitz.open(stream=r.content,filetype='pdf') as doc:
                page=doc[g['page']]
                txt=norm(page.get_text())
                if norm(g['marker']) not in txt:raise ValueError('Expected guide page marker missing')
                for pid,box in todo.items():
                    try:
                        t=targets[pid]
                        if t['school']!=g['school']:raise ValueError('School mismatch')
                        # Guide page and individual cell positions were inspected in advance.
                        # Require the matching label in a narrow region immediately below the portrait.
                        x0,y0,x1,y1=box
                        sx=page.rect.width/1088;sy=page.rect.height/1408
                        label=page.get_text(clip=fitz.Rect(max(0,x0-3)*sx,y1*sy,min(1088,x1+8)*sx,min(1408,y1+68)*sy))
                        if not any(norm(name) in norm(label) for name in t['names']):
                            raise ValueError('Adjacent label mismatch: '+label[:100])
                        rect=fitz.Rect((x0+2)*sx,(y0+2)*sy,(x1-2)*sx,(y1-2)*sy)
                        pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=rect,alpha=False)
                        im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
                        if min(im.size)<120 or max(ImageStat.Stat(im).stddev)<8:raise ValueError('Blank or undersized crop')
                        digest=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
                        if any(v.get('sha256')==digest for v in reg.values()):raise ValueError('Duplicate crop')
                        dst=Path('college-volleyball/assets/portraits')/g['slug']/(pid+'.jpg')
                        dst.parent.mkdir(parents=True,exist_ok=True);im.save(dst,quality=94)
                        url='./assets/portraits/'+g['slug']+'/'+pid+'.jpg'
                        reg[pid]={'url':url,'source':g['url'],'provider':'official','school':g['school'],'sha256':digest,'pdf_page':g['page']+1}
                        added.append({'id':pid,'name':t['names'][0],'url':url,'source':g['url']})
                    except Exception as e:errors[pid]=str(e)
        except Exception as e:errors[g['school']]=str(e)
    return added,errors
