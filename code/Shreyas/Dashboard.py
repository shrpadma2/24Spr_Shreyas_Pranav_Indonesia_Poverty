import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import pandas as pd



# Load datasets
df_2019 = pd.read_csv('my_data.csv')
df_2020 = pd.read_csv('my_data1.csv')

# Standardize column names for both datasets
df_2019.rename(columns={'r101n': 'Province', 'r403': 'FuelType', 'r404': 'WaterSource', 'r405a': 'DefecationFacility','r502ak2': 'NumberOfHospitals', 'r502ak3': 'AvgDistanceToHospital', 'r1302': 'ComputerStatus', 'r701a': 'TransportType', 'r703a': 'CableTelephone', 'r703b': 'CellPhoneUsage', 'r1201': 'BUMDesBusinessUnits', 'r1203': 'VillageMarkets', 'r1204': 'BoatMooring'}, inplace=True)
df_2020.rename(columns={'R101N': 'Province', 'R503B': 'FuelType', 'R508': 'WaterSource', 'R507A': 'DefecationFacility','R603AK2': 'NumberOfHospitals', 'R603AK3': 'AvgDistanceToHospital', 'R806A': 'ComputerStatus', 'R801A': 'TransportType', 'R803A': 'CableTelephone', 'R803B': 'CellPhoneUsage', 'R1202': 'BUMDesBusinessUnits', 'R1203': 'VillageMarkets', 'R1204': 'BoatMooring'}, inplace=True)


# Assuming 'i' iterates over school types and 'j' over data types
column_rename_2019 = {f'r501{"abcdefghij"[i]}k{j}': f'EduType{i}_{j}' for i in range(10) for j in range(2, 6)}
column_rename_2020 = {f'R601{"ABCDEFGHIJ"[i]}K{j}': f'EduType{i}_{j}' for i in range(10) for j in range(2, 6)}

# Apply renaming
df_2019.rename(columns=column_rename_2019, inplace=True)
df_2020.rename(columns=column_rename_2020, inplace=True)

transport_mapping = {
    1: 'Land',
    2: 'Land/Water',
    3: 'Land and Water',
    4: 'Air'
}

def process_transport_data(df, mapping):
    # Map the numerical responses to the defined categories
    df['TransportType'] = df['TransportType'].map(mapping)

    # Group by Province and TransportType, then count the occurrences
    transport_grouped = df.groupby(['Province', 'TransportType']).size().unstack(fill_value=0)
    transport_grouped = transport_grouped.apply(lambda x: (x / x.sum()) * 100, axis=1)  # Percentage per province

    return transport_grouped

transport_data_2019 = process_transport_data(df_2019, transport_mapping)
transport_data_2020 = process_transport_data(df_2020, transport_mapping)

# Function to process cable telephone data
def process_cable_telephone_data(df):
    # Normalize per 1000 families
    df['CableTelephone_per_1000'] = df['CableTelephone'] / df['Total Families'] * 1000
    return df.groupby('Province')['CableTelephone_per_1000'].mean().reset_index()

cell_phone_usage_mapping = {
    1: 'Most of the citizens',
    2: 'A small portion of citizens',
    3: 'None'
}

df_2019['CellPhoneUsage'] = df_2019['CellPhoneUsage'].map(cell_phone_usage_mapping)
df_2020['CellPhoneUsage'] = df_2020['CellPhoneUsage'].map(cell_phone_usage_mapping)

def process_cell_phone_data(df):
    # Group by Province and calculate the percentage of each cell phone usage category
    cell_phone_data = df.groupby(['Province', 'CellPhoneUsage']).size().unstack(fill_value=0)
    cell_phone_data = cell_phone_data.apply(lambda x: (x / x.sum()) * 100, axis=1)  # Convert counts to percentages
    return cell_phone_data

# Process the data for each year
cable_telephone_data_2019 = process_cable_telephone_data(df_2019)
cable_telephone_data_2020 = process_cable_telephone_data(df_2020)

# Define mappings outside of the callback
fuel_mapping = {
    1: 'Gas Kota', 2: 'LPG 3kg', 3: 'LPG more than 3kg', 4: 'Kerosene', 5: 'Firewood', 6: 'Other'
}
water_mapping = {
    1: 'Branded bottled water', 2: 'Refill', 3: 'Plumbing with meter (PAM/PDAM)',
    4: 'Plumber without meter', 5: 'Wells or pumps', 6: 'Well', 
    7: 'Water springs', 8: 'River/lake/pond/reservoir/situ/embung/dam',
    9: 'Rainwater', 10: 'Others'
}
defecation_facility_mapping = {
    1: 'Own toilet', 2: 'Toilet together', 3: 'Public toilet', 4: 'Not a latrine'
}

