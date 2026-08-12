#!/usr/bin/env python3
from __future__ import annotations
import json,re,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STD=Path('/usr/share/kicad/footprints')
LOCAL=ROOT/'kicad/lib/nfb_footprints.pretty'
READINESS=json.loads((ROOT/'hardware/placement_readiness_contract.json').read_text(encoding='utf-8'))
ZONE_FILES={'Z1':ROOT/'hardware/z1_production_netlist.json','Z2':ROOT/'hardware/z2_production_netlist.json','Z3':ROOT/'hardware/power_production_netlist.json','Z4':ROOT/'hardware/z4_production_netlist.json'}
FIELD=[x['ref'] for x in READINESS['field_io_sequence_left_to_right']]
GAP=1.0; MARGIN=1.0; INTERNAL_GAP=0.8; Y_START=18.0; Y_MAX=67.0

def locate(fid):
    lib,name=fid.split(':',1)
    p=(LOCAL/(name+'.kicad_mod')) if lib=='NFB' else (STD/(lib+'.pretty')/(name+'.kicad_mod'))
    if not p.exists(): raise FileNotFoundError(f'{fid} -> {p}')
    return p

def bbox(text):
    pts=[]
    # Generic coordinates on F.CrtYd primitives; capture blocks then all xy/start/end/center points.
    # Most KiCad standard footprints use fp_line/fp_rect on F.CrtYd.
    for m in re.finditer(r'\((fp_line|fp_rect|fp_arc|fp_poly)\b.*?\(layer\s+"?F\.CrtYd"?\).*?\)',text,re.S):
        block=m.group(0)
        for xy in re.finditer(r'\((?:start|end|mid|center|xy)\s+([-.0-9]+)\s+([-.0-9]+)',block):
            pts.append((float(xy.group(1)),float(xy.group(2))))
    if not pts:
        # simpler line scan catches legacy syntax where layer occurs after graphics fields
        for line in text.splitlines():
            if 'F.CrtYd' in line:
                for xy in re.finditer(r'\((?:start|end|mid|center|xy)\s+([-.0-9]+)\s+([-.0-9]+)',line): pts.append((float(xy.group(1)),float(xy.group(2))))
    if not pts:
        # conservative fallback: pad centers + sizes
        for m in re.finditer(r'\(pad\s+"?[^")\s]+"?\s+[^\n]*?\(at\s+([-.0-9]+)\s+([-.0-9]+)(?:\s+[-.0-9]+)?\).*?\(size\s+([-.0-9]+)\s+([-.0-9]+)\)',text,re.S):
            x,y,sx,sy=map(float,m.groups()); pts.extend([(x-sx/2,y-sy/2),(x+sx/2,y+sy/2)])
    if not pts: raise ValueError('no bbox')
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return [min(xs),min(ys),max(xs),max(ys)]

def shelf_height(items,width):
    usable=width-2*MARGIN; x=0.0; rowh=0.0; total=0.0
    for item in items:
        w=item['w']+INTERNAL_GAP; h=item['h']+INTERNAL_GAP
        if w>usable+1e-9: return 1e9
        if x>0 and x+w>usable:
            total+=rowh; x=0; rowh=0
        x+=w; rowh=max(rowh,h)
    return total+rowh

def main():
    zones={z:json.loads(p.read_text(encoding='utf-8')) for z,p in ZONE_FILES.items()}
    refinfo={}
    for z,d in zones.items():
        for c in d['components']:
            p=locate(c['footprint']); b=bbox(p.read_text(encoding='utf-8',errors='replace'))
            refinfo[c['ref']]={'zone':z,'footprint':c['footprint'],'bbox':b,'w':b[2]-b[0],'h':b[3]-b[1]}
    result={'schema_version':1,'source':'KiCad 10.0.5 standard footprints + NFB local footprints','field_gap_mm':GAP,'zones':{},'field_sequence':[]}
    current=READINESS['zone_guides']
    for ref in FIELD:
        i=refinfo[ref]; result['field_sequence'].append({'ref':ref,**i})
    total=53.34
    for z in ['Z1','Z2','Z3','Z4']:
        fieldrefs=[r for r in FIELD if refinfo[r]['zone']==z]
        field_required=2*MARGIN+sum(refinfo[r]['w'] for r in fieldrefs)+GAP*max(0,len(fieldrefs)-1)
        internal=[{'ref':r,**i} for r,i in refinfo.items() if i['zone']==z and r not in FIELD]
        # Preserve JSON order to preserve functional grouping.
        order=[c['ref'] for c in zones[z]['components'] if c['ref'] not in FIELD]
        by={x['ref']:x for x in internal}; internal=[by[r] for r in order]
        curw=float(current[z]['x_max'])-float(current[z]['x_min'])
        width=max(curw,math.ceil(field_required*2)/2)
        while shelf_height(internal,width)>Y_MAX-Y_START and width<100:
            width+=1.0
        h=shelf_height(internal,width)
        if h>Y_MAX-Y_START: raise SystemExit(f'{z} cannot fit under 100mm width')
        width=math.ceil(width*2)/2
        result['zones'][z]={'current_width_mm':curw,'field_required_width_mm':field_required,'planned_width_mm':width,'internal_shelf_height_mm':h,'field_refs':fieldrefs,'internal_ref_count':len(internal)}
        total+=width
    result['planned_board_width_mm']=round(total,2)
    result['current_board_width_mm']=220.0
    out=ROOT/'hardware/placement_plan_probe.json'; out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(out.read_text(encoding='utf-8'))
if __name__=='__main__': main()
