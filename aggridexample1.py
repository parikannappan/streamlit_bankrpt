from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
df = pd.read_csv('https://raw.githubusercontent.com/fivethirtyeight/data/master/college-majors/recent-grads.csv')
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_selection('multiple')  # Enable row selection
grid_options = gb.build()

response = AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True)
selected_rows = response["selected_rows"]
print(f'selected_rows:', selected_rows)