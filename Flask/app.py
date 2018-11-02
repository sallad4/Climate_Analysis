import datetime as dt
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_
from flask import Flask, jsonify

# Est Database
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect existing database
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# References to tables
Station = Base.classes.station
Measurement = Base.classes.measurement

# session
session = Session(engine)

### Function to return most recent date and one year prior date
def get_newest_date():
    
    # most recent date
    first_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    newest_date = first_date[0]

    # most recent date minus a year
    year_ago_date = newest_date_minus_year(newest_date)

    return(newest_date, year_ago_date)

# subtract yr from date provided
def newest_date_minus_year(date_provided):
    year_ago, month, day = date_provided.split("-")
    year_ago = str(int(year_ago)-1)
    calculated_date = year_ago + '-' + month + '-' + day
    return calculated_date

# Flask
app = Flask(__name__)

# Flask Routes
@app.route("/")
def welcome():
    """List api routes."""
    
    return (
        f"Routes for Hawaiian Climate Analysis:<br/>"
        f"<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"--Precipitation Observations: One Year<br/>"
        f"<br/>"
        f"/api/v1.0/stations<br/>"
        f"--Observation Stations<br/>"
        f"<br/>"
        f"/api/v1.0/tobs<br/>"
        f"--Temperature Observations (tobs): Prior Year<br/>"
        f"<br/>"
        f"/api/v1.0/temps/&ltstart&gt/&ltend&gt<br/>"
        f"--Low, Avg, High temp for date or date range (format yyyy-mm-dd)"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Precipitation Observations: Prior Year"""

    # get latest date
    latest_date, new_date = get_newest_date()

    # select date and prcp
    rainy_days = session.query(Measurement.date, Measurement.prcp). \
        filter(Measurement.date >= new_date).order_by(Measurement.date).all()

    # convert results to dictionary
    prcp_dict = {}

    for rainy_day in rainy_days:
        prcp_dict[rainy_day.date] = rainy_day.prcp
    
    #Return the JSON representation of dictionary.
    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    #Return list of stations

    stations = session.query(Station.name, func.count(Measurement.prcp) ).\
        filter(Measurement.station == Station.station ).\
            group_by(Measurement.station).order_by(func.count(Measurement.prcp).desc()).all()

    #create dictionary of stations
    station_dict = {}
    
    for station in stations:
        station_dict[station.name] = station[1]

    return jsonify(station_dict)

@app.route("/api/v1.0/tobs")
def tobs():
    #Return list of Temp Observations (tobs) for the prior year
    
    # first select the latest date
    latest_date, year_before = get_newest_date()

    # select date and tobs for 12 months
    temp_obs = session.query(Measurement.date, Measurement.tobs). \
        filter(Measurement.date >= year_before).order_by(Measurement.date).all()

    # create tobs dict
    tobs_dict = {}

    for temp_ob in temp_obs:
        tobs_dict[temp_ob.date] = temp_ob.tobs

    return jsonify(tobs_dict)

@app.route("/api/v1.0/temps/<start_date>")
@app.route("/api/v1.0/temps/<start_date>/<latest_date>")
def temps(start_date, latest_date="blank"):
    #Return a JSON list of the minimum temperature, the average temperature, 
    # and the max temperature for a given start or start-end range.
    if (latest_date == "blank"):
        latest_date, year_before = get_newest_date()

    temp_range = session.query(Measurement.date, Measurement.tobs). \
        filter(and_(Measurement.date >= start_date, Measurement.date <= latest_date)).all()
    temp_df = pd.DataFrame(temp_range, columns=["date", "tobs"])

    temp_dict = {}
    temp_dict["TMIN"] = int(temp_df["tobs"].min())
    temp_dict["TAVG"] = temp_df["tobs"].mean()
    temp_dict["TMAX"] = int(temp_df["tobs"].max())

    print(f'temp_dict: {temp_dict}')

    return jsonify(temp_dict)

if __name__ == '__main__':
    app.run()