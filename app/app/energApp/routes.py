import pandas as pd
from flask import render_template, Blueprint, request
from flask_login import login_required, current_user

from .forms import BuildingForm
from .models import db, Building
from .predict import predict_energy_consumption
from .graph import create_plot

main_bp = Blueprint('main_bp', __name__,
                    template_folder='templates',
                    static_folder='static')
prediction = None


@main_bp.route('/')
@login_required
def index():
    global prediction
    building_query = Building.query.filter_by(user_id=current_user.id)
    buildings = pd.read_sql(building_query.statement, building_query.session.bind)
    if len(buildings) > 0:
        prediction = predict_energy_consumption(buildings)

    return render_template('index.html', prediction=prediction)


@main_bp.route('/predictions')
@login_required
def predictions_page():
    global prediction
    building_query = Building.query.filter_by(user_id=current_user.id)
    buildings = pd.read_sql(building_query.statement, building_query.session.bind)
    plots = []

    if len(buildings) > 0:
        prediction = predict_energy_consumption(buildings)
        for _, g in prediction.groupby("building_id"):
            plots.append(create_plot([1, 1, 1, 1], g))

    return render_template('predictions.html',
                           buildings=buildings,
                           plots=plots)


@main_bp.route('/faq')
def faq_page():
    return render_template('faq.html')


@main_bp.route('/plot', methods=['GET', 'POST'])
def change_meters():
    prediction_building = prediction.loc[prediction["building_id"] == int(request.args["building"])]

    meter0 = int(request.args["m0"])
    meter1 = int(request.args["m1"])
    meter2 = int(request.args["m2"])
    meter3 = int(request.args["m3"])
    return create_plot([meter0, meter1, meter2, meter3], prediction_building)


@main_bp.route('/buildings', methods=['GET', 'POST'])
@login_required
def buildings_page():
    building_form = BuildingForm(request.form)
    if request.method == 'POST':
        if building_form.validate():
            building = Building(name=request.form.get('name'),
                                primary_use=request.form.get('primary_use'),
                                square_feet=request.form.get('square_feet'),
                                year_built=request.form.get('year_built'),
                                floorcount=request.form.get('floorcount'),
                                latitude=request.form.get('latitude'),
                                longitude=request.form.get('longitude'),
                                user_id=current_user.id)
            db.session.add(building)
            db.session.commit()

    buildings = Building.query.filter_by(user_id=current_user.id).all()
    return render_template('building.html', buildings=buildings, form=BuildingForm())