computer_status_mapping = {
    1: 'Used',
    2: 'Rarely used',
    3: 'Not used',
    4: 'None'
}

def aggregate_education_data(df):
    # Define column patterns to sum and average
    sum_column_patterns = [f'EduType{i}_{j}' for i in range(10) for j in [2, 3]]
    mean_column_patterns = [f'EduType{i}_4' for i in range(10)]

    # Check if columns exist in the dataframe and select them
    sum_columns = [col for col in sum_column_patterns if col in df.columns]
    mean_columns = [col for col in mean_column_patterns if col in df.columns]

    # Perform the aggregation
    df['Sum_23'] = df[sum_columns].sum(axis=1) if sum_columns else 0
    df['Mean_4'] = df[mean_columns].mean(axis=1) if mean_columns else 0

    # Normalize per 1000 families
    df['Sum_23_per_1000'] = df['Sum_23'] / df['Total Families'] * 10000
    df['Mean_4_per_1000'] = df['Mean_4'] / df['Total Families'] * 10000

    grouped_df = df.groupby('Province').agg({
        'Sum_23_per_1000': 'sum',
        'Mean_4_per_1000': 'mean'
    }).reset_index()

    return grouped_df


# Process data for each year
education_data_2019 = aggregate_education_data(df_2019)
education_data_2020 = aggregate_education_data(df_2020)


# Create Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Indonesia Poverty and Equity Program Dashboard"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[
            {'label': '2019', 'value': '2019'},
            {'label': '2020', 'value': '2020'}
        ],
        value='2020'
    ),
    dcc.Graph(id='electricity-users-graph'),
    dcc.Graph(id='fuel-type-graph'),
    dcc.Graph(id='water-source-graph'),
    dcc.Graph(id='defecation-facility-graph'),
    dcc.Graph(id='hospital-graph'),
    dcc.Graph(id='computer-status-graph'),
    dcc.Graph(id='education-graph'),
    dcc.Graph(id='transportation-graph'),
    dcc.Graph(id='cable-telephone-graph'),
    dcc.Graph(id='cell-phone-usage-graph'),
    dcc.Graph(id='province-aggregate-graph')
])

