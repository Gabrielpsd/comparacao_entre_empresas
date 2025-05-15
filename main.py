import dotenv 
import os
import requests
import json

dotenv.load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def request_google_api(search_text: str) -> dict[str, list]:
    """
    Function to get the place ID of a location using Google Places API.
    """
    # Example URL for Google Places API
    
    url = "https://places.googleapis.com/v1/places:searchText"
    
    query = {"textQuery": search_text}
    
    headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': GOOGLE_API_KEY,
    'regionCode': 'Brazil',
    'X-Goog-FieldMask': 'places.id,places.reviews'
    }

    response = requests.post(url, json= query,headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        return None

def get_place_id(data: dict) -> str:
    """
    Function to get the place ID from the response data.As a lot of places are returned, we need to interact over all
    and get the one that are located in Brazil.
    """
    if "places" in data and len(data["places"]) > 0:
        for place in data["places"]:
            if "address" in place and "country" in place["address"]:
                if place["address"]["country"] == "Brazil":
                    return place["id"]
                
        return data["places"][0]["id"]
    else:
        print("No places found.")
        return None

def get_reviews(data: dict) -> dict:
    """
    Function to get the reviews of a place using Google Places API. 
    """
    if "places" in data and len(data["places"]) > 0:
        return data["places"][0]["reviews"]
    else:
        print("No places found.")
        return None
    
if __name__ == "__main__":
    
    placeID = ''
    photo=''
    reviews = []
    dataFromGoogle = request_google_api("Grupo Fleury")    
    print(f"Data from Google API: {dataFromGoogle}")
    if dataFromGoogle:
        placeID = get_place_id(dataFromGoogle)
        print(f"Place ID: {placeID}")
        reviews = get_reviews(dataFromGoogle)
        print(f"Reviews: {reviews}")
    else:
        print("No data found.")
        exit(1)