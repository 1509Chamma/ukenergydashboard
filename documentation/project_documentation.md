# 1. Introduction

<img src="../assets/uk_energy_dashboard.png" alt="Uk Energy Dashboard">


**Project Deployment:** [https://ukenergydashboard.streamlit.app](https://ukenergydashboard.streamlit.app) <br>
**Set-up Guide:** README.md <br>
**Assignment Brief:** documentation/assignment_brief.md <br>

---

## 1.1 Background & Motivation

The UK energy system is undergoing a significant structural transition, moving away from non-renewable sources of energy in order to achieve the net zero target proposed by the government (Department for Business, Energy & Industrial Strategy, 2021). This transition has led to noticeable changes in electricity demand patterns. As wind and solar energy generation are dependent on natural factors beyond direct human control, this has introduced increased volatility into electricity generation capabilities. Despite this, the UK was able to achieve 50.4% renewable electricity generation in the previous year (RenewableUK, 2024). While achieving net zero remains a work in progress, enabling people with tools to explore the problem can help raise awareness and understanding.

At the same time, there is a large amount of publicly available data that is scattered across multiple platforms and is not centralised into a single view capable of providing a holistic understanding of how different variables interact. Organisations such as the National Energy System Operator (NESO) provide multiple high-quality datasets and APIs for electricity demand, generation, and system operation (NESO, 2024). However, these datasets are published separately, meaning that non-technical users are unable to easily derive insights into how variables such as electricity demand, carbon intensity, and generation mix relate to one another.

<img src="../assets/neso_home_page.png" alt="Home page of NESO">


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

<img src="../assets/energy_dashboard.png" alt="EnergyDashboard">

The dashboard is primarily operational rather than analytical. In addition, access to historical data is limited, and users are largely restricted to viewing short-term or current system behaviour. There is minimal support for custom filtering, cross-dataset comparison, or exploratory analysis across time and regions. As a result, the platform is well suited for real-time operational monitoring but lacks historical depth and exploratory capability.

---

### Great Britain’s Monthly Energy Statistics (NESO)

The monthly statistics published by NESO provide credible summaries of long-term trends within the UK energy system (NESO, 2024). These reports aggregate demand, generation, and system performance metrics into structured visualisations suitable for official reporting and retrospective analysis. However, these visualisations are not updated in real time and provide limited flexibility for custom analysis.

<img src="../assets/neso_monthly_reports.png" alt="Great Britain’s Monthly Energy Statistics (NESO)">

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

<img src="../assets/solution_overview.svg" alt="Overview of the solution">

---

## References

Department for Business, Energy & Industrial Strategy (2021) *Net Zero Strategy: Build Back Greener*. Available at: [https://assets.publishing.service.gov.uk/media/6194dfa4d3bf7f0555071b1b/net-zero-strategy-beis.pdf](https://assets.publishing.service.gov.uk/media/6194dfa4d3bf7f0555071b1b/net-zero-strategy-beis.pdf) 

RenewableUK (2024) *Energy Bible confirms renewables now provide over half of the UK’s electricity generation*. Available at: [https://www.renewableuk.com/news-and-resources/press-releases/energy-bible-confirms-renewables-now-provide-over-half-of-the-uk-s-electricity-generation/](https://www.renewableuk.com/news-and-resources/press-releases/energy-bible-confirms-renewables-now-provide-over-half-of-the-uk-s-electricity-generation/)

National Energy System Operator (NESO) (2024) *NESO Data and Energy Information*. Available at: [https://www.neso.energy](https://www.neso.energy) 






