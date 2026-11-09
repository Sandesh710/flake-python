"""Notebook figures with a consistent publication-style appearance."""
from contextlib import contextmanager
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as effects
from matplotlib.patches import Polygon
from matplotlib.ticker import MaxNLocator
from matplotlib.lines import Line2D
from .profiles import temperature_profiles,open_water_season

BLUE='#087e8b'
RED='#b23b43'
SNOW='#c58a24'
STYLE={'font.family':'sans-serif','font.sans-serif':['Liberation Sans','DejaVu Sans'],
       'font.size':13,'font.weight':'bold','axes.labelsize':14,'axes.labelweight':'bold',
       'axes.titlesize':16,'axes.titleweight':'bold','axes.edgecolor':'black','axes.linewidth':1.6,
       'axes.labelcolor':'black','text.color':'black','xtick.color':'black','ytick.color':'black',
       'xtick.labelsize':12,'ytick.labelsize':12,'xtick.major.width':1.4,'ytick.major.width':1.4,
       'xtick.major.size':5,'ytick.major.size':5,'figure.facecolor':'white','axes.facecolor':'white',
       'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':300}


def _axis(ax):
    for spine in ax.spines.values():spine.set_visible(True);spine.set_color('black');spine.set_linewidth(1.6)
    ax.tick_params(direction='out',colors='black',width=1.4)
    for label in ax.get_xticklabels()+ax.get_yticklabels():label.set_fontweight('bold');label.set_color('black')
    ax.set_axisbelow(True)


def _months(ax,start,end):
    ax.set_xlim(pd.Timestamp(start),pd.Timestamp(end))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))


def _project(longitude,latitude):
    """Spherical Lambert conformal map, standard parallels 43° and 49°."""
    phi1,phi2=np.deg2rad([43.,49.])
    phi0,lon0=np.deg2rad([46.,-94.])
    n=np.log(np.cos(phi1)/np.cos(phi2))/np.log(np.tan(np.pi/4+phi2/2)/np.tan(np.pi/4+phi1/2))
    F=np.cos(phi1)*np.tan(np.pi/4+phi1/2)**n/n
    rho=6371*F/np.tan(np.pi/4+np.deg2rad(np.asarray(latitude))/2)**n
    rho0=6371*F/np.tan(np.pi/4+phi0/2)**n
    theta=n*(np.deg2rad(np.asarray(longitude))-lon0)
    return rho*np.sin(theta),rho0-rho*np.cos(theta)


def location_map(catalogue,selected,root):
    with plt.rc_context(STYLE):
        fig,ax=plt.subplots(figsize=(8,7),constrained_layout=True)
        geo=json.loads((Path(root)/'assets/region_states.geojson').read_text())
        ax.set_facecolor('#f3f4f2')
        for f in geo['features']:
            geom=f['geometry'];polys=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
            for poly in polys:
                xy=np.asarray(poly[0]);x,y=_project(xy[:,0],xy[:,1])
                ax.add_patch(Polygon(np.column_stack([x,y]),fc='#fffdfa' if f['properties']['name']=='Minnesota' else '#e9ece8',ec='#737c79',lw=1.0))
        area=np.maximum(catalogue.area_km2.to_numpy(float),.001)
        def size(value):return 28+34*np.log10(1+np.asarray(value)*10)
        x,y=_project(catalogue.longitude,catalogue.latitude)
        pts=ax.scatter(x,y,c=catalogue.mean_depth_m,cmap='viridis',s=size(area),ec='white',lw=.8,zorder=5)
        row=catalogue.loc[catalogue.lake_id==selected].iloc[0]
        x,y=_project(row.longitude,row.latitude)
        ax.scatter([x],[y],marker='*',s=390,c=RED,ec='white',lw=1,zorder=7)
        for lon,lat,label in [(-95.6,49.15,'CANADA'),(-94.4,47,'MINNESOTA'),(-90.8,45.5,'WISCONSIN'),(-93.4,43.25,'IOWA')]:
            tx,ty=_project(lon,lat);ax.text(tx,ty,label,fontsize=9,color='#555',ha='center')
        offset=(-12,15) if row.longitude>-92 else (12,15)
        ax.annotate(str(row['name']),(x,y),xytext=offset,textcoords='offset points',ha='right' if offset[0]<0 else 'left',
                    fontsize=13,bbox=dict(fc='white',ec='#ddd',alpha=.95,boxstyle='round,pad=.3'),zorder=9)
        edge_x,edge_y=_project(np.array([-97.7,-89.3,-97.7,-89.3]),np.array([43.1,43.1,49.45,49.45]))
        ax.set_xlim(edge_x.min(),edge_x.max());ax.set_ylim(edge_y.min(),edge_y.max());ax.set_aspect('equal')
        ax.set_xticks([]);ax.set_yticks([])
        ax.set_title('Example lake locations',loc='left',pad=14)
        cb=fig.colorbar(pts,ax=ax,shrink=.65,pad=.025);cb.set_label('Mean depth (m)')
        handles=[ax.scatter([],[],s=size(a),c='#9caeab',ec='white',label=str(a)) for a in [.1,1,10]]
        ax.legend(handles=handles,title='Area (km²)',loc='lower left',frameon=True,edgecolor='black',fontsize=10,title_fontsize=11)
        xmin,xmax=ax.get_xlim();ymin,ymax=ax.get_ylim()
        bx=xmax-140;by=ymin+35
        ax.plot([bx,bx+100],[by,by],c='black',lw=2)
        ax.text(bx+50,by+12,'100 km',ha='center',fontsize=10)
        ax.annotate('N',xy=(.94,.93),xytext=(.94,.84),xycoords='axes fraction',ha='center',fontsize=12,
                    arrowprops=dict(arrowstyle='-|>',color='black',lw=1.5))
        _axis(ax)
    return fig

