# Using the Python implementation

The notebook is the main entry point. Open it using the README’s Colab button; Section 1 retrieves the code and versioned example dataset automatically. Run cells in order: load the package, select a lake, inspect meteorology, configure the model, run it and create figures. Changing the lake requires rerunning the subsequent cells. Changing a model control requires rerunning the simulation and figures.

## Lake properties

`Lake` describes one representative water column. Supply a name, mean depth in meters, wind fetch in meters and latitude in degrees. Longitude and area provide geographic context. Latitude is used to calculate the Coriolis parameter when a value is not supplied. The example lake records already include their assigned Coriolis values.

The model depth is mean depth, rather than the maximum bathymetric depth. Horizontal circulation and detailed lake bathymetry are not resolved. Use representative depth and fetch for the intended application.

Snow retention represents reduced snow accumulation and the resulting snow depth. It must be between zero and one. The Minnesota examples use their supplied regional assignments. For another location, use a defensible value; the Minnesota area relationship is not automatically generalized to other lakes.

## Daily meteorological data

Required columns:

| Column | Units |
|---|---|
| `date` | Daily date, YYYY-MM-DD |
| `air_temperature_c` | °C |
| `wind_speed_m_s` | m s⁻¹ |
| `vapor_pressure_mb` | mb = hPa |
| `shortwave_w_m2` | W m⁻², incoming |
| `longwave_w_m2` | W m⁻², incoming |
| `snowfall_kg_m2_s` | kg m⁻² s⁻¹, water-equivalent snowfall |
| `light_extinction_m_inv` | m⁻¹ |

A constant `ModelOptions.light_extinction_m_inv` can replace the light-extinction column. Native incoming longwave is supplied directly; cloud fraction is not required. Meteorology must be finite, chronologically ordered and daily, with no duplicate dates. Complete Gregorian and 365-day/no-leap sequences are accepted. Missing February 29 dates are not interpolated. Other gaps are rejected.

Aggregate hourly inputs to daily values before using this daily runner. Use daily means for air temperature, vapor pressure, wind and radiative fluxes. Sum daily precipitation or snowfall water equivalent before converting it to a mass flux. Convert accumulated radiation energy to a daily mean flux using the accumulation interval; do not treat joules per square meter as watts per square meter. The example notebook does not perform gap filling.

One millimeter of water equivalent corresponds to one kilogram per square meter. Divide daily snowfall water equivalent in mm by 86,400 to obtain kg m⁻² s⁻¹. If only precipitation is available, partition rain and snow before simulation. The example preparation assigns all precipitation to snow below 0 °C, a linearly decreasing snow fraction between 0 and 2 °C, and no snowfall above 2 °C. Do not repartition a snowfall product.

Wind height defaults to 10 m, temperature/humidity height to 2 m and pressure to 100,000 Pa. Supply values consistent with your meteorological preparation through `ModelOptions`.

## Initial conditions

The supplied historical examples continue from the saved state at the beginning of 1995. Their original 1950 run began with a fully mixed 4 °C water column, no snow or ice, and sediment initialized at 5 m and 6 °C.

For a new experiment, `InitialConditions` specifies water temperature and cover thickness. A snow-free, ice-free lake begins fully mixed. If ice is specified, the mixed-layer thickness is zero, surface water is at freezing and the specified water temperature is the bottom value; the mean temperature is initialized consistently with the bulk profile. Initial snow requires ice and an enabled snow module.

Changing depth, fetch, light extinction or module switches in the notebook selects new initial conditions. Selecting the historical-start option restores the example settings. This prevents a saved state from being silently reused for incompatible geometry or physics. A new January 1995 experiment has no preceding warm-up in this package; early behavior reflects the selected initial conditions. For a new application, provide an appropriate spin-up period or physically consistent saved state.

## Snow and sediment switches

`ModelOptions(snow=False)` represents bare ice: start with zero snow, and no snow accumulates during the run. Ice formation, growth and melt remain active. `ModelOptions(sediments=False)` disables conductive bottom heat exchange. The switches operate within the simulation, not only in the plotted output.

The example settings use snow and ice albedo endpoints of 0.60/0.10, snow density bounds of 100–400 kg m⁻³, a density coefficient of 2000 kg m⁻⁴ and minimum snow conductivity of 0.30 W m⁻¹ K⁻¹. `ModelOptions` exposes albedo, minimum conductivity, sediment boundary and measurement-height settings. Keep settings appropriate to the application.

## Reading figures

The thermal figure shows one year's longest continuous ice-free interval, using a 1 cm threshold. The top panel shows mixed-layer and bottom-water temperatures. The lower panel reconstructs the FLake profile using the simulated shape factor and the polynomial in Mironov (2008), Eq. (55). This is the bulk model's vertical profile, not an independent depth-resolved simulation. The black line is mixed-layer depth.

Winter diagnostics use September–June. Figures crop to approximately ten days before and after cover, with snow plotted above the cover interface and ice downward below it. Thickness axes are centimeters. Comparison plots use a common temperature scale and common snow/ice thickness scales; each thermal panel retains its own physical lake depth.

Ice-on and ice-off require three successive days above/below 1 cm. Only complete seasonal windows with sufficient data are listed. Onset is searched September–March, and breakup after the last spring ice day through June. Duration uses Gregorian calendar-date differences. Historical examples have complete winters ending in 1996–2014; scenario examples extend through 2040.

State variables are recorded at the start of the labeled day, while flux columns describe that day's integration. Output thicknesses are meters and temperatures are °C. Surface-temperature and cover-temperature diagnostics retain the engine's existing conventions. For interpretation, the notebook emphasizes water-column temperatures, cover thicknesses and ice dates.

## Files and outputs

`configuration.py`, `inputs.py`, `model.py`, `physics.py`, `profiles.py`, `plotting.py`, `diagnostics.py` and `notebook.py` each have one role. The public interface is `simulate(lake, meteorology, options, initial_conditions=...)`. It returns a `Simulation` with lake configuration, model options, daily output and final state. `restart=...` can be supplied instead of initial conditions for a consistent continuation.

Downloads contain daily CSV output, ice dates, model settings and PNG/PDF figures. The selected year controls figures; the daily table still contains the full run.

## Climate scenarios and observations

Select historical forcing for 1995–2014, or one SSP to extend that same history through 2040. Scenario data begin in 2015; there is no overlap or repeated year. The four options are SSP1-2.6, SSP2-4.5, SSP3-7.0 and SSP5-8.5, all from GFDL-ESM4. This single-model example illustrates scenario-dependent forcing, rather than the full uncertainty across climate models.

The observation files contain measured temperature profiles and ice dates within the historical period where available. They are displayed separately because a climate-model realization is not synchronized with observed daily weather. Availability varies by lake and year. Original observation dates are retained; repeated temperature measurements at one depth are averaged only when drawing a measured profile.

`thermal_figure(..., view="full_year")` retains the under-ice temperature field and marks ice periods. The default `view="open_water"` shows the longest continuous open-water interval. A cold under-ice column uses the linear conductive profile convention; the open-water thermocline uses the FLake shape function.
