#!/usr/bin/env python3
"""Micro-DRC de escapes verticales U_EFUSE.5/.6 sin alterar el PCB persistido."""
from __future__ import annotations
import json, subprocess, tempfile
from pathlib import Path
from collections import Counter
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
VARIANTS={
  'RAW_UP': [('12V_IN_RAW',(177.525,17.975),(177.525,14.0),0.25)],
  'RAW_DOWN': [('12V_IN_RAW',(177.525,17.975),(177.525,21.5),0.25)],
  'PROT_UP': [('12V_PROTECTED',(178.025,17.975),(178.025,14.0),0.25)],
  'PROT_DOWN': [('12V_PROTECTED',(178.025,17.975),(178.025,21.5),0.25)],
  'OUTWARD': [
      ('12V_IN_RAW',(177.525,17.975),(177.525,14.0),0.25),
      ('12V_PROTECTED',(178.025,17.975),(178.025,21.5),0.25),
  ],
  'SWAPPED': [
      ('12V_IN_RAW',(177.525,17.975),(177.525,21.5),0.25),
      ('12V_PROTECTED',(178.025,17.975),(178.025,14.0),0.25),
  ],
}

def iu(x): return pcbnew.FromMM(float(x))
def V(x,y): return pcbnew.VECTOR2I(iu(x),iu(y))

def netinfo(board):
    d={}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname(): d.setdefault(p.GetNetname(),p.GetNet())
    return d

def add(board,nets,net,a,z,w):
    t=pcbnew.PCB_TRACK(board); t.SetNet(nets[net]); t.SetLayer(pcbnew.F_Cu); t.SetWidth(iu(w)); t.SetStart(V(*a)); t.SetEnd(V(*z)); board.Add(t)

def main():
    results={}
    with tempfile.TemporaryDirectory(prefix='pr20a_efuse_') as td:
        td=Path(td)
        for name,tracks in VARIANTS.items():
            b=pcbnew.LoadBoard(str(PCB)); nets=netinfo(b)
            for net,a,z,w in tracks: add(b,nets,net,a,z,w)
            p=td/f'{name}.kicad_pcb'; r=td/f'{name}.json'; pcbnew.SaveBoard(str(p),b)
            cp=subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],text=True,capture_output=True)
            if not r.exists():
                results[name]={'cli_rc':cp.returncode,'fatal':cp.stderr[-1000:]}; continue
            d=json.loads(r.read_text(encoding='utf-8'))
            errs=[v for v in d.get('violations',[]) if v.get('severity')=='error']
            results[name]={
                'cli_rc':cp.returncode,
                'errors':len(errs),
                'error_types':dict(Counter(str(v.get('type','?')) for v in errs)),
                'warnings':sum(v.get('severity')=='warning' for v in d.get('violations',[])),
                'unconnected':len(d.get('unconnected_items',[])),
                'first_errors':errs[:6],
            }
    print('EFUSE_ESCAPE_DRC_BEGIN')
    print(json.dumps(results,ensure_ascii=False,separators=(',',':')))
    print('EFUSE_ESCAPE_DRC_END')
    good=[k for k,v in results.items() if v.get('errors')==0]
    print('EFUSE_ESCAPE_GOOD',good)
    if not good: raise SystemExit('ERROR: ninguna variante de escape eFuse quedó DRC=0')

if __name__=='__main__': main()
