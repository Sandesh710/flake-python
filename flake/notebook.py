"""Lake selection and model-configuration controls for Jupyter/Colab."""
from dataclasses import replace
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display,clear_output,HTML
from .inputs import load_example,example_settings
from .configuration import ModelOptions,InitialConditions
from .plotting import location_map


def select_lake(catalogue,root):
    menu=widgets.Dropdown(options=[(f"{r.name} — {r.mean_depth_m:.1f} m — {r.lake_id}",r.lake_id)
        for r in catalogue.sort_values(['name','lake_id']).itertuples()],value=example_settings(root)['default_lake_id'],description='Lake:',layout=widgets.Layout(width='95%'))
    out=widgets.Output()
    def update(change=None):
        with out:
            clear_output(wait=True)
            r=catalogue.loc[catalogue.lake_id==menu.value].iloc[0]
            fig=location_map(catalogue,menu.value,root);display(fig);plt.close(fig)
            display(pd.DataFrame({'Property':['Lake','County','Mean depth (m)','Area (km²)','Fetch (m)'],
                                  'Value':[r['name'],str(r.county).title(),round(r.mean_depth_m,2),round(r.area_km2,2),round(r.fetch_m)]}))
    menu.observe(update,names='value');display(menu,out);update()
    return menu


class ModelControls:
    """Expose meaningful inputs; retain a saved restart only with its lake setup."""
    def __init__(self,lake,restart,start_date="1995-01-01"):
        self.lake=lake;self.restart=restart;self.start_date=pd.Timestamp(start_date).strftime("%d %B %Y");self._updating=False
        style={'description_width':'155px'}
        def number(label,value,minimum=0,maximum=10000,step=.1):
            return widgets.BoundedFloatText(description=label,value=value,min=minimum,max=maximum,step=step,
                  style=style,layout=widgets.Layout(width='350px'))
        self.depth=number('Mean depth (m):',lake.mean_depth_m,.1,200)
        self.fetch=number('Fetch (m):',lake.fetch_m,1,1000000,100)
        self.sediments=widgets.Checkbox(value=True,description='Include sediment heat exchange',indent=False)
        self.snow=widgets.Checkbox(value=True,description='Include snow cover',indent=False)
        self.retention=number('Snow retention (0–1):',lake.snow_retention,0,1,.05)
        self.optics=widgets.Dropdown(options=[('Use supplied light extinction',None),('Set a constant value','constant')],
                     value=None,description='Light extinction:',style=style,layout=widgets.Layout(width='440px'))
        self.kd=number('Constant Kd (m⁻¹):',1,.01,20,.1);self.kd.disabled=True
        self.mode=widgets.Dropdown(options=[('Historical start state','historical'),('Specify initial conditions','custom')],
                     value='historical',description='Initialization:',style=style,layout=widgets.Layout(width='440px'))
        self.temperature=number('Initial water (°C):',4,0,40)
        self.ice=number('Initial ice (m):',0,0,3,.01)
        self.snow_depth=number('Initial snow (m):',0,0,2,.01)
        self.message=widgets.HTML()
        for w in [self.depth,self.fetch,self.sediments,self.snow,self.retention,self.optics,self.kd]:w.observe(self._changed,names='value')
        self.mode.observe(self._mode_changed,names='value')
        self._refresh()

    def _changed(self,change):
        if self._updating:return
        self.kd.disabled=self.optics.value is None
        self.mode.value='custom'
        if not self.snow.value:self.snow_depth.value=0.0
        self._refresh()

    def _mode_changed(self,change):
        if self._updating:return
        if self.mode.value=='historical':
            self._updating=True
            self.depth.value=self.lake.mean_depth_m;self.fetch.value=self.lake.fetch_m
            self.sediments.value=True;self.snow.value=True;self.retention.value=self.lake.snow_retention;self.optics.value=None;self.kd.disabled=True
            self._updating=False
        self._refresh()

    def _refresh(self):
        historical=self.mode.value=='historical'
        for w in [self.temperature,self.ice]:w.disabled=historical
        self.snow_depth.disabled=historical or not self.snow.value
        text=('The example begins from its saved historical state on '+self.start_date+'.' if historical else
              'This experiment starts on '+self.start_date+' from the initial conditions below. Early results reflect this initialization.')
        self.message.value='<p style="font-size:14px;color:#222">'+text+'</p>'

    def display(self):
        display(widgets.VBox([widgets.HTML('<b>Lake properties</b>'),widgets.HBox([self.depth,self.fetch],layout=widgets.Layout(flex_flow='row wrap')),
            widgets.HTML('<b>Model components</b>'),self.sediments,self.snow,self.retention,self.optics,self.kd,
            widgets.HTML('<b>Initial conditions</b>'),self.mode,self.message,
            widgets.HBox([self.temperature,self.ice,self.snow_depth],layout=widgets.Layout(flex_flow='row wrap'))]))
        return self

    def values(self):
        options=ModelOptions(sediments=self.sediments.value,snow=self.snow.value,
                            light_extinction_m_inv=self.kd.value if self.optics.value else None)
        historical=self.mode.value=='historical'
        lake=replace(self.lake,mean_depth_m=self.depth.value,fetch_m=self.fetch.value,snow_retention=self.retention.value,
                     name=self.lake.name if historical else self.lake.name+' (experiment)')
        initial=None if historical else InitialConditions(self.temperature.value,self.ice.value,self.snow_depth.value)
        return lake,options,initial,self.restart if historical else None
