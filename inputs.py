"""Read example data and validate a daily FLake meteorological table."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .configuration import Lake

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = ['date','shortwave_w_m2','longwave_w_m2','air_temperature_c',
                    'vapor_pressure_mb','wind_speed_m_s','snowfall_kg_m2_s','light_extinction_m_inv']


SCENARIO_LABELS={'historical':'Historical (1995–2014)','ssp126':'SSP1-2.6 (1995–2040)',
                 'ssp245':'SSP2-4.5 (1995–2040)','ssp370':'SSP3-7.0 (1995–2040)','ssp585':'SSP5-8.5 (1995–2040)'}


def example_settings(root=None):
    root=Path(root) if root else ROOT
    return json.loads((root/'example_settings.json').read_text())


def example_lakes(root=None):
    """Lake catalogue; exact stored floating-point parameters and IDs."""
    root=Path(root) if root else ROOT
    return pd.read_csv(root/'data/lakes.csv',dtype={'lake_id':str},float_precision='round_trip')


def load_example(lake_id=None,root=None,scenario='historical'):
    """Return lake, forcing and the state immediately before January 1995.

    Scenario runs share the historical forcing through December 2014, then
    continue with the selected SSP. No historical year is duplicated.
    """
    root=Path(root) if root else ROOT
    if scenario not in SCENARIO_LABELS:raise ValueError('Choose historical or one of the four SSPs.')
    lake_id=str(lake_id or example_settings(root)['default_lake_id']).zfill(8)
    rows=example_lakes(root).loc[lambda d:d.lake_id==lake_id]
    if len(rows)!=1:raise ValueError('Choose a lake ID from example_lakes().')
    r=rows.iloc[0]
    lake=Lake(name=str(r['name']),mean_depth_m=float(r.mean_depth_m),fetch_m=float(r.fetch_m),
              latitude=float(r.latitude),longitude=float(r.longitude),area_km2=float(r.area_km2),
              snow_retention=float(r.snow_retention),lake_id=lake_id,county=str(r.county),
              coriolis_s_inv=float(r.coriolis_s_inv))
    folder=root/'data'/lake_id
    meteo=pd.read_csv(folder/'historical.csv.gz',float_precision='round_trip',parse_dates=['date'])
    if scenario!='historical':
        future=pd.read_csv(folder/(scenario+'.csv.gz'),float_precision='round_trip',parse_dates=['date'])
        if meteo.date.iloc[-1]!=pd.Timestamp('2014-12-31') or future.date.iloc[0]!=pd.Timestamp('2015-01-01'):
            raise ValueError('Historical/future forcing boundary is inconsistent.')
        meteo=pd.concat([meteo,future],ignore_index=True)
    restart=json.loads((folder/'restart_1995.json').read_text())
    if meteo.date.iloc[0]!=pd.Timestamp(restart['valid_before_date']):
        raise ValueError('Restart date does not match the first forcing day.')
    meteo.attrs.update(scenario=scenario,forcing_model='GFDL-ESM4')
    return lake,meteo,restart['state']


def validate_meteorology(frame, options):
    """Accept daily Gregorian or noleap data without inventing missing forcing."""
    d=frame.copy().reset_index(drop=True)
    needed=[c for c in REQUIRED_COLUMNS if not (c=='light_extinction_m_inv' and options.light_extinction_m_inv is not None)]
    missing=sorted(set(needed)-set(d))
    if missing:raise ValueError('Meteorology lacks columns: '+', '.join(missing))
    d['date']=pd.to_datetime(d.date,errors='raise')
    if d.empty or d.date.isna().any() or d.date.duplicated().any() or not d.date.is_monotonic_increasing:
        raise ValueError('Dates must be valid, unique and increasing.')
    if not d.date.eq(d.date.dt.normalize()).all():raise ValueError('Use daily dates without time-of-day.')
    calendar=pd.date_range(d.date.iloc[0],d.date.iloc[-1],freq='D')
    noleap=calendar[~((calendar.month==2)&(calendar.day==29))]
    if not (pd.DatetimeIndex(d.date).equals(calendar) or pd.DatetimeIndex(d.date).equals(noleap)):
        raise ValueError('Daily forcing has gaps other than omitted February 29 dates.')
    for c in needed:
        if c=='date':continue
        d[c]=pd.to_numeric(d[c],errors='raise')
        if not np.isfinite(d[c]).all():raise ValueError(c+' must contain finite values.')
    # Native incoming longwave is used; cloud cover is not a model input.
    d=d.drop(columns=['cloud_fraction'],errors='ignore')
    for c in ['shortwave_w_m2','longwave_w_m2','vapor_pressure_mb','wind_speed_m_s','snowfall_kg_m2_s']:
        if (d[c]<0).any():raise ValueError(c+' must be nonnegative.')
    if options.light_extinction_m_inv is not None:d['light_extinction_m_inv']=options.light_extinction_m_inv
    if (d.light_extinction_m_inv<=0).any():raise ValueError('Light extinction must be positive.')
    if not d.air_temperature_c.between(-100,65).all():raise ValueError('Check air-temperature units: expected °C.')
    return d
