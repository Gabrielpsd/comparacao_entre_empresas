import dotenv 
import os, sys
import requests
import json
from groq import Groq
from datetime import datetime, timedelta, timezone
import tiktoken

dotenv.load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MAX_TIME_REVIEW = 2
BARSIZE = 20
LIMIT_MODEL = 12000
PASSOS_ADICIOANAIS = 2
MODELO_IA = "meta-llama/llama-4-scout-17b-16e-instruct"

prompt3 = """
Você é um analista especializado em avaliar reviews de negócios em múltiplas dimensões. 
Analise a seguinte review do Google Maps e atribua notas (em uma escala de 0 a 5) para o atendimento da empresa com base na avaliação geral do cliente que se trata sobre atendimento:
media: Nota média de 0 a 5
avaliacao: Avaliação geral do atendimento, considerando a experiência do cliente considerando (não esqueca o simbolo de porcentagem e coloque em formato de texto para): 
muito ruim = media 0 a 1; 
ruim = media 1 a 2;
regular = media 2 a 3;
bom = media 3 a 4;
excelente = media 4 a 5;
Após a analise agrupe as quantidades de reviews em cada categoria de avaliação, e calcule a média geral de todas as avaliações.
O agrupamento tira uma porcentagem de cada categoria em relação ao total de reviews(sempre na base 100, nunca entre 0 e 1, e sem casas decimais coloque os valores aproximados), e a média geral é a soma das notas dividida pelo número total de reviews.
em palavrasMaisCitadas retorne uma lista com as 3 palavras mais citadas na review e quandidade de vezes que foram citadas.
Sua resposta sera um json no seguinte formato: 

{
    "media_geral":"X%",
    "muito_ruim": "X%",
    "ruim": "X%",
    "regular": "X%",
    "bom": "X%",
    "excelente": "x%",
    "palavrasMaisCitadas": "[palavra1: Xvezes], [palavra2: Xvezes], [palavra3: Xvezes]",
    "resumo": "Sentimento geral e pontos-chave desta review"
}
 
"""
#lista de hospitais Fleury em São Paulo
unidades_fleury_sp = [
    "Fleury Santo Amaro – Av. Santo Amaro, 4584 – Santo Amaro, São Paulo – SP, 04701-200",
    "A+ Moema – Av. Indianópolis, 922 – Moema, São Paulo – SP, 04062-001",
    "Hermes Pardini Vila Mariana – Rua Domingos de Morais, 2422 – Vila Mariana, São Paulo – SP, 04035-000",
    "Fleury Campo Belo – Av. Vereador José Diniz, 3457 – Campo Belo, São Paulo – SP, 04603-003",
    "A+ Vila Andrade – R. Dep. João Sussumu Hirata, 120 – Vila Andrade, São Paulo – SP, 05716-100",
    "Fleury Pinheiros – R. Teodoro Sampaio, 1155 – Pinheiros, São Paulo – SP, 05405-050",
    "Hermes Pardini Perdizes – R. Cardoso de Almeida, 1316 – Perdizes, São Paulo – SP, 05013-001",
    "A+ Vila Leopoldina – R. Carlos Weber, 624 – Vila Leopoldina, São Paulo – SP, 05303-000",
    "Fleury Lapa – R. Barão de Jundiaí, 284 – Lapa, São Paulo – SP, 05073-010",
    "A+ Tatuapé Itapura – R. Itapura, 428 – Tatuapé, São Paulo – SP, 03310-000",
    "Fleury República – Av. República do Líbano, 635 – Ibirapuera, São Paulo – SP, 04501-900",
    "Hermes Pardini Sé – Praça da Sé, 100 – Sé, São Paulo – SP, 01001-000",
    "A+ Santa Cecília – R. Barão de Tatuí, 295 – Santa Cecília, São Paulo – SP, 01226-030",
    "Fleury Liberdade – R. Galvão Bueno, 40 – Liberdade, São Paulo – SP, 01506-000",
    "A+ Queiroz Filho – Av. Queiroz Filho, 498 – Vila Hamburguesa, São Paulo – SP, 05319-000",
    "Fleury Santana – R. Voluntários da Pátria, 4213 – Santana, São Paulo – SP, 02401-400",
    "Hermes Pardini Tucuruvi – Av. Tucuruvi, 808 – Tucuruvi, São Paulo – SP, 02305-000",
    "A+ Mandaqui – R. Voluntários da Pátria, 4565 – Mandaqui, São Paulo – SP, 02401-400",
    "Fleury Jaçanã – Av. Guapira, 2000 – Jaçanã, São Paulo – SP, 02266-000",
    "A+ Vila Maria – Av. Guilherme Cotching, 1580 – Vila Maria, São Paulo – SP, 02113-012"
]


