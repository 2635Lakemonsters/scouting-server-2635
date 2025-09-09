import sqlite3
import pandas as pd
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource, Select, MultiSelect, DataTable, TableColumn, CheckboxGroup
from bokeh.layouts import column, row

DB_PATH = "data\db.sqlite"

def fetch_all_matches():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM matches", conn)
    conn.close()
    return df

df = fetch_all_matches()

if 'timeStamp' in df.columns:
    df = df.drop(columns=['timeStamp'])

numeric_cols = []
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col])
        numeric_cols.append(col)
    except (ValueError, TypeError):
        pass

bool_cols = [col for col in df.columns if df[col].dropna().isin([0,1,True,False]).all() and col not in numeric_cols]

teams = sorted(df['teamNumber'].unique())
matches = sorted(df['matchNumber'].unique())

source_plot = ColumnDataSource(data=dict(matchNumber=matches))
source_top_table = ColumnDataSource(data=dict(teamNumber=[], metricValue=[]))
source_team_stats = ColumnDataSource(data=dict(Metric=[], Value=[]))
source_match_details = ColumnDataSource(df.head(0))

team_select = MultiSelect(title="Select Teams", value=[str(teams[0])], options=[str(t) for t in teams])
metric_select = Select(title="Metric", value=numeric_cols[0], options=numeric_cols)
bool_filter = CheckboxGroup(labels=bool_cols, active=[])

match_select = Select(title="Match Number", value=str(matches[0]), options=[str(m) for m in matches])

# ----------------------------
plot = figure(title="Team Metrics Over Matches", x_axis_label="Match", y_axis_label="Value",
              width=800, height=400)
lines = {}

columns_top = [
    TableColumn(field="teamNumber", title="Team"),
    TableColumn(field="metricValue", title="Metric Value")
]
top_table = DataTable(source=source_top_table, columns=columns_top, width=400, height=300)

columns_stats = [
    TableColumn(field="Metric", title="Metric"),
    TableColumn(field="Value", title="Value")
]
team_stats_table = DataTable(source=source_team_stats, columns=columns_stats, width=400, height=300)

columns_match = [TableColumn(field=c, title=c) for c in df.columns]
match_table = DataTable(source=source_match_details, columns=columns_match, width=1000, height=200)

def filter_teams(df):
    active_labels = [bool_cols[i] for i in bool_filter.active]
    for col in active_labels:
        df = df[df[col] == 1]
    return df

def update_plot(attr, old, new):
    metric = metric_select.value
    filtered_df = filter_teams(df)
    selected_teams = [int(t) for t in team_select.value if int(t) in filtered_df['teamNumber'].unique()]
    
    data = {'matchNumber': matches}
    for t in selected_teams:
        df_team = filtered_df[filtered_df['teamNumber'] == t].sort_values('matchNumber')
        data[str(t)] = df_team[metric].values
    
    source_plot.data = data
    
    # Update lines in plot
    plot.renderers.clear()
    for t in selected_teams:
        plot.line('matchNumber', str(t), source=source_plot, line_width=2, legend_label=f"Team {t}")
    plot.legend.click_policy = "hide"

def update_top_table(attr, old, new):
    metric = metric_select.value
    filtered_df = filter_teams(df)

    top_teams = filtered_df.groupby('teamNumber', as_index=False)[metric].mean()
    top_teams = top_teams.sort_values(by=metric, ascending=False).head(10)
    source_top_table.data = dict(teamNumber=top_teams['teamNumber'], metricValue=top_teams[metric])

def update_team_stats(attr, old, new):
    filtered_df = filter_teams(df)
    selected_team = int(team_select.value[0]) if team_select.value else None
    if selected_team is None or selected_team not in filtered_df['teamNumber'].unique():
        source_team_stats.data = dict(Metric=[], Value=[])
        return
    df_team = filtered_df[filtered_df['teamNumber'] == selected_team]
    summary = {col: df_team[col].mean() for col in numeric_cols}
    summary['matches_played'] = len(df_team)
    source_team_stats.data = dict(Metric=list(summary.keys()), Value=list(summary.values()))

def update_match_table(attr, old, new):
    match_num = int(match_select.value)
    df_match = df[df['matchNumber'] == match_num]
    source_match_details.data = df_match.to_dict(orient='list')

team_select.on_change('value', lambda a,o,n: (update_plot(a,o,n), update_team_stats(a,o,n)))
metric_select.on_change('value', lambda a,o,n: (update_plot(a,o,n), update_top_table(a,o,n)))
match_select.on_change('value', update_match_table)
bool_filter.on_change('active', lambda a,o,n: (update_plot(a,o,n), update_top_table(a,o,n), update_team_stats(a,o,n)))

update_plot(None, None, None)
update_top_table(None, None, None)
update_team_stats(None, None, None)
update_match_table(None, None, None)

dashboard = column(
    row(team_select, metric_select, match_select),
    plot,
    row(top_table, team_stats_table, bool_filter),
    match_table
)

curdoc().add_root(dashboard)
