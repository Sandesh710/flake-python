"""Seasonal ice dates and result downloads."""
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import json
import zipfile
import numpy as np
import pandas as pd


def _first_three(mask):
    if len(mask)<3:return None
    hits=np.flatnonzero(np.convolve(np.asarray(mask,dtype=int),np.ones(3,dtype=int),'valid')==3)
    return int(hits[0]) if len(hits) else None


def ice_dates(simulation):
    """Ice threshold 1 cm for three consecutive days; complete Sep–Jun winters."""
    d=simulation.daily.set_index('date')
    rows=[]
    for year in range(d.index.min().year,d.index.max().year+2):
        start,end=pd.Timestamp(year-1,9,1),pd.Timestamp(year,6,30)
        if start<d.index.min() or end>d.index.max():continue
        w=d.ice_thickness_m.reindex(pd.date_range(start,end))
        if w.notna().mean()<.98:continue
        ice=w.notna() & w.ge(.01);free=w.notna() & w.lt(.01)
        onset=ice.loc[:pd.Timestamp(year,3,31)]
        on=_first_three(onset)
        spring=ice.loc[pd.Timestamp(year,1,1):end]
        icy=np.flatnonzero(spring)
        if on is None or not len(icy):continue
        offset=int(icy[-1])+1
        breakup=free.loc[pd.Timestamp(year,1,1):end]
        off=_first_three(breakup.iloc[offset:])
        if off is None:continue
        a,b=onset.index[on],breakup.index[offset+off]
        rows.append({'Winter':f'{year-1}–{year}','Ice-on':a,'Ice-off':b,'Duration (days)':int((b-a).days)})
    return pd.DataFrame(rows,columns=['Winter','Ice-on','Ice-off','Duration (days)'])


def export_results(simulation,figures,folder=None):
    folder=Path(folder) if folder else Path.cwd()/'results'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    folder.mkdir(parents=True,exist_ok=False)
    simulation.daily.to_csv(folder/'daily_simulation.csv',index=False)
    ice_dates(simulation).to_csv(folder/'ice_dates.csv',index=False)
    (folder/'settings.json').write_text(json.dumps({'lake':asdict(simulation.lake),'options':asdict(simulation.options),
        'initialization':simulation.initialization,'final_state':simulation.final_state,
        'scenario':simulation.daily.attrs.get('scenario'),'forcing_model':simulation.daily.attrs.get('forcing_model')},indent=2))
    for name,figure in figures.items():
        figure.savefig(folder/(name+'.png'),dpi=300,bbox_inches='tight',facecolor='white')
        figure.savefig(folder/(name+'.pdf'),bbox_inches='tight',facecolor='white')
    archive=folder.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for f in folder.iterdir():z.write(f,f.name)
    return archive
