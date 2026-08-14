#!/usr/bin/env python3
"""PR19C v5: compresión geométrica correcta + micro-escape GNSS SCL.

Corrige un defecto del tooling que convertía una recta de rejilla en múltiples
segmentos. Añade un único escape determinista para D_GNSS_SCL.1, cuyo pad GND
adyacente bloquea la salida directa hacia +X. No cambia reglas DRC.
"""
from __future__ import annotations

import json
import math
import pcbnew  # type: ignore

import materialize_pr19c_digital as core
import materialize_pr19c_digital_v4 as v4

CANDIDATE_REVISION = 'v5-compression-fix-gnss-scl-escape-active'


def grid_path(points: list[tuple[float,float]], layer: int) -> list[tuple[int,int,int,int]]:
    out=[]
    for a,b in zip(points,points[1:]):
        ax,ay=core.gcoord(a[0]),core.gcoord(a[1]); bx,by=core.gcoord(b[0]),core.gcoord(b[1])
        if ax!=bx and ay!=by: core.fail(f'micro-route no ortogonal: {a}->{b}')
        dx=0 if ax==bx else (1 if bx>ax else -1); dy=0 if ay==by else (1 if by>ay else -1)
        if not out: out.append((ax,ay,layer,-1))
        x,y=ax,ay
        while (x,y)!=(bx,by):
            x+=dx; y+=dy
            ndir=0 if dx>0 else 1 if dx<0 else 2 if dy>0 else 3
            out.append((x,y,layer,ndir))
    return out


class RouterV5(v4.RouterV4):
    def _astar(self, net: str, a: dict, z: dict):
        refs={a['ref'],z['ref']}
        if net=='I2C_SCL' and refs=={'D_GNSS_SCL','R_I2C_SCL'}:
            d=a if a['ref']=='D_GNSS_SCL' else z; r=z if z['ref']=='R_I2C_SCL' else a
            pts=[(d['x_mm'],d['y_mm']),(133.75,17.00),(133.75,15.75),(141.00,15.75),(141.00,17.00),(r['x_mm'],r['y_mm'])]
            p=grid_path(pts,pcbnew.F_Cu)
            return p if a['ref']=='D_GNSS_SCL' else list(reversed(p))
        return super()._astar(net,a,z)

    def _materialize(self, net: str, path, a: dict, z: dict):
        clsinfo=self.class_info[self.class_by_net[net]]; width=float(clsinfo['track_width_mm_min'])
        before_s=len(self.new_segments); before_v=len(self.new_vias); bends=0; length=0.0
        sx,sy,sl,_=path[0]; gx,gy,gl,_=path[-1]
        def add(layer,p0,p1):
            nonlocal length
            if abs(p0[0]-p1[0])<1e-9 and abs(p0[1]-p1[1])<1e-9: return
            self._add_track(net,layer,width,p0,p1); self._mark_track_cells(self.track_occ,net,layer,p0,p1,halo=1)
            length += math.hypot(p1[0]-p0[0],p1[1]-p0[1])
        add(sl,(a['x_mm'],a['y_mm']),core.xy(sx,sy))
        run=0
        for i in range(1,len(path)+1):
            split=i==len(path) or path[i][2]!=path[i-1][2]
            if not split: continue
            layer=path[run][2]; pts=[(path[j][0],path[j][1]) for j in range(run,i)]
            if len(pts)>=2:
                keep=[pts[0]]
                for k in range(1,len(pts)-1):
                    prev=pts[k-1]; cur=pts[k]; nxt=pts[k+1]
                    if (cur[0]-prev[0],cur[1]-prev[1])==(nxt[0]-cur[0],nxt[1]-cur[1]): continue
                    keep.append(cur)
                keep.append(pts[-1]); bends += max(0,len(keep)-2)
                for p0,p1 in zip(keep,keep[1:]): add(layer,core.xy(*p0),core.xy(*p1))
            if i<len(path):
                ix,iy,_,_=path[i-1]; self._add_via(net,clsinfo,ix,iy); run=i
        add(gl,core.xy(gx,gy),(z['x_mm'],z['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,bends,length

    def route_all(self) -> dict:
        result=super().route_all(); result['candidate_revision']=CANDIDATE_REVISION
        result.setdefault('planner',{})['compression']='COLLINEAR_GRID_RUNS_FIXED'
        result['planner']['micro_escape_i2c_scl']='D_GNSS_SCL.1 -> y15.75 -> R_I2C_SCL.2'
        return result


def main() -> int:
    board=pcbnew.LoadBoard(str(core.PCB))
    try:
        if len(list(board.Zones()))!=0: core.fail('PR19C no parte de board con copper zones')
    except AttributeError: pass
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV5(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V5',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0


if __name__=='__main__': raise SystemExit(main())
