#!/usr/bin/env python3
"""Gráficos SVG autónomos para un perfil GitHub; sin dependencias externas de Python.

Uso local: python scripts/actualizar_estadisticas.py --offline
Uso en Actions: python scripts/actualizar_estadisticas.py

Los gráficos de repositorios usan lenguaje PRINCIPAL (un voto/repositorio),
y el gráfico de código suma los bytes de GitHub Linguist por cada repositorio público.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
USER = os.environ.get('GH_USERNAME', 'paulbellido0990')
TOKEN = os.environ.get('GH_TOKEN', '')

PALETTE = ['#9CCFC3','#B7B2E8','#93C9E1','#E9A8C3','#E9D19A','#ADB7CF','#D3AACF','#B2D5A3']
INK = '#334155'
SOFT = '#64748B'
BG = '#FAFBFE'
CARD = '#FFFFFF'

AREAS = {
    'sneakerhub': 'Aplicaciones y producto',
    'SneakerStore': 'Aplicaciones y producto',
    'agente_personal': 'Aplicaciones y producto',
    'blossom-escritorio': 'Aplicaciones y producto',
    'Labo4_Arqui_Hexagonal': 'Arquitectura y Java',
    'Labo5_arqu': 'Arquitectura y Java',
    'Labo03-Arquitectura-Software': 'Arquitectura y Java',
    'Labo03_arqui_limpia': 'Arquitectura y Java',
    'laboratorio-01-pruebas': 'Pruebas de software',
    'laboratorio-5-pruebas': 'Pruebas de software',
    'laboratorio-pruebas-s6': 'Pruebas de software',
    'IS484-Practica001-Lunes-Llallahui-Bellido': 'Jupyter y análisis',
    'IS484-Labo001-Lunes-Llallahui-Bellido': 'Jupyter y análisis',
    'IS484-Semana002-Lunes-Llallahui': 'Jupyter y análisis',
    'TallerGit': 'Git y perfil',
    'TallerGit-Compartido': 'Git y perfil',
    'paulbellido0990': 'Git y perfil',
}
OFFLINE = [
    ('Labo4_Arqui_Hexagonal','Java'),
    ('IS484-Practica001-Lunes-Llallahui-Bellido','Jupyter Notebook'),
    ('laboratorio-01-pruebas',None),
    ('TallerGit-Compartido',None),
    ('IS484-Labo001-Lunes-Llallahui-Bellido','Jupyter Notebook'),
    ('blossom-escritorio','Python'),
    ('agente_personal','JavaScript'),
    ('Labo5_arqu','Java'),
    ('laboratorio-5-pruebas','Python'),
    ('IS484-Semana002-Lunes-Llallahui','Jupyter Notebook'),
    ('Labo03-Arquitectura-Software','Java'),
    ('paulbellido0990',None),
    ('laboratorio-pruebas-s6','Python'),
    ('SneakerStore','TypeScript'),
    ('TallerGit',None),
    ('Labo03_arqui_limpia','Java'),
    ('sneakerhub','Python'),
]

def api_json(url: str):
    headers={'Accept':'application/vnd.github+json','User-Agent':'PaulBellido-Profile-SVG/1.0',
             'X-GitHub-Api-Version':'2022-11-28'}
    if TOKEN:
        headers['Authorization']='Bearer '+TOKEN
    with urlopen(Request(url,headers=headers),timeout=30) as resp:
        return json.load(resp)

def fetch_public_repositories():
    repos=[]
    for page in range(1,11):
        data=api_json(f'https://api.github.com/users/{USER}/repos?type=owner&sort=updated&per_page=100&page={page}')
        if not isinstance(data,list):
            raise RuntimeError('GitHub API returned an unexpected repos format')
        repos.extend(r for r in data if not r.get('private'))
        if len(data)<100:
            break
    else:
        raise RuntimeError('More than 1,000 repos: increase pagination support')
    if not repos:
        raise RuntimeError('GitHub API did not return any public repositories')
    return repos

def make_data(offline=False):
    if offline:
        repos=[{'name':n,'language':l} for n,l in OFFLINE]
        bytes_map=None
        asof='30/10/2026 · datos públicos verificados'
    else:
        repos=fetch_public_repositories()
        bytes_map=Counter()
        for r in repos:
            # GitHub Linguist values = classified bytes, not lines or commits.
            langs=api_json(f'https://api.github.com/repos/{USER}/{r["name"]}/languages')
            if not isinstance(langs,dict):
                raise RuntimeError(f'Invalid languages object for {r["name"]}')
            bytes_map.update({k:int(v) for k,v in langs.items()})
        asof=datetime.now(timezone.utc).strftime('%d/%m/%Y · actualización UTC')
    main=Counter(r['language'] for r in repos if r.get('language'))
    areas=Counter(AREAS.get(r['name'],'Otros proyectos') for r in repos)
    return repos, main, areas, bytes_map, asof

def e(s): return escape(str(s), quote=True)

def rect(x,y,w,h,fill,rx=14,stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" />'

def label(x,y,s,size=18,color=INK,weight=500,anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="Segoe UI, Arial, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{e(s)}</text>'

def panel(title,subtitle,body,h=360,meta=None):
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{h}" viewBox="0 0 1080 {h}" role="img" aria-label="{e(title)}">',
         '<defs><linearGradient id="wash" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#F5F2FD"/><stop offset="49%" stop-color="#F4FBFA"/><stop offset="100%" stop-color="#FFF5F7"/></linearGradient></defs>',
         rect(0,0,1080,h,'url(#wash)',28),
         rect(32,34,7,37,PALETTE[0],3),
         label(56,61,title,30,INK,700),label(56,88,subtitle,15,SOFT,400)]
    svg+=body
    if meta:svg.append(label(56,h-25,meta,13,SOFT,400))
    svg.append('</svg>')
    return '\n'.join(svg)+'\n'

def graph_stats(repos,main,areas,asof):
    items=[('REPOSITORIOS',str(len(repos)),'Públicos en GitHub',PALETTE[0]),
           ('CON LENGUAJE',str(sum(main.values())),'Clasificación principal',PALETTE[1]),
           ('TECNOLOGÍAS',str(len(main)),'Categorías principales',PALETTE[2]),
           ('ÁREAS',str(len(areas)),'Campos de proyectos',PALETTE[3])]
    body=[]
    for i,(head,value,desc,color) in enumerate(items):
        x=38+i*261
        body.extend([rect(x,119,239,132,CARD,20,'#E7EAF1'),rect(x+18,139,38,6,color,3),
                     label(x+20,174,head,13,SOFT,700),label(x+20,222,value,42,INK,750),
                     label(x+120,222,desc,12,SOFT,500)])
    return panel('Panorama de mi GitHub','Resumen verificable de mis repositorios públicos',body,293,asof)

def graph_bars(main,asof):
    values=sorted(main.items(), key=lambda p:(-p[1],p[0]))
    total=sum(main.values()) or 1
    n=len(values)
    h=max(280,155+n*55)
    body=[]
    for i,(name,qty) in enumerate(values):
        y=127+i*55
        p=qty/total
        color=PALETTE[i%len(PALETTE)]
        body.extend([label(58,y,name,16,INK,600),
            rect(332,y-19,525,19,'#E9EDF4',9),
            rect(332,y-19,round(525*p,1),19,color,9),
            label(877,y,f'{p*100:.1f}%  ·  {qty}',17,INK,650)])
    return panel('Lenguajes principales','Porcentaje de repositorios clasificados; no equivale a líneas de código',body,h,asof)

def graph_areas(areas,asof):
    vals=sorted(areas.items(), key=lambda x:(-x[1],x[0]))
    total=sum(areas.values()) or 1
    body=[]
    x=55
    for i,(name,qty) in enumerate(vals):
        w=round(955*qty/total,2)
        body.append(rect(x,129,w,34,PALETTE[i%len(PALETTE)],7))
        x+=w
    for i,(name,qty) in enumerate(vals):
        row=i//2;col=i%2
        x=58+col*496;y=203+row*59
        body.extend([rect(x,y-18,21,21,PALETTE[i%len(PALETTE)],5),label(x+33,y,name,16,INK,600),label(x+432,y,str(qty),17,INK,750)])
    h=240+((len(vals)+1)//2)*59
    return panel('Mapa de proyectos','Áreas de trabajo según los repositorios públicos',body,h,asof)

def graph_code(bytes_map,asof):
    if bytes_map is None:
        body=[rect(44,120,990,210,'#FFFFFF',20,'#E9DDEF'),
              label(540,179,'Distribución de código por lenguaje',24,INK,700,'middle'),
              label(540,217,'Pendiente del primer cálculo desde la API oficial de GitHub',18,SOFT,400,'middle'),
              label(540,256,'Actions → Actualizar estadísticas del perfil → Run workflow',16,'#886FBA',650,'middle'),
              label(540,292,'El gráfico usará bytes clasificados por GitHub Linguist',15,SOFT,400,'middle')]
        return panel('Composición del código','Diferente del porcentaje por repositorios',body,375,'Se actualiza tras ejecutar el workflow')
    totals=sum(bytes_map.values())
    if totals<=0:
        return panel('Composición del código','Todavía no hay bytes reconocidos por GitHub Linguist',[],210,asof)
    items=sorted(bytes_map.items(),key=lambda x:-x[1])
    values=items[:6]
    rest=sum(v for _,v in items[6:]);
    if rest:values.append(('Otros',rest))
    h=max(310,170+len(values)*49)
    body=[]
    for i,(name,qty) in enumerate(values):
        y=128+i*49
        part=qty/totals
        body.extend([label(58,y,name,15,INK,600),rect(330,y-18,520,16,'#E9EDF4',8),
            rect(330,y-18,round(520*part,1),16,PALETTE[i%len(PALETTE)],8),
            label(873,y,f'{100*part:.1f}%',17,INK,650)])
    return panel('Composición del código','Proporción de bytes por lenguaje, medida por GitHub Linguist',body,h,f'{asof}  ·  {totals:,} bytes clasificados')

def update_table(main):
    path=ROOT/'README.md'
    readme=path.read_text(encoding='utf-8')
    total=sum(main.values())
    lines=['<!-- LANG_TABLE_START -->','| Lenguaje principal | Repositorios | Participación |',
           '|:--|--:|--:|']
    for lang,count in sorted(main.items(),key=lambda x:(-x[1],x[0])):
        lines.append(f'| {lang} | {count} | **{100*count/total:.1f} %** |')
    lines.append(f'| **Total identificado** | **{total}** | **100 %** |')
    lines.append('<!-- LANG_TABLE_END -->')
    result='\n'.join(lines)
    import re
    newer,n=re.subn(r'<!-- LANG_TABLE_START -->[\s\S]*?<!-- LANG_TABLE_END -->',lambda m:result,readme,count=1)
    if n!=1:raise RuntimeError('Missing language table markers in README.md')
    if newer!=readme:path.write_text(newer,encoding='utf-8')

def main():
    offline='--offline' in sys.argv
    repos, main_l, areas, bytes_map, asof=make_data(offline)
    (ROOT/'estadisticas.svg').write_text(graph_stats(repos,main_l,areas,asof),encoding='utf-8')
    (ROOT/'lenguajes.svg').write_text(graph_bars(main_l,asof),encoding='utf-8')
    (ROOT/'proyectos.svg').write_text(graph_areas(areas,asof),encoding='utf-8')
    (ROOT/'codigo.svg').write_text(graph_code(bytes_map,asof),encoding='utf-8')
    update_table(main_l)
    print(f'Generados 4 SVG. Repos: {len(repos)}. Con lenguaje: {sum(main_l.values())}. Offline: {offline}')

if __name__=='__main__':main()