hospitais_dasa_sp = [
    "Delboni – Unidade Brooklin – Av. Vereador José Diniz, 3687 – Brooklin, São Paulo – SP, 04603-004",
    "Delboni Auriemo – Unidade Ricardo Jafet – Av. Ricardo Jafet, 1550 – Ipiranga, São Paulo – SP, 04115-060",
    "Delboni – Unidade Vila Clementino – R. Dr. Diogo de Faria, 1379 – Vila Clementino, São Paulo – SP, 04037-005",
    "Delboni – Unidade Jardim Sul – R. Jandiatuba, 566 – Vila Andrade, São Paulo – SP, 05716-070",
    "Delboni – Unidade Itaim Bibi – R. João Cachoeira, 743 – Itaim Bibi, São Paulo – SP, 04535-902",
    "Alta Diagnósticos – Unidade Alto de Pinheiros – Praça São Marcos, 20 – Alto de Pinheiros, São Paulo – SP, 05455-050",
    "Delboni – Unidade Pompéia – Av. Pompéia, 1007 – Vila Pompéia, São Paulo – SP, 05023-000",
    "Lavoisier – Unidade Lapa Catão – R. Catão, 301 – Vila Romana, São Paulo – SP, 05041-000",
    "Delboni Auriemo – Unidade Butantã – Av. Jorge João Saad, 89 – Vila Progredior, São Paulo – SP, 05618-000",
    "Lavoisier – Unidade República – Av. Vieira de Carvalho, 176 – República, São Paulo – SP, 01046-001",
    "Delboni – Unidade Sumaré – Av. Sumaré, 1500 – Perdizes, São Paulo – SP, 05016-110",
    "Lavoisier – Unidade Teodoro Sampaio – R. Teodoro Sampaio, 1926 – Pinheiros, São Paulo – SP, 05406-150",
    "Lavoisier – Unidade Lapa – R. Tomé de Souza, 220 – Lapa, São Paulo – SP, 05079-000",
    "Lavoisier – Unidade Vila Maria – Av. Guilherme Cotching, 1580 – Vila Maria, São Paulo – SP, 02113-012",
    "Lavoisier – Unidade Vila Sabrina – Av. Professor Castro Júnior, 74 – Vila Sabrina, São Paulo – SP, 02138-030",
    "Alta Diagnósticos – Unidade Bela Vista – R. Peixoto Gomide, 515 – Bela Vista, São Paulo – SP, 01409-001",
    "Alta Diagnósticos – Unidade Peixoto Gomide – R. Peixoto Gomide, 515 – Bela Vista, São Paulo – SP, 01409-001",
    "Delboni – Unidade Mooca – Av. Paes de Barros, 663 – Mooca, São Paulo – SP, 03115-020",
    "Lavoisier – Unidade Vila Maria – Av. Guilherme Cotching, 1580 – Vila Maria, São Paulo – SP, 02113-012",
    "Lavoisier – Unidade Mooca – Av. Paes de Barros, 663 – Mooca, São Paulo – SP, 03115-020"
]



