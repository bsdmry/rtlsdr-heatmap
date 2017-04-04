#!/usr/bin/env python
import json
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')

step_f = 0.0250
min_weight = []
pdgps = pd.DataFrame()
pdsig = pd.DataFrame()
end_df = pd.DataFrame()

def save_pic(frame, x_axis, y_axis, name):
    ax = frame.plot(x=x_axis, y=y_axis, figsize=(20,3), color='g')
    fig = ax.get_figure()
    fig.savefig(name, dpi=100)
    plt.close('all')

with open('scan.rfs') as data_file:    
    data = json.load(data_file)

start_f = float(data[1]['Start'])
stop_f = float(data[1]['Stop'])

#pd.set_option('expand_frame_repr', False)


for times, loc in data[1]['Location'].iteritems():
    tf = pd.DataFrame({'ts' : [int(float(times))], 'lat':[float(loc[0])], 'lon':[float(loc[1])]})
    pdgps =  pdgps.append(tf)
pdgps =  pdgps.set_index('ts')

data_arr = []
for time2 in data[1]['Spectrum']:
    myobj =  data[1]['Spectrum'][time2]
    freqs = sorted(myobj, key=float)
    for freq in freqs:
        data_arr.append([int(float(time2)), float(freq), myobj[freq]])

pdsig = pd.DataFrame.from_records(data_arr, columns=["ts", "freq", "db"])

avg_dev_band  = pdsig.groupby(pd.cut(pdsig["freq"], np.arange(start_f, stop_f+step_f, step_f))).agg({'db' :['mean', 'std']})
avg_dev_band.columns = ['db_avg', 'db_dev']

bands_num = avg_dev_band.index.categories.values.size
band_names = np.linspace(start_f,stop_f,bands_num, endpoint=False).tolist() 

group_a = pdsig.groupby(pdsig["ts"])
#-------------------GOOD!
pdsig['freq'] = pd.Categorical(pd.cut(pdsig["freq"], np.arange(start_f, stop_f+step_f, step_f)))
avg_freqs = pdsig.groupby(["ts", 'freq']).mean()
#save_pic()
avg_freqs = avg_freqs.join(avg_dev_band, how='inner')
value_points = avg_freqs.apply(lambda row: ((row['db'] - row['db_avg'])/row['db_dev']), axis=1)
mval = value_points.min()
value_points = value_points.apply(lambda row: round(( (row+abs(mval)*10)),2))
value_points = value_points.reset_index()
value_points.columns = ['ts', 'freq', 'point']
value_points = value_points.pivot(index='ts', columns='freq', values='point')
#-----------------------

value_points.drop_duplicates(inplace=True)
pdgps["spectrum"] = np.nan
pdgps =  pd.concat([pdgps, value_points], axis=1)
pdgps = pdgps.reset_index()
pdgps = pdgps.astype('object')
pdgps['spectrum']  = pdgps.iloc[:,4:].values.tolist()
pdgps = pdgps.iloc[:,:4]
pdgps = pdgps.dropna()
pdgps = pdgps[['lat', 'lon','ts', 'spectrum']]
pdgps = pdgps.to_dict(orient='records')

json_dict = {'bands':band_names, 'startf':start_f, 'stopf':stop_f ,'band_width':step_f, 'points':pdgps}
print json.dumps(json_dict)