def forcing_plot(meteo,lake,year=2012):
    d=meteo.loc[pd.to_datetime(meteo.date).dt.year==int(year)]
    if d.empty:raise ValueError('Year is outside the meteorological record.')
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(2,2,figsize=(12,6.4),sharex=True,constrained_layout=True)
        for ax,col,title,unit,color in zip(axes.flat,
          ['air_temperature_c','wind_speed_m_s','shortwave_w_m2','longwave_w_m2'],
          ['(a) Air temperature','(b) Wind speed','(c) Incoming shortwave','(d) Incoming longwave'],
          ['Temperature (°C)','Wind speed (m s⁻¹)','Radiation (W m⁻²)','Radiation (W m⁻²)'],[RED,BLUE,SNOW,BLUE]):
            ax.plot(d.date,d[col],lw=1.5,c=color);ax.set_title(title,loc='left');ax.set_ylabel(unit)
            _months(ax,f'{year}-01-01',f'{year}-12-31');_axis(ax)
        fig.suptitle(f'{lake.name} | Meteorological inputs, {year}',fontsize=18,fontweight='bold')
    return fig


def _section(ax,simulation,d,vmax,panel=''):
    depths,temp=temperature_profiles(simulation,d)
    image=ax.contourf(mdates.date2num(pd.to_datetime(d.date)),depths,temp,levels=np.linspace(0,vmax,71),cmap=('turbo' if 'turbo' in plt.colormaps() else 'jet'),vmin=0,vmax=vmax,zorder=-1)
    ax.set_rasterization_zorder(0)
    line,=ax.plot(pd.to_datetime(d.date),d.mixed_layer_depth_m,c='black',lw=1.0,label='Mixed-layer depth')
    line.set_path_effects([effects.Stroke(linewidth=2.0,foreground='white'),effects.Normal()])
    ice=d.ice_thickness_m.to_numpy(float)>=.01
    transitions=np.diff(np.r_[False,ice,False].astype(int))
    for begin,finish in zip(np.flatnonzero(transitions==1),np.flatnonzero(transitions==-1)):
        left=pd.Timestamp(d.date.iloc[begin]);right=pd.Timestamp(d.date.iloc[finish-1])+pd.Timedelta(days=1)
        ax.axvspan(left,right,facecolor='#d5e2ed',alpha=.13,zorder=3)
        ax.plot([left,right],[1,1],transform=ax.get_xaxis_transform(),lw=5,c='#657b8a',solid_capstyle='butt',zorder=6)
        if (right-left).days>=14:
            ax.text(left+(right-left)/2,.975,'Ice cover',transform=ax.get_xaxis_transform(),ha='center',va='top',fontsize=9,
                    bbox=dict(fc='white',ec='none',alpha=.8),zorder=7)
    ax.set_ylim(simulation.lake.mean_depth_m,0)
    ax.set_ylabel('Depth (m)')
    if panel:ax.set_title(panel,loc='left',pad=10)
    handles,labels=ax.get_legend_handles_labels()
    if ice.any():
        handles.append(Line2D([0],[0],color='#657b8a',lw=4));labels.append('Ice cover (top edge)')
    ax.legend(handles,labels,loc='lower left',frameon=True,facecolor='white',edgecolor='black',fontsize=10,framealpha=.9)
    _axis(ax)
    return image