def analyze_text_using_groq(text: str) -> dict:
    client = Groq(

    api_key=os.environ.get("GROQ_API_KEY"),

    )


    chat_completion = client.chat.completions.create(

        messages=[

            {

                "role": "system",

                "content": prompt3,

            },
            {

                "role": "user",

                "content": limit_tokens(text, max_tokens=LIMIT_MODEL, model="gpt-4"),

            }

        ],
        response_format={"type": "json_object"},
        model=MODELO_IA,

    )

    return chat_completion.choices[0].message.content
    
    
def request_google_api(search_text: str) -> dict[str, list]:
    """
    Function to get the place ID of a location using Google Places API.
    """
    # Example URL for Google Places API
    
    url = "https://places.googleapis.com/v1/places:searchText"

    query = {   
                "textQuery": search_text + "no Brasil",
                "languageCode": "pt-BR",
                "pageSize": 1,
                "regionCode": "BR",        
            }
    
    
    headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': GOOGLE_API_KEY,
    'X-Goog-FieldMask': 'places.id,places.reviews,places.reviews.publishTime'
    }
    
    response = requests.post(url, json= query,headers=headers)

    if response.status_code == 200:
        data = response.json()
        # Check if the response contains places
        if "places" in data:
            return data
        else:
            pass 
    # If the request was successful, return the data
    else:
        print(f"Error: {response.status_code}")
        pass

def filter_recente_views(reviews: list) -> list:
    """
    Function to filter the reviews that are recent.
    """
    filtered_reviews = []

    # Calculate the threshold (2 years ago)
    two_years_ago = datetime.now(timezone.utc) - timedelta(days=MAX_TIME_REVIEW*365)  # Approximate (doesn't account for leap years)

    # Filter reviews
    filtered_reviews = [
        review for review in reviews
        if datetime.fromisoformat(review["publishTime"].replace("Z", "+00:00")) >= two_years_ago
    ]

    return filtered_reviews

def get_reviews(data: list) -> list:
    """
    Function to get the reviews of a place using Google Places API. 
    """
    reviewslist = []
    if "places" in data and len(data["places"]) > 0:
        place = data["places"][0]
        if("reviews" in place):
            for reviews in place["reviews"]:
                reviewslist.append({
                    "rating": reviews["rating"],
                    "originalText": reviews["originalText"]["text"],
                    "authorAttribution": reviews["authorAttribution"]["displayName"],
                    "publishTime": reviews["publishTime"],
                })
            return reviewslist
        else:
            return None
    else:
        return None

def print_review(reviews: list) -> None:
    for review in reviews:
            print(f"Review: {review['originalText']}")
            print(f"Rating: {review['rating']}")
            print(f"Author: {review['authorAttribution']}")
            print(f"Publish Time: {review['publishTime']}")
            print("-" * 40)
            print("-" * 40)
            
    print("Total reviews: ", len(reviews))
    print("-" * 40)
    print("#" * 60)
            
def progressBar(downloaded: int, totalFile: int, msg:str = '') -> None:
    """ this is a funtion that print a progress bar in 

    Args:
        downloaded (int): bytes donloaded 
        totalFile (int): total of bytes to be downloaded
    """
    progress = int(downloaded*BARSIZE/totalFile)
    completed = str(int(downloaded*100/totalFile)) + '%'
    # exit =  str(f''[',chr(9608)*progress,' ',completed, '.'*(BARSIZE),']',str(downloaded)+'/'+str(totalFile)')
    exit = f"Progresso: [{'='*progress}{' '*((BARSIZE)-progress)}]{completed} passo({str(downloaded)}/{str(totalFile)}): {msg[:80]}"
    sys.stdout.write(exit + '\r')
    sys.stdout.flush()  
    
