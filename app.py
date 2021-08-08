#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artists = db.relationship('Artist')
    venues = db.relationship('Venue')
    start_time = db.Column(db.DateTime)


class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship(
        'Show', backref=db.backref('artist_shows', lazy=True))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))


class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship(
        'Show', backref=db.backref('venue_shows', lazy=True))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = [{
        "city": j.city,
        "state": j.state,
        "venues": [{
            "name": i.name,
            "id": i.id
        } for i in Venue.query.filter(Venue.city == j.city, Venue.state == j.state)]

    } for j in Venue.query.order_by(Venue.state)]

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = '%{}%'.format(request.form.get('search_term', '').lower())
    query = Venue.query.filter(Venue.name.ilike(search_term))
    response = {
        "count": query.count(),
        "data": query
    }

    return render_template('pages/search_venues.html',
                           results=response,
                           search_term=request.form.get('search_term', '')
                           )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    i = Venue.query.filter_by(id=venue_id).all()

    data_list = [{
        "id": i[0].id,
        "name": i[0].name,
        "genres": i[0].genres,
        "address": i[0].genres,
        "city": i[0].city,
        "state": i[0].state,
        "phone": i[0].phone,
        "website": i[0].website,
        "facebook_link": i[0].facebook_link,
        "seeking_talent": i[0].seeking_talent,
        "seeking_description": i[0].seeking_description,
        "image_link": i[0].image_link,
        "past_shows": [{
            "artist_id": j.artist_id,
            "artist_name": Artist.query.filter(j.artist_id == Artist.id).first().name,
            "artist_image_link": Artist.query.filter(j.artist_id == Artist.id).first().image_link,
            "start_time": j.start_time
        } for j in Show.query.all() if j.id == venue_id and j.start_time < datetime.now()],
        "upcoming_shows": [{
            "artist_id": j.artist_id,
            "artist_name": Artist.query.filter(j.artist_id == Artist.id).first().name,
            "artist_image_link": Artist.query.filter(j.artist_id == Artist.id).first().image_link,
            "start_time": j.start_time
        } for j in Show.query.all() if j.id == venue_id and j.start_time > datetime.now()],
    }]
    data_list[0]["past_shows_count"] = len(data_list[0]["past_shows"])
    data_list[0]["upcoming_shows_count"] = len(data_list[0]["upcoming_shows"])

    data = data_list[0]
    return render_template('pages/show_artist.html', artist=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    facebook_link = request.form.get('facebook_link')
    genres = request.form.get('genres')

    try:
        venue = Venue(name=name, city=city, state=state, address=address, phone=phone,
                      genres=genres, facebook_link=facebook_link)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + name + ' was successfully listed!')

    except:
        db.session.rollback()
        flash('An error occurred. Venue ' + name + ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()

    except:
        db.session.rollback()

    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    return render_template('pages/artists.html', artists=Artist.query.order_by('id').all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = '%{}%'.format(request.form.get('search_term', '').lower())
    query = Artist.query.filter(Artist.name.ilike(search_term))
    response = {
        "count": query.count(),
        "data": query
    }
    return render_template('pages/search_artists.html',
                           results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    i = Artist.query.filter_by(id=artist_id).all()

    data_list = [{
        "id": i[0].id,
        "name": i[0].name,
        "genres": i[0].genres,
        "city": i[0].city,
        "state": i[0].state,
        "phone": i[0].phone,
        "website": i[0].website,
        "facebook_link": i[0].facebook_link,
        "seeking_venue": i[0].seeking_venue,
        "seeking_description": i[0].seeking_description,
        "image_link": i[0].image_link,
        "past_shows": [{
            "venue_id": j.venue_id,
            "venue_name": Venue.query.filter(j.venue_id == Venue.id).first().name,
            "venue_image_link": Venue.query.filter(j.venue_id == Venue.id).first().image_link,
            "start_time": j.start_time
        } for j in Show.query.all() if j.id == artist_id and j.start_time < datetime.now()],
        "upcoming_shows": [{
            "venue_id": j.venue_id,
            "venue_name": Venue.query.filter(j.venue_id == Venue.id).first().name,
            "venue_image_link": Venue.query.filter(j.venue_id == Venue.id).first().image_link,
            "start_time": j.start_time
        } for j in Show.query.all() if j.id == artist_id and j.start_time > datetime.now()],
    }]
    data_list[0]["past_shows_count"] = len(data_list[0]["past_shows"])
    data_list[0]["upcoming_shows_count"] = len(data_list[0]["upcoming_shows"])

    data = data_list[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter(id == artist_id).first()

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    try:
        artist = Artist.query.filter(id == artist_id).first()
        artist.name = request.form.get('name')
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.genres = request.form.get('genres')
        artist.facebook_link = request.form.get('facebook_link')
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter(id == venue_id).first()

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    try:
        venue = Venue.query.filter(id == venue_id).first()
        venue.name = request.form.get('name')
        venue.city = request.form.get('city')
        venue.address = request.form.get('address')
        venue.state = request.form.get('state')
        venue.phone = request.form.get('phone')
        venue.genres = request.form.get('genres')
        venue.facebook_link = request.form.get('facebook_link')
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    facebook_link = request.form.get('facebook_link')
    genres = request.form.get('genres')

    artist = Artist(name=name, city=city, state=state, phone=phone,
                    facebook_link=facebook_link, genres=genres)

    try:
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + name + ' was successfully listed!')

    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + name + ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

    data = [{
        "venue_id": i.venue_id,
        "venue_name": Venue.query.filter(id == i.venue_id),
        "artist_id": i.artist_id,
        "artist_name": Artist.query.filter_by(id=i.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=i.artist_id).first().image_link,
        "start_time": i.start_time
    } for i in Show.query.all()]

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')

    new_show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time)

    try:
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
