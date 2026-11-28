"""Extract labeled 2017 UCLA media roster portraits, using inspected page 5."""
import hashlib, io
import fitz
from PIL import Image
from audit_player_portraits import ROOT
from audit_ncaaw_school_portraits import get, norm
URL='https://s3.us-east-2.amazonaws.com/sidearm.nextgen.sites/uclabruins.com/documents/2017/8/31/UMD_GU_0901.pdf?timestamp=20170831101617'
ROWS=[
['Kevin Silva','Eirik Baekkelund','Alex Knox','Erik Holt','Brandon Terwege'],
['Andrew Paoli','Milan Iloski','Anderson Asiedu','Santiago Herrera','Brian Iloski'],
['Kike Poleo','Roman Martin','Eric Iloski','Christian Chavez','Robert Knights'],
['Blayne Martinez','Tobi Henneke','Joab Santoyo','Matthew Powell','Chase Bishoy'],
['Cole Martinez','Cameron Douglas','Malcolm Jones']]
# Coordinates measured on the official page screenshot, not inferred from faces.
XS=[(69,241),(263,435),(457,630),(651,824),(845,1018)]
YS=[(103,244),(301,442),(498,638),(692,833),(897,1038)]
def recover(reg,targets):
    wanted={norm(t['names'][0]):pid for pid,t in targets.items() if t['school']=='UCLA' and pid not in reg}
    added=[]
    if not wanted:return added
    response=get(URL);response.raise_for_status()
    doc=fitz.open(stream=response.content,filetype='pdf');page=doc[4]
    if 'radiotvroster' not in norm(page.get_text()):raise ValueError('Unexpected UCLA PDF page')
    root=ROOT/'college-soccer/assets/portraits/ucla';root.mkdir(parents=True,exist_ok=True)
    seen=set()
    for r,row in enumerate(ROWS):
        for c,name in enumerate(row):
            pid=wanted.get(norm(name))
            if not pid:continue
            x0,x1=XS[c];y0,y1=YS[r]
            rect=fitz.Rect((x0+2)*page.rect.width/1088,(y0+2)*page.rect.height/1408,(x1-2)*page.rect.width/1088,(y1-2)*page.rect.height/1408)
            # Confirm the printed player name occurs directly beneath this crop.
            labels=page.search_for(name)
            if not any(rect.x0-8<=l.x0<=rect.x1 and 0<=l.y0-rect.y1<=20 for l in labels):raise ValueError('Label alignment failed: '+name)
            pix=page.get_pixmap(matrix=fitz.Matrix(4,4),clip=rect,alpha=False)
            im=Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB');im.load()
            digest=hashlib.sha256(im.tobytes()).hexdigest()
            if digest in seen or min(im.size)<100:raise ValueError('Invalid or duplicate portrait '+name)
            seen.add(digest);im.thumbnail((500,500))
            filename=pid+'.jpg';im.save(root/filename,quality=93)
            record={'url':'./assets/portraits/ucla/'+filename,'source':URL,'provider':'official','school':'UCLA','source_page':5,'sha256':digest}
            reg[pid]=record;added.append({'id':pid,'name':name,**record})
    return added