def limit_tokens(text, max_tokens=12000, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return text
 
if __name__ == "__main__":
    
    reviewFleury = ''
    reviewDasa = ''
    reviewsFleury = []
    reviewsDasa = []
    requestFromGoogle =[]
    
    # --------------------------------- Analysing the Fleury hospitals in São Paulo ---------------------------------
    print("-" * 60)
    print("Realizando busca dos hospitais da rede Fleury em São Paulo...")
    
    for i in range(len(unidades_fleury_sp)):
        progressBar(i, len(unidades_fleury_sp)+PASSOS_ADICIOANAIS,f"Hospital: {unidades_fleury_sp[i]}")
        var = request_google_api(unidades_fleury_sp[i])
        if(var != None):

            requestFromGoogle.append(var)

    #print(f"Data from Google API: {dataFromGoogle}")
    if requestFromGoogle.__len__() > 0:
            
        for dataFromGoogle in requestFromGoogle:
            var = get_reviews(dataFromGoogle)
            if var != None:
                reviewsFleury.append(var)
            
        reviewsFleury = [review for reviews_list in reviewsFleury for review in reviews_list]

        reviewsFleury = filter_recente_views(reviews=reviewsFleury)
        
    # Write to file
        with open("promtReviewsFleury.txt", "w", encoding="utf-8") as f:
            f.write(prompt3)
            json.dump(reviewsFleury, f, indent=4)  # `indent=4` for pretty formatting

        progressBar(len(unidades_fleury_sp)+1, len(unidades_fleury_sp)+PASSOS_ADICIOANAIS,f"Analizandos dados recebidos"+' '*100)
        reviewFleury = analyze_text_using_groq('Avaliação: '.join([review['originalText'] for review in reviewsFleury]))
        progressBar(len(unidades_fleury_sp)+PASSOS_ADICIOANAIS, len(unidades_fleury_sp)+PASSOS_ADICIOANAIS,f"CONCLUIDO"+' '*100)
    else:
        print("Nanhuma resposta na busca das redes Fleury ")
        exit(1)
        
    # --------------------------------- Analysing the Dasa hospitals in São Paulo ---------------------------------
    print('   ')
    print("-" * 60)
    print("Realizando busca dos hospitais da rede Dasa em São Paulo...")
    
    requestFromGoogle = []
    for i in range(len(hospitais_dasa_sp)):
        progressBar(i, len(hospitais_dasa_sp)+PASSOS_ADICIOANAIS,f"Hospital: {hospitais_dasa_sp[i]}")
        requestFromGoogle.append(request_google_api(hospitais_dasa_sp[i]))

    #print(f"Data from Google API: {dataFromGoogle}")
    if requestFromGoogle.__len__() > 0:
        
        reviewsDasa = []
        
        for dataFromGoogle in requestFromGoogle:
            reviewsDasa.append(get_reviews(dataFromGoogle))
            
        reviewsDasa = [review for reviews_list in reviewsDasa for review in reviews_list]

        reviewsDasa = filter_recente_views(reviews=reviewsDasa)
        
    # Write to file
        with open("PromptReviewsDasa.txt", "w", encoding="utf-8") as f:
            f.write(prompt3)
            json.dump(reviewsDasa, f, indent=4)  # `indent=4` for pretty formatting
        
        progressBar(len(hospitais_dasa_sp)+1, len(hospitais_dasa_sp)+PASSOS_ADICIOANAIS,f"Analizandos dados recebidos"+' '*100)
        reviewDasa = analyze_text_using_groq('Avaliação:'.join([review['originalText'] for review in reviewsDasa]))
        progressBar(len(hospitais_dasa_sp)+PASSOS_ADICIOANAIS, len(hospitais_dasa_sp)+PASSOS_ADICIOANAIS,f"CONCUIDO"+' '*100)
        
    else:
        print("Nanhuma resposta na busca das redes Dasa ")
        exit(1)
        
    print("-"*60 )
    print("Modelo de IA utilizado: ", MODELO_IA)
    print("-"*60 )
    print(" ")
    print("-"*60 )
    print("Review dos hospitais Fleury: ")
    print("Quantidade de reviews: ", len(reviewsFleury))
    print(reviewFleury)
    print("-"*60 )
    print("Quantidade de reviews: ", len(reviewsDasa))
    print("Review dos hospitais Dasa : ")
    print(reviewDasa)
    
    