def thermal_figure(simulation,year=2012,view='open_water'):
    if view not in ['open_water','full_year']:raise ValueError('Choose open_water or full_year.')
    d=open_water_season(simulation,year) if view=='open_water' else simulation.daily.loc[pd.to_datetime(simulation.daily.date).dt.year==int(year)]
    if d.empty:raise ValueError('Year is outside the simulation.')
    vmax=max(30,5*np.ceil(d.mixed_layer_temperature_c.max()/5))
    with plt.rc_context(STYLE):
        fig=plt.figure(figsize=(12,7.3),constrained_layout=True)
        grid=fig.add_gridspec(2,2,width_ratios=[1,.025],height_ratios=[1,2.1],hspace=.08)
        top=fig.add_subplot(grid[0,0]);lower=fig.add_subplot(grid[1,0],sharex=top);cbax=fig.add_subplot(grid[1,1])
        top.plot(d.date,d.mixed_layer_temperature_c,c=RED,lw=2,label='Mixed layer')
        top.plot(d.date,d.bottom_temperature_c,c=BLUE,lw=2,label='Bottom water')
        top.set_ylabel('Temperature (°C)');top.set_title('(a) Water temperature',loc='left')
        top.legend(frameon=False,ncol=2,fontsize=11,loc='best');top.tick_params(labelbottom=False)
        image=_section(lower,simulation,d,vmax,'(b) Thermal structure')
        cb=fig.colorbar(image,cax=cbax);cb.set_ticks(np.arange(0,vmax+.1,5));cb.set_label('Temperature (°C)')
        for ax in [top,lower]:_months(ax,d.date.iloc[0],d.date.iloc[-1]);_axis(ax)
        lower.set_xlabel(f'{year}')
        fig.suptitle(f"{simulation.lake.name} | {'Open-water season' if view=='open_water' else 'Full year'}, {year}",fontsize=18,fontweight='bold')
    return fig


def _winter_data(simulation,ending_year):
    y=int(ending_year);start,end=pd.Timestamp(y-1,9,1),pd.Timestamp(y,6,30)
    d=simulation.daily
    if d.date.min()>start or d.date.max()<end:raise ValueError('Choose a complete September–June winter within the simulation.')
    window=d.loc[d.date.between(start,end)]
    cover=window.loc[(window.ice_thickness_m>=.01)|(window.snow_thickness_m>1e-5)]
    if not cover.empty:
        start=max(start,pd.Timestamp(cover.date.min())-pd.Timedelta(days=10))
        end=min(end,pd.Timestamp(cover.date.max())+pd.Timedelta(days=10))
    return window.loc[window.date.between(start,end)],start,end


