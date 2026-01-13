# 1. Introduction

<br>
<p align="center">
    <img src="../assets/uk_energy_dashboard.png" alt="Uk Energy Dashboard" width="50%" height="50%">
</p>
<br>

**Project Deployment:** [https://ukenergydashboard.streamlit.app](https://ukenergydashboard.streamlit.app) <br>
**Set-up Guide:** README.md <br>
**Assignment Brief:** documentation/assignment_brief.md <br>

---

## 1.1 Background & Motivation

The UK energy system is undergoing a significant structural transition, moving away from non-renewable sources of energy in order to achieve the net zero target proposed by the government (Department for Business, Energy & Industrial Strategy, 2021). This transition has led to noticeable changes in electricity demand patterns. As wind and solar energy generation are dependent on natural factors beyond direct human control, this has introduced increased volatility into electricity generation capabilities. Despite this, the UK was able to achieve 50.4% renewable electricity generation in the previous year (RenewableUK, 2024). While achieving net zero remains a work in progress, enabling people with tools to explore the problem can help raise awareness and understanding.

At the same time, there is a large amount of publicly available data that is scattered across multiple platforms and is not centralised into a single view capable of providing a holistic understanding of how different variables interact. Organisations such as the National Energy System Operator (NESO) provide multiple high-quality datasets and APIs for electricity demand, generation, and system operation (NESO, 2024). However, these datasets are published separately, meaning that non-technical users are unable to easily derive insights into how variables such as electricity demand, carbon intensity, and generation mix relate to one another.

<br>
<p align="center">
    <img src="../assets/neso_home_page.png" alt="Home page of NESO" width="50%" height="50%">
</p>
<br>

As a result, users who wish to explore how electricity demand, carbon intensity, generation mix, and environmental factors interact must either rely on static summaries or perform significant preprocessing themselves. This project is motivated by the observation that data accessibility does not necessarily imply the ability to derive analytical insight, particularly in the context of exploratory data analysis.

---

## 1.2 Problem Definition

The central problem addressed by this project is:

> *How can multiple UK energy and environmental datasets be integrated into a single interactive system that allows intuitive exploration of energy and environmental patterns and trends?*

Although publicly available UK energy data continues to increase in availability, these sources remain fragmented and often exist at differing temporal resolutions, requiring substantial preprocessing and technical knowledge (NESO, 2024). This project aims to address this problem by providing an interactive dashboard that integrates electricity demand, carbon intensity, and weather data into a single system for exploratory analysis. The system also supports exploration of regions both in isolation and in combination.

---

## 1.3 Review of Existing Tools

### EnergyDashboard (energydashboard.co.uk)

EnergyDashboard provides a near real-time overview of the UK electricity system, with a clear emphasis on short-term operational indicators such as demand, generation mix, and system status. The platform is effective at communicating current system conditions to a broad audience but lacks the analytical depth that may be of interest to researchers or analysts.

<br>
<p align="center">
    <img src="../assets/energy_dashboard.png" alt="EnergyDashboard" width="50%" height="50%">
</p>
<br>

The dashboard is primarily operational rather than analytical. In addition, access to historical data is limited, and users are largely restricted to viewing short-term or current system behaviour. There is minimal support for custom filtering, cross-dataset comparison, or exploratory analysis across time and regions. As a result, the platform is well suited for real-time operational monitoring but lacks historical depth and exploratory capability.

---

### Great Britain’s Monthly Energy Statistics (NESO)

The monthly statistics published by NESO provide credible summaries of long-term trends within the UK energy system (NESO, 2024). These reports aggregate demand, generation, and system performance metrics into structured visualisations suitable for official reporting and retrospective analysis. However, these visualisations are not updated in real time and provide limited flexibility for custom analysis.

<br>
<p align="center">
    <img src="../assets/neso_monthly_reports.png" alt="Great Britain’s Monthly Energy Statistics (NESO)" width="50%" height="50%">
</p>
<br>

While this approach ensures that insights are consistent and reliable, it limits interactivity and fine-grained time-series exploration. This constrains the ability of users to generate insights across specific regions, time windows, or in combination with external datasets such as weather data.

Across both platforms, the primary limitation is not data quality but the range of interactions available to the user and the extent of data integration. EnergyDashboard excels at near real-time operational indicators, while NESO’s monthly statistics provide historical depth and reliability at the expense of interactivity. Neither platform integrates multiple datasets into a single interactive system designed for exploratory visual analysis.

---

## 1.4 Positioning of This Project

This project is intentionally positioned as an interactive and exploratory dashboard rather than a real-time monitoring or forecasting tool. Its primary contributions are:

* Integrating electricity demand, generation mix, power flow, carbon intensity, and weather data into a single platform
* Allowing users to filter data by region and selected time periods
* Supporting pattern discovery through advanced visualisations
* Providing a system architecture that supports future development and extension

Rather than directly competing with existing platforms, this project aims to fill a gap by offering a free, open-source tool that enables users to engage directly with up-to-date UK energy data.

<br>
<p align="center">
    <img src="../assets/solution_overview.svg" alt="Solution Overview">
</p>
<br>


## 1.5 Objectives & Scope

To fulfil the gaps identified in the analysis above, a set of core objectives and additional optional objectives are defined.

### Core Objectives

1. **Multi-source Data Integration**

   > Integrate electricity demand, generation mix, power flow, carbon intensity, and weather data into a single platform. Data should cover the period from 01/01/2020 to the latest available data point.

2. **Reliable Data Storage**

   > Store data in a remote relational database with clearly defined schemas and logic to rerun ingestion when new data becomes available.

3. **Interactive Time-Series Exploration**

   > Visualise data using time-series plots that support zooming, panning, and comparison of multiple variables within a single view.

4. **Regional and Temporal Exploration**

   > Allow users to filter data by region and date range, supporting both single and multiple region selection, as well as quick-select options such as the last 7, 30, or 90 days.

5. **Summary Statistics**

   > Provide summary statistics for the selected data, including metrics such as average, minimum, maximum, and trend, accompanied by a time-series plot for the selected period.

6. **Data-Driven Visualisations**

   > Use appropriate visualisations such as stacked bar charts, heatmaps, annotated geographical maps, diverging horizontal bar charts, and scatter plots to highlight patterns within the data.

---

### Additional Optional Objectives

7. **Deployment to Remote Hosting**

   > Deploy the dashboard to a cloud-based hosting platform for public access via a shareable URL, ensuring the deployed version mirrors local execution behaviour.

8. **Experimental Forecasting Tab**

   > Introduce an experimental section allowing users to select input features and targets to perform short-horizon forecasting using simple machine learning models, including regression and tree-based approaches.

9. **Visualisation of Experimental Results**

   > Present model performance metrics such as MAE, RMSE, and R². Visualise predicted versus true values and model performance over a 180-day window, and allow users to generate a 7-day future prediction.


<br><br>

# 2. Design

## 2.1 Design Objectives & Constraints

The design of the Uk energy board is guided by the need of having support  for an interactive tool for exploratory analysis of multiple related datasets in one single platform whilst being easily reproducible maintainable and easy to extend future capabilties. Unlike operational monitoring system or predictive analytics platforms the aim of thsi system is to allow users to investigate patterns, trends and relattionships across many different regiosn and time periods.

Keeping this in mind here are some constrainst that will inform the design of this application:
- All the datasets are observational (missing data if measuirng instruments are down)
- Different temporal resolution and update frequencies
- The requirement for clean historical data (2020 onwards per Objective 1.5.1)
- The requirement for deployment alongside local set-ups

Theese constraints have motivated a modular streamlit application with a remote relational database that priortises user interactivity over computational complexity.

---

## 2.2 High-level System Architechture

The systems aime to adopt a layered archiechture that seperates different functioanlties such as data ingestion, data validation, database storage, application logic and UI. This allows for the isolation of different funtionalties which allows for easier maintainabilty and extension of functionality in the future.

<p align="center">
    <img src="../assets/high_level_system_architechture.svg" alt="High level system architechture" >
</p>

At the high level the system consists of the following system componenets:
- External data sources
- Autoamted ingestion and validation layer
- Reliable Relational Database
- Application layer for data query and state managment 
- an interactive UI for the dashboard 

One of the key considerations is the use of a relational database so that the dashboard does not have to rely on external APIs which can be subject to rate limits and latency. Instead the use of the relational database (Supabase) allows all visulisations to come from validated data that follow a consistent schema which overal prevents user experience from being degraded if external API fail.

To support a much smoother UX the application aims to make use of query-level caching with a time-to-live(TTL) mechanism ehich reduce the amount of redundant DB reads when visualising differnt plots or switching between tabs which will improve the applications responsivness to the users interaction making the experience much better and computationaly effecient.

Another consideration is making use of pagination logic when retrieving data for a long period of time. This ensures that results are not truncated over long historacl time period queries and also make sure that the Supabase client does not exceed the platform imposed limits.

To ensure that data is up to date a background data update mechanism is to be implmented so that new data can be added whenever the application is started to maintain the database. This background process should run independent of the UI to allow the user to use the application while data is refreshed. Once the data refresh is complete any cached query results are cleared and the new data is loaded to allow for the user to interact with the latest data

Overall this architechture ensures that the dashboard only operates on validated consistent data while remaining responsive. 

The figure above demonstrates the high-level system architechture highlighting the flow of data from external sources to being validated and then acessible to the user via an interactive UI.

---

## 2.3 Abstraction & Decomposition 

To manage the complexity of the application and simplify the UI abstraction techniques and decompistion techniques have been applied on the system level for the design of this application. 


At the user level, abstraction has been applied to ensure that the interaction a user has is limited to high-level analytical concepts such as time ranges, geographic regions, and energy metrics. The user is abstracted away from the low-level details such as the database schemas, API specefic details. For example whwn a user wants to select a time range for a certain region the user does not have to construct SQL query but rather filter through the data via an intuitive UI componnents. This allows non-technical user to make use of the system and explore the different tools without having technical abilty as the limiting factor.

<br>
<p align="center">
    <img src="../assets/data_abstraction.svg" alt="Data Abstraction" width="20%" height="20%">
</p>
<br>

The figure above illustrates how data handeling at the low-level is abstracted away from the UI


At the application level, the seperate data acess, preprocessing and transformation within encapsulated data loader components. This allows the application to recieve data in a cleanly structured manner rather than having to recieve the data in the form of a raw API response. This ensures that changes to the data sources formats or storage schemas do not affect the UI or any of the visulisations.

The overall problem of implemting the dashboard is further addresed through the use of decomposition. The system is divided into distinct functional components that each serve a seperate purpose. Theese functional components are further divided and grouped by a shared system function and placed into modules to allow for better maintanibilty and extension of future work. For example a data modulel can have following functional componenets; data acess, validation, ingestion.


Decomposition will also be applied on the UI level, where the visulisations will be grouped by the domain of the data rather than chart type. The dashboard will seperate views into distinct sections for electricty demand, carbon intensity & weather variables. This structure mirrors the underlying data decomposition and allows users to reason abou the different domains seperatly while maintaing a consistent interactive UI. This also prevents cocgnitve overload whn exploring data allowing them to explore different aspects of the energy system independetly.

<br>
<p align="center">
    <img src="../assets/sytem_decomposition.svg" alt="System decomposition">
</p>
<br>

The figure above demonstrates how the application is broken down into single-responsibilty components for easier testing and devlopment.


Decomposition will allow for incremental development and the testing of individual components whcih reduces the risk of having a chain of failures. Additionaly this allows for new features to be introduced without much refactoring to the old code as functional components work in isolation. This also allows for a better understanding of the system behaviour as each function has a well defined behaviour.

Both abstraction & decomposition will ensure that the system remains as flexible as possible & maintainable. Theese design principles allow the dashboard to support complex exploratory analysis while maintaining a clear interactive UI for the users.

---

## 2.4 Data Design 

This project makes use of a remote relational database to store large validated  historical dataset whilst supporting interactive analysis at scale. A database-backed design was mainly chosen instead of a flat file on a local set up to ensure query perfomance and updatebality.

The data used in this project is mianly sourced form 2 providers each contributing differntly to the data richness of the uk energy system. 

For the electricity demand and system-level operation data is sources from the National Energy System Operator (NESO), the official legal body responsible for the uk electrical system. NESO also offers data for carbon intensity, generation mix & power flow. The data provided by NESO is authaurative and consistently structured. The data published has a sufficent temporal resolution and great historical depth. While the data is aggregated at regional level it is well suited to descriptive and comparitive analysis of the national energy demands.

Open Meteo is an open sourced historical archive of weather and environmental variables provided for free for hourly weather observations with a very large geographic coverage. Although regional weather cannot capture microclimates accurately it is sufficent to investigating the realtionships between energy related variables and weather based variables.



### 2.4.1 Why Supabase?

Supabase was chosen as the storage platform for the following reasons:
- A PostgreSQL instance with ACID guarantees and indexing for faster querying 
- A remote set up suitable for deployment 
- Simple integration from python via a client interface and some easily acessible API keys
- Can easily add on new tables for future extension work 

The supabase has also a very freindly API ehich will allow for smoother data ingestion 

### 2.4.2 Schema design 

The schema is organised arounnd the dimensions of time and region. The three main with validated historical data are the following:
- `historic_demand` - energy demand and power flow data
- `carbon_intensity` - carbon intensity and generation mix data
- `weather` -waether data

The following SQL defenitions willbe used to create the tbles and indexes for much faster querying. Theese queries can be executed in the Supabase SQL editor to repoduce results locally 

#### `weather` table

```sql
CREATE TABLE weather (
    id BIGSERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    region_id INTEGER NOT NULL,
    region_name TEXT NOT NULL,
    temperature REAL,
    humidity REAL,
    wind_speed REAL,
    cloud_cover REAL,
    precipitation REAL,
    UNIQUE(datetime, region_id)
);

CREATE INDEX idx_weather_datetime ON weather(datetime);
CREATE INDEX idx_weather_region ON weather(region_id);
```

#### `carbon_intensity` table

```sql
CREATE TABLE carbon_intensity (
    id BIGSERIAL PRIMARY KEY,
    datetime TIMESTAMPTZ NOT NULL,
    region_id INTEGER NOT NULL,
    region_name TEXT,
    forecast INTEGER,
    index TEXT,
    gen_biomass DECIMAL,
    gen_coal DECIMAL,
    gen_imports DECIMAL,
    gen_gas DECIMAL,
    gen_nuclear DECIMAL,
    gen_other DECIMAL,
    gen_hydro DECIMAL,
    gen_solar DECIMAL,
    gen_wind DECIMAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_carbon_intensity_datetime ON carbon_intensity(datetime);
CREATE INDEX idx_carbon_intensity_region ON carbon_intensity(region_id);
CREATE UNIQUE INDEX idx_carbon_intensity_datetime_region ON carbon_intensity(datetime, region_id);
```

#### `historic_demand` table

```sql
CREATE TABLE historic_demand (
    id BIGSERIAL PRIMARY KEY,
    datetime TIMESTAMPTZ NOT NULL UNIQUE,
    nd DOUBLE PRECISION,
    tsd DOUBLE PRECISION,
    england_wales_demand DOUBLE PRECISION,
    embedded_wind_generation DOUBLE PRECISION,
    embedded_wind_capacity DOUBLE PRECISION,
    embedded_solar_generation DOUBLE PRECISION,
    embedded_solar_capacity DOUBLE PRECISION,
    non_bm_stor DOUBLE PRECISION,
    pump_storage_pumping DOUBLE PRECISION,
    scottish_transfer DOUBLE PRECISION,
    ifa_flow DOUBLE PRECISION,
    ifa2_flow DOUBLE PRECISION,
    britned_flow DOUBLE PRECISION,
    moyle_flow DOUBLE PRECISION,
    east_west_flow DOUBLE PRECISION,
    nemo_flow DOUBLE PRECISION,
    nsl_flow DOUBLE PRECISION,
    eleclink_flow DOUBLE PRECISION,
    viking_flow DOUBLE PRECISION,
    greenlink_flow DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_historic_demand_datetime ON historic_demand(datetime);
```



### 2.4.3 Data Cleaning

Given that the datasets used in this project come from multiple sources that have different structures and temporal solution data must be standardised before it is storedd in the relational database. This therfore requires for a well deatiled cleaning stage so that it can be applied across all the data including the newly ingested data.


<br>
<p align="center">
    <img src="../assets/data_cleaning.svg" alt="Data Cleaning" >
</p>
<br>

The first stage in the cleanning requires the timestamp to be normalised to a single format. As some external providers may provide timestamps that are not timezone aware timezone normalisation will be crucial for temporal allignment.

The second step is to standardise the schema of the data to make sure that all fields have the same format. Additionaly some data may not come in the format that is alligned with the database schema. For example demand data does not come with a time stamp but rather in 2 seperate fields SETTELMENT_DATE and SETELMENT_PERIOD where setelement period is a number from 1 to 48 of half an hour increments, this needs to be processed into a timezone aware timestamp bbefore being added to the database.

The next step is to handle any duplicates. Composite keys (datetime, region) or primary keys(datetime) can be made to ensure that data has no duplicates. When usperting new data into Supabase there is functionality that allows Supabase to ignore duplicates that are being added so acts as a second line of defense to ensure that the relational database only conatins unique data points.

The next step is handling missing data. Rather than deleting all the records with missing fields the project will meaintain all records to reflect the obervational neture of the datasets and will perfom the filtering of missing values on the client level. This gives the possibilty of expanding investigational capabilties around incomplete data points in the future.

The final stage is to have sanity & range checks to detect any implausible data points such as having a neagtive demand or a temapture over 100. Record sthat fail to pass this stage are not added to the Database as they are unrealistic and physically impossible to ensure only validated data is used in the dashboard 

Collectively the steps above ensure that the datasets are consistent and that they are suitable for exploratory analysis.


### 2.4.4 Data Quality 

To make sure that the data is of good quality and check how much of the data is inline with the standards set above a dedicated notebook can be found in `notebooks\data_analysis.ipynb`. This notebook can also be used to bulk add data to a seperate database instance for local experimentation.

The first quality check that was assesed is temporal completeness which is simply a measure of how many timesatmps you have and the amount of timesatmps that you expect to have. This is used to 

| Dataset            | Expected Coverage        | Observed Coverage        | Time Gaps Detected | Action Taken              |
|--------------------|--------------------------|--------------------------|--------------------|---------------------------|
| Historic Demand    | 2020–present (hourly)    | 2020–present             | No                 | Accepted                  |
| Carbon Intensity   | 2020–present (hourly)    | 2020–present             | Minor gaps         | Accepted & Documented     |
| Weather            | 2020–present (hourly)    | 2020–present             | No                 | Accepted                  |

The second quality check is to make sure that there are no duplicates in the data records that will be uplaoded. This was perfomed by using composite keys(`datetime`, `region_id`) for where regions are avaialable and if not then use `datetime` as the primary key

| Dataset            | Key Used                    | Duplicates Found | Resolution Strategy      |
|--------------------|-----------------------------|------------------|--------------------------|
| Historic Demand    | datetime                    | No               | No action required       |
| Carbon Intensity   | datetime + region_id        | Yes (2,982)      | Deduplicated / upserted  |
| Weather            | datetime + region_id        | No               | No action required       |


The third quality check was a missing value analysis to see how many incomplete obervations are made within each dataset.

| Dataset            | Fields Affected        | Missing Values Present | Handling Strategy              |
|--------------------|------------------------|------------------------|--------------------------------|
| Historic Demand    | Minor operational fields | Yes (low proportion) | Retained, visually apparent    |
| Carbon Intensity   | Generation mix fields  | Yes                   | Retained, documented           |
| Weather            | Precipitation, cloud cover | Yes              | Retained, no imputation        |


The last quality check was to make sure that Sanity and Range Checks were implmented to the 3 seperate datasets.

| Dataset            | Check Performed            | Issues Detected | Action Taken              |
|--------------------|----------------------------|-----------------|---------------------------|
| Historic Demand    | Non-negative demand        | No              | Accepted                  |
| Carbon Intensity   | Non-negative generation    | Rare anomalies  | Excluded                  |
| Weather            | Physical plausibility      | No              | Accepted                  |


## 2.5 Design Trade-offs

The design of the Uk energy dahsboard involved a series of delibrate deciosn that balance explotaory capbility, system complexity and perfomance whilst remianing in the project scope. Rather than maximising the technical complexity or the number of the features there was a bigger focus on enabling reliable exploratory analysis

The choice for the dashboard framework is a python-based lightweight library called streamlit. Streamlit has great support for cloud deployment offering its own free solutions for public project for free under the "streamlit cloud" franchise. Additionaly streamlit is very easy to run locally and does not need any additional steps accept for being downloaded via pip. However this lighrweight framework abstract away from the finegrailed customisations other frameworks can provide. However this was considered an acceptable trade off as the project is analytical rather than presantation driven objectives.

As the project is to be deployed, a remote relational database was chosen over a flat file. This will introduce a lot of complexity to set up the relational database and make sure that it can work. However this additional complexity is acceptable as it will allow for much more effecient querying and indexing and also allow both local and deployed set ups to run smoothly as the database will be acessed the same way.

## References

Department for Business, Energy & Industrial Strategy (2021) *Net Zero Strategy: Build Back Greener*. Available at: [https://assets.publishing.service.gov.uk/media/6194dfa4d3bf7f0555071b1b/net-zero-strategy-beis.pdf](https://assets.publishing.service.gov.uk/media/6194dfa4d3bf7f0555071b1b/net-zero-strategy-beis.pdf) 

RenewableUK (2024) *Energy Bible confirms renewables now provide over half of the UK’s electricity generation*. Available at: [https://www.renewableuk.com/news-and-resources/press-releases/energy-bible-confirms-renewables-now-provide-over-half-of-the-uk-s-electricity-generation/](https://www.renewableuk.com/news-and-resources/press-releases/energy-bible-confirms-renewables-now-provide-over-half-of-the-uk-s-electricity-generation/)

National Energy System Operator (NESO) (2024) *NESO Data and Energy Information*. Available at: [https://www.neso.energy](https://www.neso.energy) 







