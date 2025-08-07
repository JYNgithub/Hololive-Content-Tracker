import pandas as pd

df_info = pd.read_csv('./data/talent_info.csv')
df_schedule = pd.read_csv('./data/talent_schedule.csv')
df_keys = pd.read_csv('./data/intermediate.csv')

df_info = df_info.merge(df_keys, on='Name', how='left')
df_info = df_info[['Handle'] + [col for col in df_info.columns if col != 'Handle']]
df_info.to_csv('./data/dummy1.csv', index=False)

df_schedule.rename(columns={'name': 'Name'}, inplace=True)
df_schedule = df_schedule.merge(df_keys, on='Name', how='left')
df_schedule = df_schedule[['Handle'] + [col for col in df_schedule.columns if col != 'Handle']]
df_schedule.to_csv('./data/dummy2.csv', index=False)



