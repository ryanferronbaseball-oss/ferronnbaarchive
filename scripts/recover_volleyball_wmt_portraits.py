"""Recovery for WMT roster data and clearly labelled PDF portrait grids."""
import json, re, io, hashlib
from pathlib import Path
from urllib.parse import urljoin
from PIL import Image, ImageStat
import fitz
from audit_ncaaw_school_portraits import norm, allowed, clean, attrs, get, verify

def wmt_images(soup,page,names,school):
    ns={norm(n) for n in names};out=[]
    def add(u):
        if isinstance(u,str):
            u=urljoin(page,u)
            if allowed(u,school) and clean(u) and re.search(r'\.(?:png|jpe?g|webp)(?:[?#]|$)|storage\.googleapis\.com/|wmt\.digital/',u,re.I):out.append(u)
    # An exact-name player record, not a general team or article record.
    def images(v):
        if isinstance(v,str):add(v)
        elif isinstance(v,list):
            for x in v:images(x)
        elif isinstance(v,dict):
            for k,x in v.items():
                if k.lower() in ('url','src','path','original','originalurl','imageurl','image','file','sizes','variants','asset','webp','large','medium','small'):images(x)
    def walk(v):
        if isinstance(v,list):
            for x in v:walk(x)
        elif isinstance(v,dict):
            fields={str(k).lower().replace('_',''):x for k,x in v.items()}
            labels=[fields.get(k,'') for k in ('name','fullname','displayname','playername','athletename','title')]
            labels.append(str(fields.get('firstname',''))+' '+str(fields.get('lastname','')))
            if any(isinstance(n,str) and norm(n) in ns for n in labels):
                for k,x in fields.items():
                    if re.search(r'headshot|portrait|profileimage|rosterimage|playerimage|athleteimage|^image$|^photo$|^imageurl$|^photourl$',k):images(x)
            for x in v.values():walk(x)
    for script in soup.find_all('script'):
        s=script.string or script.get_text()
        if not s or len(s)>15000000:continue
        if not any(n in norm(s) for n in ns):continue
        try:walk(json.loads(s))
        except (ValueError,RecursionError):
            # JSON assignment payloads such as window.__INITIAL_STATE__.
            match=re.search(r'(?:__INITIAL_STATE__|__NEXT_DATA__|__NUXT__|__APOLLO_STATE__)\s*=\s*',s)
            if match:
                try:walk(json.JSONDecoder().raw_decode(s[match.end():])[0])
                except (ValueError,RecursionError):pass
    # WMT card: an exact named link/heading and one image within its local card.
    for tag in soup.find_all(['a','h2','h3','h4','span']):
        if norm(tag.get_text(' ',strip=True)) not in ns:continue
        node=tag
        for _ in range(5):
            if not node:break
            cls=' '.join(node.get('class',[])).lower()
            if re.search(r'roster|athlete|player|card',cls) and not re.search(r'grid|list|wrapper|container',cls):
                imgs=node.find_all('img')
                if len(imgs)==1:
                    for u in attrs(imgs[0],page,school):add(u)
                    for a in ('data-src','src','data-lazy-src'):
                        add(imgs[0].get(a))
                    break
            node=node.parent
    # Individual bio: only image URLs containing the verified player's complete name.
    if '/player/' in page:
        for im in soup.find_all('img'):
            for u in attrs(im,page,school):
                if any(n in norm(u) for n in ns):add(u)
        for m in soup.find_all('meta',attrs={'property':'og:image'}):
            u=m.get('content','')
            if any(n in norm(u) for n in ns):add(u)
    return list(dict.fromkeys(out))

def recover_nebraska_grid(reg,targets):
    added=[];errors={}
    sources=[
      'https://sidearm.nextgen.sites.s3.us-east-2.amazonaws.com/huskers.com/documents/2019/9/11/Ameritas_Players_Challenge.pdf',
      'https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites/huskers.com/documents/2019/9/11/Ameritas_Players_Challenge.pdf',
      'https://sidearm.nextgen.sites.s3.us-east-2.amazonaws.com/huskers.com/documents/2021/9/6/9_8_21_at_Creighton.pdf']
    for url in sources:
        if all(pid in reg for pid,t in targets.items() if t['school']=='Nebraska'):break
        try:
            r=get(url);r.raise_for_status()
            with fitz.open(stream=r.content,filetype='pdf') as doc:
                for page in doc:
                    text=page.get_text()
                    if 'NEBRASKA VOLLEYBALL' not in text.upper():continue
                    # Require four or more exact player labels and at least eight
                    # similarly sized portrait image rectangles on a roster-grid page.
                    labels={}
                    for pid,t in targets.items():
                        if t['school']!='Nebraska':continue
                        hits=page.search_for(t['names'][0])
                        if len(hits)==1:labels[pid]=hits[0]
                    if len(labels)<4:continue
                    rects=[fitz.Rect(x['bbox']) for x in page.get_image_info() if x['width']>=70 and x['height']>=70]
                    rects=[z for z in rects if 35<=z.width<=160 and 40<=z.height<=190 and .55<=z.width/z.height<=1.15]
                    if len(rects)<8:continue
                    choices={}
                    for pid,label in labels.items():
                        opts=[]
                        for z in rects:
                            gap=label.y0-z.y1
                            if -2<=gap<=26 and z.x0-8<=label.x0 and label.x1<=z.x1+8:
                                opts.append(z)
                        if len(opts)==1:choices[pid]=opts[0]
                    if len(choices)<4:continue
                    if len({tuple(z) for z in choices.values()})!=len(choices):continue
                    for pid,z in choices.items():
                        if pid in reg:continue
                        pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=z,alpha=False)
                        im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
                        if min(im.size)<120 or max(ImageStat.Stat(im).stddev)<8:continue
                        digest=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
                        if any(v.get('sha256')==digest for v in reg.values()):continue
                        path=Path('college-volleyball/assets/portraits/nebraska')/(pid+'.jpg')
                        path.parent.mkdir(parents=True,exist_ok=True);im.save(path,quality=94)
                        dest='./assets/portraits/nebraska/'+pid+'.jpg'
                        reg[pid]={'url':dest,'source':url,'provider':'official','school':'Nebraska','sha256':digest,'pdf_page':page.number+1}
                        added.append({'id':pid,'name':targets[pid]['names'][0],'url':dest,'source':url})
        except Exception as ex:errors[url]=str(ex)
    return added,errors
