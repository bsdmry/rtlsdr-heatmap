#!/usr/bin/env python
import json
import pandas as pd
import numpy as np

start_f = 430.000
stop_f = 435.000
step_f = 0.02500
min_weight = []
pdgps = pd.DataFrame()
pdsig = pd.DataFrame()
end_df = pd.DataFrame()
def oper_f(frame):
    frame =  pd.concat([frame.groupby(pd.cut(frame["freq"], np.arange(start_f, stop_f+step_f, step_f))).mean(), avg_dev_band], axis=1)
    frame.columns = ['ts', 'avg_freq', 'db', 'db_avg', 'db_dev']
    frame['point'] = frame.apply(lambda row: round(((row['db'] - row['db_avg'])/row['db_dev']),2), axis=1)
    frame = frame.drop(['db', 'db_avg', 'db_dev'], axis=1)
    min_weight.append( frame['point'].min())

def up_mark(frame, add):
    global end_df
    frame =  pd.concat([frame.groupby(pd.cut(frame["freq"], np.arange(start_f, stop_f+step_f, step_f))).mean(), avg_dev_band], axis=1)
    frame.columns = ['ts', 'avg_freq', 'db', 'db_avg', 'db_dev']
    frame['point'] = frame.apply(lambda row: round((((row['db'] - row['db_avg'])/row['db_dev'] + add)*10 ),2), axis=1)
    frame = frame.drop(['avg_freq', 'db', 'db_avg', 'db_dev'], axis=1)
    frame = frame.dropna()
    #cats =  frame.index.categories
    frame = frame.reset_index()
    frame = frame.pivot(index='ts', columns='freq', values='point')
    end_df = pd.concat([end_df, frame])

with open('/storage/scan430_435.rfs') as data_file:    
    data = json.load(data_file)
#print data[1]['Start']
#print data[1]['Stop']

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
group_a.apply(lambda tab: oper_f(tab))
pdsig.groupby(pdsig["ts"]).apply(lambda tab: up_mark(tab, abs(min(min_weight)) ))

end_df.drop_duplicates(inplace=True)
pdgps["spectrum"] = np.nan
pdgps =  pd.concat([pdgps, end_df], axis=1)

pdgps = pdgps.reset_index()
pdgps = pdgps.astype('object')
pdgps['spectrum']  = pdgps.iloc[:,4:].values.tolist()
pdgps = pdgps.iloc[:,:4]
pdgps = pdgps[['lat', 'lon','ts', 'spectrum']]
pdgps = pdgps.to_dict(orient='records')
#print pdgps.to_json(orient='records')

#print band_names
json_dict = {'bands':band_names, 'startf':start_f, 'stopf':stop_f ,'band_width':step_f, 'points':pdgps}
print json.dumps(json_dict)