@app.callback(
    [Output('electricity-users-graph', 'figure'),
     Output('fuel-type-graph', 'figure'),
     Output('water-source-graph', 'figure'),
     Output('defecation-facility-graph', 'figure'),
     Output('hospital-graph', 'figure'),
     Output('computer-status-graph', 'figure'),
     Output('education-graph', 'figure'),
     Output('transportation-graph', 'figure'),
     Output('cable-telephone-graph', 'figure'),
     Output('cell-phone-usage-graph', 'figure'),
     Output('province-aggregate-graph', 'figure')],
    [Input('year-dropdown', 'value')]
)
def update_graph(selected_year):
    try:
        df_selected = df_2019.copy() if selected_year == '2019' else df_2020.copy()
        
        df_selected['ComputerStatus'] = df_selected['ComputerStatus'].map(computer_status_mapping)
        computer_status_data = df_selected.groupby(['Province', 'ComputerStatus']).size().unstack(fill_value=0)
        computer_status_data = computer_status_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        computer_status_fig = px.bar(
            computer_status_data.reset_index(),
            x='Province',
            y=computer_status_data.columns,
            title="Computer Status per 1000 Offices by Province",
            labels={'value': 'Number of Offices', 'variable': 'Computer Status'},
            barmode='stack'
        )
        computer_status_fig.update_layout(
            title="Computer Status per 1000 Offices by Province",
            xaxis_title="Province",
            yaxis_title="Number of Offices",
            legend_title="Computer Status"
        )

        # Process hospital data for the selected year
        hospital_df = df_selected.groupby('Province').agg({
            'NumberOfHospitals': 'sum', 
            'AvgDistanceToHospital': 'mean'
        }).reset_index()
        hospital_df['NumberOfHospitalsPer100000'] = (hospital_df['NumberOfHospitals'] / df_selected['Total Families'] * 100000)
        national_average = hospital_df['NumberOfHospitalsPer100000'].mean()

        # Create the Plotly graph for hospital data
        hospital_fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add bar plot for the number of hospitals per 100,000 families
        hospital_fig.add_trace(
            go.Bar(
                x=hospital_df['Province'],
                y=hospital_df['NumberOfHospitalsPer100000'],
                name='Number of Hospitals per 100000 Families',
                marker_color='lightblue'
            ),
            secondary_y=False,
        )

        # Add line plot for the average distance to the nearest hospital
        hospital_fig.add_trace(
            go.Scatter(
                x=hospital_df['Province'],
                y=hospital_df['AvgDistanceToHospital'],
                name='Average Distance to Nearest Hospital',
                mode='lines+markers',
                marker_color='darkorange',
                line=dict(width=2)
            ),
            secondary_y=True,
        )

        # Add a scatter trace for the national average line for a legend entry
        hospital_fig.add_trace(
            go.Scatter(
                x=hospital_df['Province'],
                y=[national_average]*len(hospital_df['Province']),
                name='National Average',
                mode='lines',
                line=dict(color="red", width=2, dash="dot"),
                hoverinfo='skip'
            ),
            secondary_y=False,
        )

        # Set titles, axes labels, and legend positioning
        hospital_fig.update_layout(
            title_text="Hospital Data Analysis",
            yaxis_title='Number of Hospitals per 100000 Families',
            legend=dict(
                x=0,
                y=1.0,
                traceorder='normal',
                bgcolor='rgba(255,255,255,0)',
                bordercolor='rgba(255,255,255,0)'
            )
        )

        hospital_fig.update_yaxes(title_text="Number of Hospitals per 100000 Families", secondary_y=False)
        hospital_fig.update_yaxes(title_text="Average Distance to Nearest Hospital (km)", secondary_y=True)


        # Process electricity data
        # Assuming you have columns 'PLN users by 1000' and 'Non-PLN users by 1000' in your dataframe
        grouped_electricity = df_selected.groupby('Province').agg({
            'PLN users by 1000': 'mean',
            'Non-PLN users by 1000': 'mean'
        }).reset_index()
        electricity_fig = px.bar(
            grouped_electricity,
            x='Province',
            y=['PLN users by 1000', 'Non-PLN users by 1000'],
            title="Electricity Usage by Province for 1000 Families",
            labels={'value': 'Number of Families', 'variable': 'Type of Electricity User'},
            barmode='stack'
        )
        electricity_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Number of Families",
            legend_title="Type of Electricity User"
        )

        # Process fuel data
        df_selected['FuelType'] = df_selected['FuelType'].map(fuel_mapping)
        fuel_data = df_selected.groupby(['Province', 'FuelType']).size().unstack(fill_value=0)
        fuel_data = fuel_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        fuel_fig = px.bar(
            fuel_data.reset_index(),
            x='Province',
            y=fuel_data.columns,
            title="Fuel Used for Cooking per 1000 Families by Province",
            labels={'value': 'Number of Families', 'variable': 'Fuel Type'},
            barmode='stack'
        )
        fuel_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Number of Families",
            legend_title="Fuel Type"
        )

        # Process water source data
        df_selected['WaterSource'] = df_selected['WaterSource'].map(water_mapping)
        water_data = df_selected.groupby(['Province', 'WaterSource']).size().unstack(fill_value=0)
        water_data = water_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        water_fig = px.bar(
            water_data.reset_index(),
            x='Province',
            y=water_data.columns,
            title="Water Source per 1000 Families by Province",
            labels={'value': 'Number of Families', 'variable': 'Water Source'},
            barmode='stack'
        )
        water_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Number of Families",
            legend_title="Water Source"
        )

        df_selected['DefecationFacility'] = df_selected['DefecationFacility'].map(defecation_facility_mapping)
        defecation_data = df_selected.groupby(['Province', 'DefecationFacility']).size().unstack(fill_value=0)
        defecation_data = defecation_data.apply(lambda x: (x / x.sum()) * 1000, axis=1)
        defecation_facility_fig = px.bar(
            defecation_data.reset_index(),
            x='Province',
            y=defecation_data.columns,
            title="Defecation Facilities per 1000 Families by Province",
            labels={'value': 'Number of Families', 'variable': 'Defecation Facility'},
            barmode='stack'
        )
        defecation_facility_fig.update_layout(title="Defecation Facility Usage by Province for 1000 Families",
                                                xaxis_title="Province",
                                                yaxis_title="Number of Families",
                                                legend_title="Defecation Facility")
        
        education_data = education_data_2019 if selected_year == '2019' else education_data_2020
        national_average_mean = education_data['Mean_4_per_1000'].mean()

        education_fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add bar plot for summed '2' and '3' columns
        education_fig.add_trace(
            go.Bar(
                x=education_data['Province'], 
                y=education_data['Sum_23_per_1000'],
                name='Sum of Public and Private Education Levels per 10000 Families'
            ),
            secondary_y=False
        )

        # Add line plot for averaged '4' columns
        education_fig.add_trace(
            go.Scatter(
                x=education_data['Province'], 
                y=education_data['Mean_4_per_1000'],
                name='Average Distance to Educational Facility',
                mode='lines+markers',
                marker_color='orange'
            ),
            secondary_y=True
        )

        education_fig.add_trace(
            go.Scatter(
                x=education_data['Province'], 
                y=[national_average_mean]*len(education_data),
                mode='lines',
                line=dict(color='blue', dash='dash'),
                name='National Avg Distance to Educational Institution'
            ),
            secondary_y=True
        )

        education_fig.update_layout(
            title_text='Educational Facilities and Distance Data by Province',
            yaxis_title='Total Educational Facilities per 10000 Families',
            yaxis2_title='Average Distance to Facilities (km)',
            legend_title='Legend'
        )

        transport_data = transport_data_2019 if selected_year == '2019' else transport_data_2020

        # Create the Plotly graph for transportation data
        transport_fig = px.bar(
            transport_data.reset_index(),
            x='Province',
            y=transport_data.columns,
            title="Means of Transportation per Province",
            labels={'value': 'Percentage of Responses', 'variable': 'Means of Transportation'},
            barmode='group'
        )
        transport_fig.update_layout(
            xaxis_title="Province",
            yaxis_title="Percentage of Responses",
            legend_title="Means of Transportation"
        )

        cable_telephone_data = cable_telephone_data_2019 if selected_year == '2019' else cable_telephone_data_2020
        cable_telephone_fig = px.bar(
        cable_telephone_data,
        x='Province',
        y='CableTelephone_per_1000',
        title='Cable Telephone Subscriptions per 1000 Families'
    )

        # Select the appropriate year's data for cell phone usage
        cell_phone_data = process_cell_phone_data(df_selected)
        cell_phone_usage_fig = px.bar(
            cell_phone_data.reset_index(),
            x='Province',
            y=cell_phone_data.columns,
            title='Cell Phone Usage Distribution',
            labels={'value': 'Percentage of Citizens', 'variable': 'Cell Phone Usage'}
    )
        
        province_stats = df_selected.groupby('Province').agg({
            'BUMDesBusinessUnits': 'sum',
            'VillageMarkets': 'sum',
            'BoatMooring': 'sum'
        }).reset_index()

        # Normalize the data per 1000 families
        province_stats['BUMDesBusinessUnits_per_1000'] = province_stats['BUMDesBusinessUnits'] / df_selected['Total Families'] * 1000
        province_stats['VillageMarkets_per_1000'] = province_stats['VillageMarkets'] / df_selected['Total Families'] * 1000
        province_stats['BoatMooring_per_1000'] = province_stats['BoatMooring'] / df_selected['Total Families'] * 1000

        # Creating the bar graph
        province_statistics_fig = go.Figure(data=[
            go.Bar(name='BUMDes Business Units', x=province_stats['Province'], y=province_stats['BUMDesBusinessUnits_per_1000']),
            go.Bar(name='Village Markets', x=province_stats['Province'], y=province_stats['VillageMarkets_per_1000']),
            go.Bar(name='Boat Mooring', x=province_stats['Province'], y=province_stats['BoatMooring_per_1000'])
        ])
        province_statistics_fig.update_layout(
            title='Provincial Statistics per 1000 Families',
            xaxis_title='Province',
            yaxis_title='Count per 1000 Families',
            barmode='group'
        )



        return electricity_fig, fuel_fig, water_fig, defecation_facility_fig, hospital_fig, computer_status_fig, education_fig, transport_fig, cable_telephone_fig, cell_phone_usage_fig, province_statistics_fig
    except Exception as e:
        print(f"An error occurred: {e}")
        # Return blank figures in case of an error
        return {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

if __name__ == '__main__':
    app.run_server(debug=True)
