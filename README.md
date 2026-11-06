# Does Weather Move Retail?

## What is this

This is my data project for STAT 386. I put together monthly retail sales from the Census Bureau and monthly weather for Salt Lake City to see if sales follow the seasons and if the weather has anything to do with it. My full write up is on my (http://localhost:7832/)

## The question

How do retail sales go up and down across the year and does weather have anything to do with it?

## What is in the data

Each row is one month for one store type from January 2016 to December 2025. That is 600 rows. The five store types are:

- Clothing
- Sporting goods and hobby and book stores
- Building materials and garden stores
- General merchandise stores
- Food and beverage stores

The columns are `year` and `month` and `category` and `sales_millions` and `avg_temp_f` and `total_precip_in` and `holiday_flag`. The holiday flag is 1 for November and December and 0 for every other month. Sales are not seasonally adjusted so the seasons stay in there.

## Where the data came from

- Sales come from the Census Bureau
(https://www.census.gov/retail) and you need a free key to get them
- Weather comes from Open-Meteo(https://open-meteo.com/en/docs/historical-weather-api) and it is free with no key. Weather data by Open-Meteo.com

I pulled everything on 2026-11-05. Census numbers get revised later so a new pull might look a little different.

## What is in this repo

```
scripts/fetch_census.py    gets the sales
scripts/fetch_weather.py   gets the weather
scripts/scrape.py          mashes it all into the final data
data/raw/                  the untouched pulls
data/processed/            the final data
report.qmd                 my analysis
```

## How to run it yourself

First install the packages with `uv sync`. Then get a free Census key and save it in a file called `census_key.txt`. Never share that file. It is already in my .gitignore so it stays off GitHub.

Then run these in order:

```bash
uv run python scripts/fetch_census.py
uv run python scripts/fetch_weather.py
uv run python scripts/scrape.py
```

Last thing is `quarto render report.qmd` to build the report.

## Stuff to know

- The sales are for the whole country but the weather is only Salt Lake City so they do not match perfectly
- The weather numbers come from a model and not real weather stations
- 2020 was a weird year because of the pandemic

[blog]: https://scerny.github.io
[census]: https://www.census.gov/retail
[meteo]: https://open-meteo.com/en/docs/historical-weather-api