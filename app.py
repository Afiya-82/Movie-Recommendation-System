import pickle
import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

def fetch_poster(movie_id):
    """
    Fetch the poster URL for a given movie ID using TMDB API.
    Implements retry and SSL bypass for stability.
    """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=10, verify=False)  # Disable SSL verification
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch poster: {e}")
    return None

def fetch_trending_movies():
    """
    Fetch a list of trending movies from TMDB API.
    """
    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={API_KEY}"
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, timeout=10, verify=False)  # Disable SSL verification
        response.raise_for_status()
        data = response.json()
        trending_movies = data.get('results', [])
        return trending_movies[:10]  # Return the top 10 trending movies
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch trending movies: {e}")
    return []

def recommend(movie):
    """
    Recommend similar movies based on the given movie title.
    """
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        poster = fetch_poster(movie_id)
        recommended_movie_posters.append(poster)
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names, recommended_movie_posters

# Streamlit UI
st.title('🎥 Movie Recommender System')

# Load the necessary data
try:
    movies = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    movie_list = movies['title'].values
except Exception as e:
    st.error(f"Error loading data: {e}")
    movie_list = []  # Fallback to an empty list if data fails to load

# Search Section
if len(movie_list) == 0:
    st.warning("No movies available to display. Please check your data files.")
else:

    selected_movie = st.selectbox(
        "Type or select a movie from the dropdown",
        movie_list  # Ensure this is a valid non-empty list
    )

    if st.button('Recommend'):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

        # Display Recommended Movies
        st.write("## Recommended Movies")
        for i in range(0, len(recommended_movie_names), 5):
            cols = st.columns(5)
            for j, col in enumerate(cols):
                if i + j < len(recommended_movie_names):
                    with col:
                        if recommended_movie_posters[i + j]:  # Check if the poster is available
                            st.image(recommended_movie_posters[i + j], use_container_width=True)
                        else:
                            st.text("No poster available")
                        st.caption(recommended_movie_names[i + j])

# Display Trending Movies Below Search Section
st.write("## Trending Movies")
trending_movies = fetch_trending_movies()
for i in range(0, len(trending_movies), 5):  # Display movies in rows of 5
    cols = st.columns(5)
    for j, col in enumerate(cols):
        if i + j < len(trending_movies):
            with col:
                movie = trending_movies[i + j]
                poster_path = movie.get('poster_path')
                title = movie.get('title', 'Unknown Title')
                if poster_path:
                    st.image(f"https://image.tmdb.org/t/p/w500/{poster_path}", use_container_width=True)
                else:
                    st.text("No poster available")
                st.caption(title)
