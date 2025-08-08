import pandas as pd

# Data loading (probably move this into scrape_dynamic script)
df = pd.read_csv('./data/talent_schedule.csv')
df_with_image = df[df['image1'].notna()]
df_no_image = df[df['image1'].isna()]
df_sorted = pd.concat([df_with_image, df_no_image])

mask_bracket = df_sorted['name'].str.contains(r'\[.*\]', na=False)
df_final = pd.concat([df_sorted[~mask_bracket], df_sorted[mask_bracket]])
df_final = df_final.reset_index(drop=True)
df_final.index += 1

# df_final.to_csv('./data/talent_schedule.csv')


