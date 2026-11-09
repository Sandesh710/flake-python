"""Historical observations for context, independent of the GCM realization."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from .inputs import ROOT
from .plotting import STYLE,_axis


def load_observations(lake_id,root=None):
    root=Path(root) if root else ROOT
    profiles=pd.read_csv(root/'data/observations/temperature_profiles.csv.gz',dtype={'lake_id':str},parse_dates=['date'])
    ice=pd.read_csv(root/'data/observations/ice_dates.csv.gz',dtype={'lake_id':str},parse_dates=['ice_on_date','ice_off_date'])
    key=str(lake_id).zfill(8)
    return profiles.loc[profiles.lake_id==key].copy(),ice.loc[ice.lake_id==key].copy()


def observation_summary(profiles,ice):
    return pd.DataFrame({'Historical observations':['Temperature profile dates','Ice-on winters','Ice-off winters'],
      'Available':[profiles.date.nunique(),int(ice.ice_on_date.notna().sum()),int(ice.ice_off_date.notna().sum())]})


def observed_profile_figure(profiles,date,lake_name):
    day=pd.Timestamp(date)
    g=profiles.loc[profiles.date==day]
    if g.empty:raise ValueError('Choose one of the available observed profile dates.')
    # Repeated observations at a depth are averaged for display only.
    g=g.groupby('depth_m',as_index=False).temperature_c.mean().sort_values('depth_m')
    with plt.rc_context(STYLE):
        fig,ax=plt.subplots(figsize=(5.2,6),constrained_layout=True)
        ax.plot(g.temperature_c,g.depth_m,'o-',c='#087e8b',lw=1.5,ms=5)
        ax.set(xlabel='Observed temperature (°C)',ylabel='Depth (m)')
        ax.invert_yaxis();ax.set_title(lake_name+'\n'+day.strftime('%d %B %Y'),loc='left')
        _axis(ax)
    return fig
