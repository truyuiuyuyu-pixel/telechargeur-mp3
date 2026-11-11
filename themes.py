# -*- coding: utf-8 -*-
"""
themes.py — Gestion des styles et thèmes musicaux (Amour, Halloween, Noël, Fête, Sport, Chill, etc.)
Permet de rechercher par style/ambiance et de proposer des morceaux cultes et pertinents.
"""

THEMES_CATALOG = {
    "amour": {
        "id": "amour",
        "name": "Amour & Romantique",
        "icon": "fa-heart",
        "color": "#f43f5e",
        "badge": "❤️ Amour & Romantique",
        "keywords": ["amour", "ammour", "love", "romantique", "romance", "mariage", "declaration", "saint-valentin", "couple", "coeur"],
        "description": "Les plus belles chansons d'amour et déclarations romantiques intemporelles",
        "tracks": [
            {"title": "Pour que tu m'aimes encore", "artist": "Céline Dion", "query": "Céline Dion Pour que tu maimes encore lyrics"},
            {"title": "Perfect", "artist": "Ed Sheeran", "query": "Ed Sheeran Perfect lyrics"},
            {"title": "I Will Always Love You", "artist": "Whitney Houston", "query": "Whitney Houston I Will Always Love You lyrics"},
            {"title": "All of Me", "artist": "John Legend", "query": "John Legend All of Me lyrics"},
            {"title": "Je t'aimais, je t'aime, je t'aimerai", "artist": "Francis Cabrel", "query": "Francis Cabrel Je taimais je taime lyrics"},
            {"title": "Someone Like You", "artist": "Adele", "query": "Adele Someone Like You lyrics"},
            {"title": "A Thousand Years", "artist": "Christina Perri", "query": "Christina Perri A Thousand Years lyrics"},
            {"title": "L'Hymne à l'amour", "artist": "Édith Piaf", "query": "Edith Piaf Hymne a lamour paroles"},
            {"title": "Say You Won't Let Go", "artist": "James Arthur", "query": "James Arthur Say You Wont Let Go lyrics"},
            {"title": "La vie en rose", "artist": "Édith Piaf", "query": "Edith Piaf La vie en rose paroles"}
        ]
    },
    "halloween": {
        "id": "halloween",
        "name": "Halloween & Horreur",
        "icon": "fa-ghost",
        "color": "#f97316",
        "badge": "🎃 Halloween & Horreur",
        "keywords": ["halloween", "allowen", "haloween", "hallowen", "horreur", "spooky", "peur", "citrouille", "fantome", "vampire", "zombie"],
        "description": "Les plus grands morceaux cultes et mystérieux pour frissonner à Halloween",
        "tracks": [
            {"title": "Thriller", "artist": "Michael Jackson", "query": "Michael Jackson Thriller lyrics"},
            {"title": "Ghostbusters (Theme)", "artist": "Ray Parker Jr.", "query": "Ray Parker Jr Ghostbusters lyrics"},
            {"title": "Spooky Scary Skeletons", "artist": "Andrew Gold", "query": "Andrew Gold Spooky Scary Skeletons lyrics"},
            {"title": "This Is Halloween", "artist": "The Nightmare Before Christmas", "query": "This Is Halloween The Nightmare Before Christmas lyrics"},
            {"title": "Monster Mash", "artist": "Bobby Boris Pickett", "query": "Bobby Pickett Monster Mash lyrics"},
            {"title": "Halloween Theme (Main Title)", "artist": "John Carpenter", "query": "John Carpenter Halloween Theme original"},
            {"title": "Somebody's Watching Me", "artist": "Rockwell", "query": "Rockwell Somebody's Watching Me lyrics"},
            {"title": "Highway to Hell", "artist": "AC/DC", "query": "AC DC Highway to Hell lyrics"},
            {"title": "Sweet Dreams", "artist": "Marilyn Manson", "query": "Marilyn Manson Sweet Dreams lyrics"},
            {"title": "Zombie", "artist": "The Cranberries", "query": "The Cranberries Zombie lyrics"},
            {"title": "Bury a Friend", "artist": "Billie Eilish", "query": "Billie Eilish Bury a friend lyrics"},
            {"title": "Disturbia", "artist": "Rihanna", "query": "Rihanna Disturbia lyrics"}
        ]
    },
    "noel": {
        "id": "noel",
        "name": "Noël & Fêtes",
        "icon": "fa-tree",
        "color": "#10b981",
        "badge": "🎄 Noël & Fêtes",
        "keywords": ["noel", "noël", "christmas", "fetes", "fêtes", "hiver", "sapin", "cadeaux"],
        "description": "Les classiques intemporels de Noël et fêtes de fin d'année",
        "tracks": [
            {"title": "All I Want for Christmas Is You", "artist": "Mariah Carey", "query": "Mariah Carey All I Want for Christmas Is You lyrics"},
            {"title": "Last Christmas", "artist": "Wham!", "query": "Wham Last Christmas lyrics"},
            {"title": "Jingle Bell Rock", "artist": "Bobby Helms", "query": "Bobby Helms Jingle Bell Rock lyrics"},
            {"title": "Vive le vent", "artist": "Chants de Noël", "query": "Vive le vent paroles"},
            {"title": "Petit Papa Noël", "artist": "Tino Rossi", "query": "Tino Rossi Petit Papa Noel paroles"},
            {"title": "Feliz Navidad", "artist": "José Feliciano", "query": "Jose Feliciano Feliz Navidad lyrics"},
            {"title": "Let It Snow! Let It Snow! Let It Snow!", "artist": "Dean Martin", "query": "Dean Martin Let It Snow lyrics"},
            {"title": "Santa Tell Me", "artist": "Ariana Grande", "query": "Ariana Grande Santa Tell Me lyrics"},
            {"title": "Rockin' Around the Christmas Tree", "artist": "Brenda Lee", "query": "Brenda Lee Rockin Around the Christmas Tree lyrics"},
            {"title": "It's Beginning to Look a Lot Like Christmas", "artist": "Michael Bublé", "query": "Michael Buble Its Beginning to Look a Lot Like Christmas lyrics"}
        ]
    },
    "soiree": {
        "id": "soiree",
        "name": "Soirée & Fête",
        "icon": "fa-champagne-glasses",
        "color": "#a855f7",
        "badge": "🎉 Soirée & Fête",
        "keywords": ["soiree", "soirée", "fete", "fête", "party", "club", "dance", "boite", "dj"],
        "description": "Les hits ultimes pour danser et mettre le feu en soirée",
        "tracks": [
            {"title": "One More Time", "artist": "Daft Punk", "query": "Daft Punk One More Time lyrics"},
            {"title": "Don't Start Now", "artist": "Dua Lipa", "query": "Dua Lipa Don't Start Now lyrics"},
            {"title": "Titanium", "artist": "David Guetta ft. Sia", "query": "David Guetta Titanium lyrics"},
            {"title": "I Gotta Feeling", "artist": "The Black Eyed Peas", "query": "Black Eyed Peas I Gotta Feeling lyrics"},
            {"title": "Alors on danse", "artist": "Stromae", "query": "Stromae Alors on danse lyrics"},
            {"title": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "query": "Justin Timberlake Can't Stop the Feeling lyrics"},
            {"title": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "query": "Mark Ronson Uptown Funk lyrics"},
            {"title": "Wake Me Up", "artist": "Avicii", "query": "Avicii Wake Me Up lyrics"}
        ]
    },
    "sport": {
        "id": "sport",
        "name": "Sport & Motivation",
        "icon": "fa-dumbbell",
        "color": "#eab308",
        "badge": "🏋️ Sport & Motivation",
        "keywords": ["sport", "fitness", "workout", "gym", "motivation", "musculation", "training", "running"],
        "description": "L'énergie maximale pour booster vos entraînements et running",
        "tracks": [
            {"title": "Eye of the Tiger", "artist": "Survivor", "query": "Survivor Eye of the Tiger lyrics"},
            {"title": "Lose Yourself", "artist": "Eminem", "query": "Eminem Lose Yourself lyrics"},
            {"title": "Stronger", "artist": "Kanye West", "query": "Kanye West Stronger lyrics"},
            {"title": "Till I Collapse", "artist": "Eminem", "query": "Eminem Till I Collapse lyrics"},
            {"title": "Can't Hold Us", "artist": "Macklemore & Ryan Lewis", "query": "Macklemore Can't Hold Us lyrics"},
            {"title": "Remember the Name", "artist": "Fort Minor", "query": "Fort Minor Remember the Name lyrics"},
            {"title": "Believer", "artist": "Imagine Dragons", "query": "Imagine Dragons Believer lyrics"},
            {"title": "Hall of Fame", "artist": "The Script ft. will.i.am", "query": "The Script Hall of Fame lyrics"}
        ]
    },
    "chill": {
        "id": "chill",
        "name": "Détente & Chill",
        "icon": "fa-mug-hot",
        "color": "#06b6d4",
        "badge": "🧘 Détente & Relaxation",
        "keywords": ["chill", "detente", "détente", "calme", "relax", "relaxation", "lofi", "sommeil", "sleep", "zen"],
        "description": "Musiques douces, Lofi et piano pour se relaxer ou étudier",
        "tracks": [
            {"title": "Sunset Lover", "artist": "Petit Biscuit", "query": "Petit Biscuit Sunset Lover audio"},
            {"title": "River Flows in You", "artist": "Yiruma", "query": "Yiruma River Flows in You piano"},
            {"title": "Clair de Lune", "artist": "Claude Debussy", "query": "Claude Debussy Clair de Lune piano"},
            {"title": "Get You The Moon", "artist": "Kina ft. Snøw", "query": "Kina Get You The Moon lyrics"},
            {"title": "Weightless", "artist": "Marconi Union", "query": "Marconi Union Weightless audio"},
            {"title": "Death Bed (Coffee for Your Head)", "artist": "Powfu ft. beabadoobee", "query": "Powfu Death Bed lyrics"},
            {"title": "Experience", "artist": "Ludovico Einaudi", "query": "Ludovico Einaudi Experience audio"}
        ]
    },
    "gaming": {
        "id": "gaming",
        "name": "Gaming & Électro",
        "icon": "fa-gamepad",
        "color": "#6366f1",
        "badge": "🎮 Gaming & Électro",
        "keywords": ["gaming", "game", "electro", "ncs", "synthwave", "jeux", "jeuxvideo"],
        "description": "Les sons préférés des gamers et passionnés d'électro / bass",
        "tracks": [
            {"title": "Faded", "artist": "Alan Walker", "query": "Alan Walker Faded lyrics"},
            {"title": "Monody", "artist": "TheFatRat", "query": "TheFatRat Monody lyrics"},
            {"title": "The Spectre", "artist": "Alan Walker", "query": "Alan Walker The Spectre lyrics"},
            {"title": "Unity", "artist": "TheFatRat", "query": "TheFatRat Unity lyrics"},
            {"title": "Alone", "artist": "Marshmello", "query": "Marshmello Alone lyrics"},
            {"title": "Heroes Tonight", "artist": "Janji ft. Johnning", "query": "Janji Heroes Tonight NCS lyrics"},
            {"title": "Spectre", "artist": "Alan Walker", "query": "Alan Walker Spectre NCS audio"}
        ]
    },
    "retro80": {
        "id": "retro80",
        "name": "Années 80 & 90 Rétro",
        "icon": "fa-compact-disc",
        "color": "#ec4899",
        "badge": "📻 Années 80/90 Rétro",
        "keywords": ["80", "90", "retro", "rétro", "vintage", "disco", "nostalgie", "annees 80", "années 80"],
        "description": "Les plus grands classiques cultes des années 80 et 90",
        "tracks": [
            {"title": "Take On Me", "artist": "A-ha", "query": "A-ha Take On Me lyrics"},
            {"title": "Billie Jean", "artist": "Michael Jackson", "query": "Michael Jackson Billie Jean lyrics"},
            {"title": "Sweet Child O' Mine", "artist": "Guns N' Roses", "query": "Guns N Roses Sweet Child O Mine lyrics"},
            {"title": "Girls Just Want to Have Fun", "artist": "Cyndi Lauper", "query": "Cyndi Lauper Girls Just Want to Have Fun lyrics"},
            {"title": "Never Gonna Give You Up", "artist": "Rick Astley", "query": "Rick Astley Never Gonna Give You Up lyrics"},
            {"title": "L'Aventurier", "artist": "Indochine", "query": "Indochine L Aventurier paroles"},
            {"title": "Les Démons de minuit", "artist": "Images", "query": "Images Les Demons de minuit paroles"},
            {"title": "Nuit de folie", "artist": "Début de Soirée", "query": "Debut de Soiree Nuit de folie paroles"}
        ]
    },
    "latino": {
        "id": "latino",
        "name": "Latino & Soleil",
        "icon": "fa-sun",
        "color": "#f59e0b",
        "badge": "🏖️ Latino & Soleil",
        "keywords": ["latino", "soleil", "ete", "été", "reggaeton", "plage", "vacances"],
        "description": "Rythmes ensoleillés, reggaeton et hits de l'été",
        "tracks": [
            {"title": "Despacito", "artist": "Luis Fonsi ft. Daddy Yankee", "query": "Luis Fonsi Despacito lyrics"},
            {"title": "Danza Kuduro", "artist": "Don Omar ft. Lucenzo", "query": "Don Omar Danza Kuduro lyrics"},
            {"title": "Bailando", "artist": "Enrique Iglesias", "query": "Enrique Iglesias Bailando lyrics"},
            {"title": "Mi Gente", "artist": "J Balvin, Willy William", "query": "J Balvin Mi Gente lyrics"},
            {"title": "Pepas", "artist": "Farruko", "query": "Farruko Pepas lyrics"},
            {"title": "Calma", "artist": "Pedro Capó, Farruko", "query": "Pedro Capo Calma remix lyrics"}
        ]
    },
    "rap": {
        "id": "rap",
        "name": "Rap & Hip-Hop",
        "icon": "fa-microphone",
        "color": "#ef4444",
        "badge": "🎤 Rap & Hip-Hop",
        "keywords": ["rap", "hiphop", "hip-hop", "trap", "freestyle", "drill", "urbain"],
        "description": "Les plus gros bangers Rap Français et International",
        "tracks": [
            {"title": "Bande Organisée", "artist": "13 Organisé", "query": "13 Organise Bande Organisee paroles"},
            {"title": "Lettre à une femme", "artist": "Ninho", "query": "Ninho Lettre a une femme paroles"},
            {"title": "J'oublie tout", "artist": "Jul", "query": "Jul Joublie tout paroles"},
            {"title": "DKR", "artist": "Booba", "query": "Booba DKR paroles"},
            {"title": "Godzilla", "artist": "Eminem ft. Juice WRLD", "query": "Eminem Godzilla lyrics"},
            {"title": "SICKO MODE", "artist": "Travis Scott", "query": "Travis Scott SICKO MODE lyrics"},
            {"title": "In My Feelings", "artist": "Drake", "query": "Drake In My Feelings lyrics"}
        ]
    },
    "pop": {
        "id": "pop",
        "name": "Pop & Hits du Moment",
        "icon": "fa-star",
        "color": "#3b82f6",
        "badge": "🌟 Pop & Hits du Moment",
        "keywords": ["pop", "hits", "top", "chart", "tendance", "radio", "star"],
        "description": "Les titres incontournables et hits populaires mondiaux",
        "tracks": [
            {"title": "Blinding Lights", "artist": "The Weeknd", "query": "The Weeknd Blinding Lights lyrics"},
            {"title": "Levitating", "artist": "Dua Lipa", "query": "Dua Lipa Levitating lyrics"},
            {"title": "As It Was", "artist": "Harry Styles", "query": "Harry Styles As It Was lyrics"},
            {"title": "Flowers", "artist": "Miley Cyrus", "query": "Miley Cyrus Flowers lyrics"},
            {"title": "Bad Guy", "artist": "Billie Eilish", "query": "Billie Eilish Bad Guy lyrics"},
            {"title": "Shape of You", "artist": "Ed Sheeran", "query": "Ed Sheeran Shape of You lyrics"},
            {"title": "Cruel Summer", "artist": "Taylor Swift", "query": "Taylor Swift Cruel Summer lyrics"}
        ]
    },
    "variete_fr": {
        "id": "variete_fr",
        "name": "Variété Française Cult",
        "icon": "fa-guitar",
        "color": "#8b5cf6",
        "badge": "🇫🇷 Variété & Classiques Français",
        "keywords": ["francais", "français", "variete", "variété", "classique", "chanson", "france"],
        "description": "Les plus grands chefs-d'œuvre de la chanson française",
        "tracks": [
            {"title": "Allumez le feu", "artist": "Johnny Hallyday", "query": "Johnny Hallyday Allumez le feu paroles"},
            {"title": "Mistral Gagnant", "artist": "Renaud", "query": "Renaud Mistral Gagnant paroles"},
            {"title": "Envole-moi", "artist": "Jean-Jacques Goldman", "query": "Jean-Jacques Goldman Envole-moi paroles"},
            {"title": "La Bohème", "artist": "Charles Aznavour", "query": "Charles Aznavour La Boheme paroles"},
            {"title": "Santiano", "artist": "Hugues Aufray", "query": "Hugues Aufray Santiano paroles"},
            {"title": "Champs-Élysées", "artist": "Joe Dassin", "query": "Joe Dassin Champs Elysees paroles"},
            {"title": "Bella Ciao", "artist": "Naestro, Gims, Vitaa, Dadju, Slimane", "query": "Bella Ciao Gims Vitaa Dadju paroles"}
        ]
    }
}

def get_all_themes():
    """Renvoie la liste des thèmes disponibles avec métadonnées."""
    result = []
    for tid, info in THEMES_CATALOG.items():
        result.append({
            "id": tid,
            "name": info["name"],
            "icon": info["icon"],
            "color": info.get("color", "#6366f1"),
            "badge": info["badge"],
            "description": info["description"],
            "tracks": info.get("tracks", []),
            "track_count": len(info.get("tracks", []))
        })
    return result

def match_theme_by_query(query: str):
    """
    Vérifie si une recherche textuelle correspond à un thème particulier.
    Ex: si l'utilisateur cherche 'halloween', 'allowen', 'musique noel', etc.
    """
    if not query:
        return None
    q_lower = query.lower().strip()
    words = q_lower.split()
    
    for tid, info in THEMES_CATALOG.items():
        for kw in info["keywords"]:
            if kw in q_lower or any(kw in w for w in words):
                return info
    return None

def get_theme_by_id(theme_id: str):
    """Renvoie le thème par son identifiant."""
    return THEMES_CATALOG.get(theme_id)
