#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import re
import dateutil.parser
import babel
from flask import render_template, request, Response, flash, redirect, url_for, abort
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, app, Venue, Show, ShowTime, Artist

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


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
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []

    # get all distinct city, states
    distinct_venues = db.session.query(
        Venue.city, Venue.state).distinct().all()

    # for each pair, get venue info and shows info
    for city, state in distinct_venues:
        data_entry = {
            'city': city,
            'state': state,
            'venues': []
        }

        venues = db.session.query(Venue.id, Venue.name).filter(
            Venue.city == city, Venue.state == state).all()

        for v_id, v_name in venues:
            venue_entry = {
                'id': v_id,
                'name': v_name
            }
            venue_entry['num_upcoming_shows'] = db.session.query(ShowTime.start_time).join(
                Show).filter(Show.venue_id == v_id, ShowTime.start_time > datetime.now()).count()

            data_entry['venues'].append(venue_entry)

        data.append(data_entry)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    data = []
    term = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike('%' + term + '%')).all()

    response = {
        "count": len(venues),
        "data": []
    }

    for venue in venues:
        num_upcoming = 0

        for show in Show.query.all():
            if show.venue.id == venue.id and show.show_time.start_time > datetime.now():
                num_upcoming = num_upcoming+1

        response["data"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming
        })

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)

    # show non existent
    if venue is None:
        abort(404)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }

    # build up info about shows
    all_shows = Show.query.all()
    shows = filter(lambda x: x.venue_id == venue_id, all_shows)
    uc, pc = 0, 0

    pc = db.session.query(Show).join(ShowTime).filter(
        Show.venue_id == venue_id, ShowTime.start_time <= datetime.now()).count()
    uc = db.session.query(Show).join(ShowTime).filter(
        Show.venue_id == venue_id, ShowTime.start_time > datetime.now()).count()

    past_shows = db.session.query(Artist.id, Artist.name, Artist.image_link, ShowTime.start_time).select_from(
        Artist).join(Show).join(ShowTime).filter(Show.venue_id == 4, ShowTime.start_time <= datetime.now()).all()
    upcoming_shows = db.session.query(Artist.id, Artist.name, Artist.image_link, ShowTime.start_time).select_from(
        Artist).join(Show).join(ShowTime).filter(Show.venue_id == 4, ShowTime.start_time > datetime.now()).all()

    for show in past_shows:
        a_id, a_name, a_link, s_start = show
        data["past_shows"].append({
            "artist_id": a_id,
            "artist_name": a_name,
            "artist_image_link": a_link,
            "start_time": s_start.strftime("%Y-%m-%d %H:%M:%S")
        })

    for show in upcoming_shows:
        a_id, a_name, a_link, s_start = show
        data["past_shows"].append({
            "artist_id": a_id,
            "artist_name": a_name,
            "artist_image_link": a_link,
            "start_time": s_start.strftime("%Y-%m-%d %H:%M:%S")
        })

    data["past_shows_count"] = pc
    data["upcoming_shows_count"] = uc

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # create venue object
    form = VenueForm()
    if form.validate_on_submit():   
        try:
            venue = Venue(
                name=request.form['name'],
                city=request.form['city'],
                state=request.form['state'],
                address=request.form['address'],
                phone=request.form['phone'],
                genres=request.form.getlist('genres'),
                facebook_link=request.form['facebook_link'],
                image_link=request.form['image_link'],
                website=request.form['website_link'],
                seeking_talent=request.form.get('seeking_talent', 'n') == 'y',
                seeking_description=request.form['seeking_description']
            )

            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occured. Venue ' +
                  request.form['name'] + ' could not be listed!')
        finally:
            db.session.close()
    else:
        for field, errorMessages in form.errors.items():
            for err in errorMessages:
                flash("Error: " + err)
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
      venue = Venue.query.get(venue_id)

      if venue is None:
        abort(404)
      
      db.session.delete(venue)
      db.session.commit()
      flash('Venue "' + venue.name + '" has been removed successfully.')
    except:
      flash('Cannot delete! This venue has one or more shows associated with it.')
      db.session.rollback()
    finally:
      db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = []
    for artist in Artist.query.all():
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    term = request.form.get('search_term')
    artists = Artist.query.filter(Artist.name.ilike('%' + term + '%')).all()

    response = {
        "count": len(artists),
        "data": []
    }

    for artist in artists:
        num_upcoming = 0
        for show in Show.query.all():
            if show.artist.id == artist.id and show.show_time.start_time > datetime.now():
                num_upcoming = num_upcoming+1

        response["data"].append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming
        })

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)

    # show non existent
    if artist is None:
        abort(404)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0
    }

    # build up info about shows
    uc, pc = 0, 0

    pc = db.session.query(Show).join(ShowTime).filter(
        Show.artist_id == artist_id, ShowTime.start_time <= datetime.now()).count()
    uc = db.session.query(Show).join(ShowTime).filter(
        Show.artist_id == artist_id, ShowTime.start_time > datetime.now()).count()

    past_shows = db.session.query(Venue.id, Venue.name, Venue.image_link, ShowTime.start_time).select_from(
        Venue).join(Show).join(ShowTime).filter(Show.venue_id == 4, ShowTime.start_time <= datetime.now()).all()
    upcoming_shows = db.session.query(Venue.id, Venue.name, Venue.image_link, ShowTime.start_time).select_from(
        Venue).join(Show).join(ShowTime).filter(Show.venue_id == 4, ShowTime.start_time > datetime.now()).all()

    for show in past_shows:
        v_id, v_name, v_link, s_start = show
        data["past_shows"].append({
            "venue_id": v_id,
            "venue_name": v_name,
            "venue_image_link": v_link,
            "start_time": s_start.strftime("%Y-%m-%d %H:%M:%S")
        })

    for show in upcoming_shows:
        v_id, v_name, v_link, s_start = show
        data["past_shows"].append({
            "venue_id": v_id,
            "venue_name": v_name,
            "venue_image_link": v_link,
            "start_time": s_start.strftime("%Y-%m-%d %H:%M:%S")
        })

    data["past_shows_count"] = pc
    data["upcoming_shows_count"] = uc

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    if artist is None:
        abort(404)

    # TODO: populate form with fields from artist with ID <artist_id>
    form.city.data = artist.city
    form.facebook_link.data = artist.facebook_link
    form.name.data = artist.name
    form.phone.data = artist.phone
    form.seeking_description.data = artist.seeking_description
    form.state.data = artist.state
    form.website_link.data = artist.website
    form.image_link.data = artist.image_link

    if artist.seeking_venue:
        form.seeking_venue.data = 'y'
    else:
        form.seeking_venue.data = 'n'

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        artist = Artist.query.get(artist_id)

        if artist is None:
            abort(404)

        artist.name = request.form['name']
        artist.phone = request.form['phone']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.genres = request.form.getlist('genres')
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.website = request.form['website_link']
        artist.seeking_venue = request.form.get('seeking_venue', 'n') == 'y'
        artist.seeking_description = request.form['seeking_description']

        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    if venue is None:
        abort(404)

    # TODO: populate form with fields from artist with ID <artist_id>
    form.city.data = venue.city
    form.facebook_link.data = venue.facebook_link
    form.name.data = venue.name
    form.phone.data = venue.phone
    form.seeking_description.data = venue.seeking_description
    form.state.data = venue.state
    form.website_link.data = venue.website
    form.image_link.data = venue.image_link
    form.address.data = venue.address

    if venue.seeking_talent:
        form.seeking_talent.data = 'y'
    else:
        form.seeking_talent.data = 'n'

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        venue = Venue.query.get(venue_id)

        if venue is None:
            abort(404)

        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.website = request.form['website_link']
        venue.seeking_talent = request.form.get('seeking_talent', 'n') == 'y'
        venue.seeking_description = request.form['seeking_description']
        db.session.commit()
    except Exception as e:
        print(e)
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
    # called upon submitting the new artist listing form
    form = ArtistForm()
    if form.validate_on_submit():
        artist = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            facebook_link=request.form['facebook_link'],
            image_link=request.form['image_link'],
            website=request.form['website_link'],
            seeking_venue=request.form.get('seeking_venue', 'n') == 'y',
            seeking_description=request.form['seeking_description']
        )
        # TODO: insert form data as a new Venue record in the db, instead
        # TODO: modify data to be the data object returned from db insertion
        try:
            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
    else:
        for field, errorMessages in form.errors.items():
            for err in errorMessages:
                flash("Error: " + err)
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    shows = Show.query.all()
    for show in shows:
        venue = show.venue
        artist = show.artist
        show_time = show.show_time
        item = {
            "venue_id": venue.id,
            "venue_name": venue.name,
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show_time.start_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data.append(item)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        venue = Venue.query.get(request.form['venue_id'])
        show_time = ShowTime(start_time=request.form['start_time'])
        artist = Artist.query.get(request.form['artist_id'])
        show = Show()
        show.artist = artist
        show.venue = venue
        show.show_time = show_time
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except Exception as e:
        print(e)
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
