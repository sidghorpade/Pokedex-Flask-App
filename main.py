# 
# Project Header
# 
# Title: PokeDex App
# Class: CST 205
# Date: 05/17/2022
# Authors: Pedro Gutierrez, Siddhi Ghorpade, Jared Lopez-Leon, Justin Garcia
# Abstract: Pokedex Web application serving as a wiki for information about things from the Pokemon universe.
#           Search By Image feature made using an image classification model to predict a Pokemon based on an image.
#           
# Github Link: https://github.com/sidghorpade/Pokedex-Flask-App
# Pokebase Github Link: https://github.com/PokeAPI/pokebase

# main.py
# Description: Holds Flask application code and all routes to web pages

import os
from ensurepip import version
from info import preprocess_bio, preprocess_evolution, preprocess_versions, preprocess_stats, preprocess_habitats
from transformations import transform_image
from generations import gen_number_dict, game_dict, gen_descriptions, preprocess_gen_pokemon
from habitats import habitats_dict
import random
import pokebase as pb
import requests, json
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea
from flask import Flask, render_template, request, redirect,url_for, abort, send_from_directory
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap5
from pprint import pprint
from PIL import Image
from io import BytesIO
from poke_info import *
import imghdr

# creating flask appliation
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pokemain'
app.config['UPLOAD_PATH'] = 'uploads'

# passing app to bootstrap
bootstrap = Bootstrap5(app)

class Pokemon(FlaskForm):
    pokemon_name = StringField('Pokemon', validators=[DataRequired()] )   

#Pass search
@app.context_processor
def base():
    form = Pokemon()
    return dict(form=form)

# Worked on by: Jared
# Homepage
@app.route('/', methods=('GET', 'POST'))
def home():
    form = Pokemon()
    if form.validate_on_submit():
        info.pokemon =form.pokemon_name.data
        return redirect('/info',form=form, pokemon_name = info.pokemonn)
    return render_template('home.html')

# Worked on by: Pedro
# Generations route
@app.route('/generations')
@app.route('/generations/<id>')
def generations(id=None):
    generations = []

    if id != None:
        id = gen_number_dict[id]

    # Loop through the generations, 8 in total
    for gen in range(1, 9):
        generations.append(pb.generation(gen))
    
    gen_pokemon = {}
    gen_pokemon = preprocess_gen_pokemon(generations)

    # Key in this dictionary is the id passed into the route
    games = game_dict

    descriptions = gen_descriptions
        
    return render_template('generations.html', id=id, generations=generations, gen_pokemon=gen_pokemon, games=games, descriptions=descriptions)

# Worked on by: Pedro
# Habitats route
@app.route('/habitats')
@app.route('/habitats/<hab>')
def habitats(hab=None):
    # Get habitat to open on page load if passed into route
    if hab != None:
        hab = pb.pokemon_habitat(hab).name

    # Get a preprocessed habitats dictionary from habitats.py
    habitats = habitats_dict()

    return render_template('habitats.html', habitats=habitats, hab=hab)

# Worked on by: Pedro
# Pokemon info route
@app.route('/info/<transformation>/<name>')
def info(transformation, name):
    pokemon = pb.pokemon(name)
    
    # preprocess Pokemon's description
    bio = preprocess_bio(pokemon.species.flavor_text_entries)

    img_url = "https://cdn.traction.one/pokedex/pokemon/" + str(pokemon.id) + ".png"
    response = requests.get(img_url)

    # transforms image to be send to the template
    img = Image.open(BytesIO(response.content))
    img_tag = transform_image(img, transformation)

    stats = preprocess_stats(pokemon.stats)

    # try except to preprocess Pokemon's evolution data
    try:
        r = requests.get(pokemon.species.evolution_chain.url)
        data = r.json()
        evolution_dict = preprocess_evolution(data["chain"])
    except:
        print('error')
    # preprocess generation data
    gen_dict = preprocess_versions(pokemon.sprites.versions.__dict__, pokemon.id)

    habitats = {}
    # gets information of all habitats
    for i in range(1, 10):
        habitat = pb.pokemon_habitat(i)
        habitats[habitat.name] = habitat.pokemon_species
    
    # preprocess habitat data
    habitat_list = preprocess_habitats(habitats, pokemon.name)
    no_habitats = len(habitat_list) == 0
    
    return render_template('info.html', pokemon=pokemon, img_tag=img_tag, bio=bio, stats=stats, evolution_dict=evolution_dict, gen_dict=gen_dict, habitat_list=habitat_list, no_habitats=no_habitats)
  
# Worked on by: Justin and Jared
# Lists Pokemon types
@app.route('/types')
def types():
    return render_template('types.html')

# Worked on by: Justin
# Pokemon Type Pages
@app.route('/types/<type>')
def selectedType(type):
    poke_list = []

    i = 0
    while i < len(poke_info):
        temp_dict = {}

        for key in poke_info[i]:
            if poke_info[i]['type'] == type:
                temp_dict.update({key:poke_info[i][key]})

        if len(temp_dict) > 0:
            poke_list.append(temp_dict)

        i +=1
    
    limit = len(poke_list)
    return render_template('selectedType.html', poke_list = poke_list, type = type, limit = limit)

# Worked on by: Siddhi
# Validates an image upload
def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

# Worked on by: Siddhi
@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

# Worked on by: Siddhi
# Search by image route
@app.route('/searchByImage')
def index():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('searchByImage.html', files=files)

# Worked on by: Siddhi
@app.route('/searchByImage', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return "Invalid image", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return '', 204

# Worked on by: Siddhi
@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)
