from typing import Tuple, List

from flask import Blueprint, request, render_template, url_for

import movie.adapters.repository as repo
from movie.domainmodel.movie import Movie
from movie.movie import services
from movie.movie.movie_forms import MovieSearchForm
from movie.utils.constants import MOVIE_BP, LIST_MOVIE_ENDPOINT, MOVIE_DETAILS_ENDPOINT

movie_blueprint = Blueprint(MOVIE_BP, __name__)


@movie_blueprint.route('/' + LIST_MOVIE_ENDPOINT, methods=['GET', 'POST'])
def movies():
    movies_per_page = int(request.args.get('movies_per_page', 5))
    form = MovieSearchForm()

    search_by = request.args.get('search_by', None)
    search_key = request.args.get('search_key', None)
    clear_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT)

    if form.validate_on_submit() or (search_by and search_key):
        movies, first_url, prev_url, next_url, last_url = parse_movie_search_request(
            movies_per_page, request, form, search_by, search_key)
    else:
        movies, first_url, prev_url, next_url, last_url = parse_movie_list_request(movies_per_page, request)

    return render_template(
        'movie/movie.html',
        form=form,
        title='Movie List',
        movies=movies,
        clear_url=clear_url,
        first_url=first_url,
        last_url=last_url,
        prev_url=prev_url,
        next_url=next_url
    )


def parse_movie_list_request(movies_per_page: int, request: request) -> Tuple[List[Movie], str, str, str, str]:
    prev_url = None
    first_url = None
    next_url = None
    last_url = None

    offset = int(request.args.get('offset', 0))
    movies = services.get_n_movies(movies_per_page, offset, repo.repo_instance)
    total_movies = services.get_movie_num(repo.repo_instance)

    if offset > 0:
        prev_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, offset=offset - movies_per_page,
                           movies_per_page=movies_per_page)
        first_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, movies_per_page=movies_per_page)
    if offset + len(movies) < total_movies:
        next_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, offset=offset + movies_per_page,
                           movies_per_page=movies_per_page)

        if total_movies % movies_per_page == 0:
            last_page = total_movies // movies_per_page - 1
        else:
            last_page = total_movies // movies_per_page
        last_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, offset=last_page * movies_per_page,
                           movies_per_page=movies_per_page)

    return movies, first_url, prev_url, next_url, last_url


def parse_movie_search_request(movies_per_page: int, request: request, form: MovieSearchForm,
                               search_by: str, search_key: str) -> Tuple[List[Movie], str, str, str, str]:
    movies = []
    total_movies = 0
    prev_url = None
    first_url = None
    next_url = None
    last_url = None

    search_func_map = {
        'Actor': services.get_n_movies_by_actor,
        'Actor fuzzy': services.get_n_movies_by_actor_fuzzy,
        'Director': services.get_n_movies_by_director,
        'Director fuzzy': services.get_n_movies_by_director_fuzzy,
        'Genre': services.get_n_movies_by_genre,
        'Genre fuzzy': services.get_n_movies_by_genre_fuzzy
    }

    offset = int(request.args.get('offset', 0))
    search_by = form.search_by.data or search_by
    search_key = form.search_text.data or search_key

    if search_by in search_func_map:
        movies, total_movies = search_func_map[search_by](offset, movies_per_page, repo.repo_instance, search_key)

    if offset > 0:
        prev_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, offset=offset - movies_per_page,
                           search_by=search_by,
                           search_key=search_key,
                           movies_per_page=movies_per_page)
        first_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, search_by=search_by, search_key=search_key,
                            movies_per_page=movies_per_page)
    if offset * movies_per_page + len(movies) < total_movies:
        next_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, offset=offset + movies_per_page,
                           search_by=search_by, search_key=search_key, movies_per_page=movies_per_page)

        if total_movies % movies_per_page == 0:
            last_page = total_movies // movies_per_page - 1
        else:
            last_page = total_movies // movies_per_page
        last_url = url_for(MOVIE_BP + '.' + LIST_MOVIE_ENDPOINT, offset=last_page * movies_per_page,
                           search_by=search_by, search_key=search_key, movies_per_page=movies_per_page)

    form.search_by.data = search_by
    form.search_text.data = search_key

    return movies, first_url, prev_url, next_url, last_url


@movie_blueprint.route('/' + MOVIE_DETAILS_ENDPOINT, methods=['GET'])
def movie_info():
    movie_id = request.args.get('movie_id')
    movie_dict = services.fetch_movie_info_by_id(movie_id, repo.repo_instance)

    movie_title = movie_dict.get('movie_title')
    movie_id = movie_dict.get('movie_id')
    movie_director_full_name = movie_dict.get('movie_director_full_name')
    movie_genres = movie_dict.get('movie_genres')
    movie_actors = movie_dict.get('movie_actors')
    movie_description = movie_dict.get('movie_description')
    movie_reviews = movie_dict.get('movie_reviews')

    if not movie_title:
        return render_template(
            'page404.html'
        )

    return render_template(
        'movie/movie_info.html',
        movie_title=movie_title,
        movie_id=movie_id,
        movie_director_full_name=movie_director_full_name,
        movie_genres=movie_genres,
        movie_actors=movie_actors,
        movie_description=movie_description,
        movie_reviews=movie_reviews
    )
