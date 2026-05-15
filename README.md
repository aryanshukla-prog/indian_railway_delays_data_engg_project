I went into this project expecting New Delhi to be the most dangerous junction in the network. It ranked 11th.
Itarsi Junction — a mid-sized junction in Madhya Pradesh that most people couldn't place on a map — came out on top. 382 trains pass through it. A delay there creates over 72,000 at-risk train pairs and ripples to 1,323 downstream stations. That's 18% of every station in India, from one junction.
That result is what this project is about.


The idea
Everyone knows Indian trains run late. What nobody seemed to have mapped was why, structurally — not operationally. Not "this train was late because of fog" but "which points in the network, when they fail, take everything else down with them?"
I'd been reading about how SREs model microservice failures — blast radius, cascade depth, dependency graphs. The railway network is the same problem in physical form. A delayed train at a shared junction is a slow database query fanning out to dependent services. So I built the tooling to measure it that way.
What I found
Itarsi Jn is the highest-leverage failure point in the network, not any of the famous terminal stations. It sits at the intersection of the Mumbai–Delhi and Chennai–Delhi corridors, which means almost every long-distance train in India passes through it at some point.
The contagion index I built — (shared_pairs × reachable_stations) / total_trains — puts it at 252,032, about 21% above second-placed Kanpur Central.


Junction                           TrainsAt-Risk                   PairsDownstream             StationsContagion           Index
ItarsiJn                           382                             72,771                       1,323                      252,032
Kanpur Central                     327                             53,301                       1,279                      208,477
Ghaziabad                          317                             50,086                       1,315                      207,770
Dd Upadhyaya Jn                    321                             51,360                       1,212                      193,920
Kalyan Jn                          312                             48,516                       1,189                      184,890


The second thing I found was more surprising — 46 train pairs are scheduled to arrive at the same junction at the exact same minute. That's not a delay. That's a scheduling conflict baked into the timetable. One of those trains is always going to wait, every single day it runs.



How it's built
The data is the Indian Railways timetable from Kaggle — 8,366 trains, one row each, with the full route stuffed into a single text column. First step was exploding that into ~180,000 individual stop records.
From there I built two parallel structures:
SQLite holds the flat records — every train, every stop, scheduled times, and weather data from Open-Meteo (free, no API key, 2 years of hourly data per station).
Neo4j holds the graph — stations as nodes, trains as directed edges through them. This is where the cascade queries live. The core query finds every train that passes through a given junction, then finds every other train that also passes through it, then measures the time gap between their scheduled arrivals. That gap is the risk window.

(Train A) --[STOPS_AT {arr: "23:45"}]--> (Itarsi Jn) <--[STOPS_AT {arr: "23:45"}]-- (Train B)
gap = 0 minutes → HIGH RISK

The Streamlit dashboard lets you explore any train's route, filter high-risk pairs by junction, and see the full contagion ranking interactively.



Stack

Python — parsing, pipeline, analysis
SQLite — local flat storage during development
Neo4j AuraDB — graph database, free cloud tier
Cypher — graph traversal queries
Streamlit + Plotly — dashboard


to run the file download the clean kaggle data csv IRCTC_cleaned.csv
run parsed data 
make a Neo4j account and copy id pass
run cascade analysis and the nodes will be created
venv\Scripts\activate where you have saved all your files
open the terminal and select that same location
run the dashboard

