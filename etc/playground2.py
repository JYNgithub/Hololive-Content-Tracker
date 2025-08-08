import pandas as pd

# Data loading (probably move this into scrape_dynamic script)
df_info = pd.read_csv('./data/talent_info.csv')
df_sche = pd.read_csv('./data/talent_schedule.csv')
df = pd.merge(df_info, df_sche, on="Handle", how="inner")
df['name'] = df['name_x'] 
df.drop(columns=['name_x', 'name_y'], inplace=True)
df = df[~((df['name'] == 'Mococo Abyssgard') & (df['default_image'].str.lower().str.contains('fuwawa')))]
df = df[~((df['name'] == 'Fuwawa Abyssgard') & (df['default_image'].str.lower().str.contains('mococo')))]
df.to_csv('test.csv')