def _cover(upper,lower,d,start,end,snow_limit,ice_limit,ending_year=None):
    upper.fill_between(d.date,0,d.snow_thickness_m*100,color=SNOW,alpha=.35)
    upper.plot(d.date,d.snow_thickness_m*100,c=SNOW,lw=2)
    lower.fill_between(d.date,0,d.ice_thickness_m*100,color=BLUE,alpha=.28)
    lower.plot(d.date,d.ice_thickness_m*100,c=BLUE,lw=2)
    upper.set_ylim(0,snow_limit);lower.set_ylim(ice_limit,0)
    upper.yaxis.set_major_locator(MaxNLocator(nbins=4,prune='lower'))
    lower.yaxis.set_major_locator(MaxNLocator(nbins=6))
    upper.set_ylabel('Snow thickness (cm)');lower.set_ylabel('Ice thickness (cm)')
    upper.tick_params(labelbottom=False)
    for ax in [upper,lower]:
        ax.set_xlim(start,end);_axis(ax)
        ax.xaxis.set_major_locator(mdates.MonthLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    season_year=int(ending_year) if ending_year is not None else end.year
    lower.set_xlabel(f'{season_year-1}–{season_year}')


def winter_figure(simulation,ending_year=2014):
    d,start,end=_winter_data(simulation,ending_year)
    snow_limit=max(5,float(d.snow_thickness_m.max()*100)*1.12)
    ice_limit=max(10,float(d.ice_thickness_m.max()*100)*1.10)
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(2,1,figsize=(12,6.6),sharex=True,gridspec_kw={'height_ratios':[1,2],'hspace':0})
        _cover(*axes,d,start,end,snow_limit,ice_limit,ending_year=ending_year)
        axes[0].set_title(f'{simulation.lake.name} | Winter {int(ending_year)-1}–{int(ending_year)}',loc='left',fontsize=18,pad=14)
        fig.subplots_adjust(left=.12,right=.98,top=.89,bottom=.12)
    return fig


def compare_temperature(first,second,year=2012,view='open_water'):
    if view not in ['open_water','full_year']:raise ValueError('Choose open_water or full_year.')
    seasons=[open_water_season(r,year) for r in [first,second]]
    start=min(d.date.min() for d in seasons) if view=='open_water' else pd.Timestamp(int(year),1,1)
    end=max(d.date.max() for d in seasons) if view=='open_water' else pd.Timestamp(int(year),12,31)
    ds=[r.daily.loc[pd.to_datetime(r.daily.date).between(start,end)] for r in [first,second]]
    vmax=max(30,5*np.ceil(max(d.mixed_layer_temperature_c.max() for d in ds)/5))
    start=min(d.date.min() for d in ds);end=max(d.date.max() for d in ds)
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(1,2,figsize=(13,5.1),constrained_layout=True)
        for i,(ax,r,d) in enumerate(zip(axes,[first,second],ds)):
            im=_section(ax,r,d,vmax,f'({chr(97+i)}) {r.lake.name} — {r.lake.mean_depth_m:.1f} m')
            _months(ax,start,end);ax.set_xlabel(str(year))
        cb=fig.colorbar(im,ax=list(axes),shrink=.92,pad=.025);cb.set_ticks(np.arange(0,vmax+.1,5));cb.set_label('Temperature (°C)')
        fig.suptitle(f"Thermal structure | {'Open-water-season window' if view=='open_water' else 'Full year'}, {year}",fontsize=18,fontweight='bold')
    return fig


def compare_winter(first,second,ending_year=2014):
    triples=[_winter_data(r,ending_year) for r in [first,second]]
    common_start=min(t[1] for t in triples);common_end=max(t[2] for t in triples)
    triples=[(r.daily.loc[r.daily.date.between(common_start,common_end)],common_start,common_end) for r in [first,second]]
    snow=max(5,max(float(d.snow_thickness_m.max()*100) for d,_,_ in triples)*1.12)
    ice=max(10,max(float(d.ice_thickness_m.max()*100) for d,_,_ in triples)*1.10)
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(2,2,figsize=(13,6.5),sharex='col',sharey='row',gridspec_kw={'height_ratios':[1,2],'hspace':0,'wspace':.2})
        for i,(r,(d,start,end)) in enumerate(zip([first,second],triples)):
            _cover(axes[0,i],axes[1,i],d,start,end,snow,ice,ending_year=ending_year)
            axes[0,i].set_title(f'({chr(97+i)}) {r.lake.name}',loc='left',pad=12)
            if i:axes[0,i].set_ylabel('');axes[1,i].set_ylabel('')
        fig.suptitle(f'Snow and ice | Winter {int(ending_year)-1}–{int(ending_year)}',fontsize=18,fontweight='bold',y=.98)
        fig.subplots_adjust(left=.09,right=.98,top=.87,bottom=.12)
    return fig
