#!/usr/bin/env python3
"""Render a matching A7 memory card and its actual-size A4 cutting sheet."""
import argparse,json,re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from pypdf import PdfReader,PdfWriter,Transformation

ASSETS=Path(__file__).resolve().parents[1]/'assets'
W,H=74*mm,105*mm
M=9

def wrap(s,font,size,width):
    result=[];line=''
    for word in s.split():
        if pdfmetrics.stringWidth(word,font,size)>width:
            raise ValueError('Word too wide: '+word)
        proposed=(line+' '+word).strip()
        if line and pdfmetrics.stringWidth(proposed,font,size)>width:
            result.append(line);line=word
        else:line=proposed
    if line:result.append(line)
    return result

def render(spec,directory,stem):
    pdfmetrics.registerFont(TTFont('FM',str(ASSETS/'fm-sans-regular.ttf')))
    pdfmetrics.registerFont(TTFont('FM-Bold',str(ASSETS/'fm-sans-bold.ttf')))
    entries=spec['entries']
    if not entries or not spec['title'].strip():raise ValueError('Title and entries required')
    content_count=sum('section' not in e for e in entries)
    if not content_count:raise ValueError('At least one content row required')
    layout=None
    for body in (9,8.8,8.5,8.2,8,7.8,7.5):
        heading=body+1.7;lead=body*1.16;planned=[]
        try:
            for e in entries:
                if 'section' in e:
                    if pdfmetrics.stringWidth(e['section'].upper(),'FM-Bold',8)>W-2*M-8:
                        raise ValueError('Section title too wide')
                    planned.append((e,[],11,0));continue
                label=str(e.get('label',''))
                if pdfmetrics.stringWidth(label,'FM-Bold',20)>24:raise ValueError('Use a shorter label')
                x=M+28 if label else M+4
                title=e.get('title','')
                if title and pdfmetrics.stringWidth(title,'FM-Bold',heading)>W-M-x-3:
                    raise ValueError('Row title too wide')
                raw=e.get('lines',[])
                if not raw or not all(isinstance(t,str) and t.strip() for t in raw):raise ValueError('Rows require text')
                ss=[t for s in raw for t in wrap(s,'FM',body,W-M-x-3)]
                block=(heading+4 if title else 0)+body+(len(ss)-1)*lead
                planned.append((e,ss,block+(9 if title else 6),block))
        except ValueError:
            continue
        needed=sum(p[2] for p in planned);available=H-46-M
        if needed<=available:
            extra=(available-needed)/content_count
            layout=(body,heading,lead,[(e,ss,rh+(extra if 'section' not in e else 0),block) for e,ss,rh,block in planned]);break
    if layout is None:raise ValueError('Content cannot fit legibly on one A7 page; shorten it without omitting required points')
    body,heading,lead,planned=layout
    directory.mkdir(parents=True,exist_ok=True)
    card=directory/(stem+'-a7.pdf');sheet=directory/(stem+'-a4-klipp.pdf')
    c=canvas.Canvas(str(card),pagesize=(W,H));c.setTitle(spec['title']+' - A7 minneskort')
    if spec.get('source'):c.setSubject(spec['source'])
    def text(x,y,s,size,font='FM'):
        c.setFillGray(0);c.setFont(font,size);c.drawString(x,y,s)
    d=svg2rlg(str(ASSETS/'hemvarnet-black.svg'));scale=36/d.height;d.scale(scale,scale)
    renderPDF.draw(d,c,W-M-30+(30-d.width*scale)/2,H-43)
    title_size=21
    while pdfmetrics.stringWidth(spec['title'],'FM-Bold',title_size)>W-2*M-36:
        title_size-=.5
        if title_size<12:raise ValueError('Shorten the card title')
    text(M,H-23,spec['title'],title_size,'FM-Bold')
    subtitle=spec.get('subtitle','MINNESKORT • HEMVÄRNET')
    if pdfmetrics.stringWidth(subtitle,'FM-Bold',7)>W-2*M-35:raise ValueError('Shorten subtitle')
    text(M,H-36,subtitle,7,'FM-Bold')
    y=H-46;index=0
    for e,ss,rh,block in planned:
        if 'section' in e:
            c.setFillGray(0);c.rect(M,y-rh,W-2*M,rh,fill=1,stroke=0)
            c.setFillGray(1);c.setFont('FM-Bold',8);c.drawString(M+4,y-9,e['section'].upper());y-=rh;continue
        if index%2==0:
            c.setFillGray(.92);c.rect(M,y-rh,W-2*M,rh,fill=1,stroke=0)
        c.setStrokeGray(.4);c.setLineWidth(.45);c.line(M,y,W-M,y)
        label=str(e.get('label',''));x=M+28 if label else M+4
        top=y-(rh-block)/2
        title=e.get('title','')
        if title:
            text(x,top-heading,title,heading,'FM-Bold');baseline=top-heading-4-body
        else:baseline=top-body
        for j,s in enumerate(ss):text(x,baseline-j*lead,s,body)
        if label:
            # Center visible capitals/numerals beside the entire text block.
            label_size=20 if title else 10
            cap=pdfmetrics.getFont('FM-Bold').face.capHeight*label_size/1000
            bottom=baseline-(len(ss)-1)*lead
            visible_top=top-1
            center=(visible_top+bottom)/2
            text(M+13-pdfmetrics.stringWidth(label,'FM-Bold',label_size)/2,center-cap/2,label,label_size,'FM-Bold')
        y-=rh;index+=1
    c.setStrokeGray(.4);c.setLineWidth(.45);c.line(M,y,W-M,y)
    c.showPage();c.save()
    # Draw print furniture directly onto a vector A4 page.
    import io
    overlay=io.BytesIO();c=canvas.Canvas(overlay,pagesize=A4)
    aw,ah=A4;px=(aw-W)/2;py=(ah-H)/2
    c.setFont('FM',12);c.drawCentredString(aw/2,py+H+18*mm,spec['title']+' • A7 MINNESKORT')
    c.setLineWidth(.7);c.rect(px,py,W,H)
    c.setFont('FM',10)
    for i,s in enumerate(['Skriv ut i 100 % / faktisk storlek.','Klipp längs den heldragna ytterkanten.','Laminera kortet.']):c.drawCentredString(aw/2,py-12*mm-i*6*mm,s)
    yy=py-36*mm;c.setLineWidth(.5);c.line(px,yy,px+50*mm,yy)
    for xx in (px,px+50*mm):c.line(xx,yy-mm,xx,yy+mm)
    c.setFont('FM',8);c.drawString(px,yy-5*mm,'Kontrollmått: 50 mm')
    c.showPage();c.save();overlay.seek(0)
    writer=PdfWriter();page=writer.add_blank_page(aw,ah)
    page.merge_transformed_page(PdfReader(str(card)).pages[0],Transformation().translate(px,py))
    page.merge_page(PdfReader(overlay).pages[0]);writer.add_metadata({'/Title':spec['title']+' - A4 klippversion'})
    with sheet.open('wb') as f:writer.write(f)
    for file,size in ((card,(W,H)),(sheet,A4)):
        reader=PdfReader(str(file));assert len(reader.pages)==1
        box=reader.pages[0].mediabox
        assert abs(float(box.width)-size[0])<.01 and abs(float(box.height)-size[1])<.01
        assert spec['title'] in reader.pages[0].extract_text()
    return card,sheet

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--stem',required=True);a=p.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*',a.stem):p.error('stem must use lowercase letters, numbers and hyphens')
    result=render(json.loads(a.input.read_text(encoding='utf-8')),a.output_dir,a.stem)
    for path in result:print(path.resolve())
