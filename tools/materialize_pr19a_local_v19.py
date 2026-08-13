#!/usr/bin/env python3
"""PR19A v19: aplica micro-rutas declaradas en hardware/pr19a_route_overrides_v19.json."""
from __future__ import annotations
import json
from pathlib import Path
import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v17 as v17
import pr19a_router_core as base

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'hardware/pr19a_route_overrides_v19.json').read_text(encoding='utf-8'))
ROUTES=DATA['routes']

def key(e): return str(e.get('ref')),str(e.get('pad'))
def rkey(net,a,b): return net,frozenset((key(a),key(b)))
INDEX={(r['net'],frozenset(tuple(x) for x in r['endpoints'])):r for r in ROUTES}

class RouterPR19AV19(v17.RouterPR19AV17):
    def _override(self,net,a,b): return INDEX.get(rkey(net,a,b))
    def _special(self,net,a,b):
        r=self._override(net,a,b)
        return 'V19:'+r['id'] if r else super()._special(net,a,b)
    def _astar(self,net,cls,a,b,xmin,xmax):
        if self._override(net,a,b): return [(0,0,pcbnew.F_Cu)]
        return super()._astar(net,cls,a,b,xmin,xmax)
    def _materialize_path(self,net,cls,ci,path,a,b):
        r=self._override(net,a,b)
        if not r: return super()._materialize_path(net,cls,ci,path,a,b)
        start_key=tuple(r['start'])
        s,e=(a,b) if key(a)==start_key else (b,a)
        w=float(ci['track_width_mm_min'])
        def pt(x):
            if x=='START': return (float(s['x_mm']),float(s['y_mm']))
            if x=='END': return (float(e['x_mm']),float(e['y_mm']))
            return (float(x[0]),float(x[1]))
        for op in r['ops']:
            if 'via' in op:
                p=pt(op['via'])
                self._add_via(net,ci,base.gcoord(p[0]),base.gcoord(p[1]))
                continue
            layer=pcbnew.F_Cu if op['track']=='F.Cu' else pcbnew.B_Cu
            points=[pt(x) for x in op['points']]
            for p,q in zip(points,points[1:]):
                self._track(net,layer,w,p,q)
        print('V19_OVERRIDE',r['id'])

impl.RouterPR19A=RouterPR19AV19
if __name__=='__main__': raise SystemExit(impl.main())
