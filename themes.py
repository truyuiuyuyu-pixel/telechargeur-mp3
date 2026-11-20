# -*- coding: utf-8 -*-
"""
themes.py — Catalogue complet des styles et thèmes musicaux.
Contient plus de 25 thèmes riches avec des dizaines de morceaux cultes
et le moteur de recherche par thème.
"""

THEMES_CATALOG = {
    "amour": {
        "id": "amour",
        "name": "Amour & Romantique",
        "icon": "fa-heart",
        "color": "#f43f5e",
        "badge": "❤️ Amour & Romantique",
        "keywords": ["amour", "ammour", "love", "romantique", "romance", "mariage", "declaration", "saint-valentin", "couple", "coeur"],
        "description": "Les plus belles chansons d'amour, slows et déclarations romantiques intemporelles",
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
            {"title": "La vie en rose", "artist": "Édith Piaf", "query": "Edith Piaf La vie en rose paroles"},
            {"title": "Just the Way You Are", "artist": "Bruno Mars", "query": "Bruno Mars Just the Way You Are lyrics"},
            {"title": "My Heart Will Go On", "artist": "Céline Dion", "query": "Celine Dion My Heart Will Go On lyrics"},
            {"title": "Unchained Melody", "artist": "The Righteous Brothers", "query": "The Righteous Brothers Unchained Melody lyrics"},
            {"title": "Thinking Out Loud", "artist": "Ed Sheeran", "query": "Ed Sheeran Thinking Out Loud lyrics"},
            {"title": "Quelqu'un m'a dit", "artist": "Carla Bruni", "query": "Carla Bruni Quelquun ma dit paroles"},
            {"title": "Stand by Me", "artist": "Ben E. King", "query": "Ben E King Stand by Me lyrics"},
            {"title": "Can't Help Falling in Love", "artist": "Elvis Presley", "query": "Elvis Presley Cant Help Falling in Love lyrics"},
            {"title": "Mistral Gagnant", "artist": "Renaud", "query": "Renaud Mistral Gagnant paroles"}
        ]
    },
    "halloween": {
        "id": "halloween",
        "name": "Halloween & Horreur",
        "icon": "fa-ghost",
        "color": "#f97316",
        "badge": "🎃 Halloween & Horreur",
        "keywords": ["halloween", "allowen", "haloween", "hallowen", "horreur", "spooky", "peur", "citrouille", "fantome", "vampire", "zombie"],
        "description": "Les plus grands morceaux cultes, mystérieux et effrayants pour Halloween",
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
            {"title": "Disturbia", "artist": "Rihanna", "query": "Rihanna Disturbia lyrics"},
            {"title": "Tubular Bells (The Exorcist Theme)", "artist": "Mike Oldfield", "query": "Mike Oldfield Tubular Bells Exorcist theme"},
            {"title": "Psycho (Main Theme)", "artist": "Bernard Herrmann", "query": "Bernard Herrmann Psycho shower scene theme"},
            {"title": "Superstition", "artist": "Stevie Wonder", "query": "Stevie Wonder Superstition lyrics"}
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
            {"title": "It's Beginning to Look a Lot Like Christmas", "artist": "Michael Bublé", "query": "Michael Buble Its Beginning to Look a Lot Like Christmas lyrics"},
            {"title": "Underneath the Tree", "artist": "Kelly Clarkson", "query": "Kelly Clarkson Underneath the Tree lyrics"},
            {"title": "Douce Nuit, Sainte Nuit", "artist": "Chants de Noël", "query": "Douce Nuit Sainte Nuit chorale"}
        ]
    },
    "soiree": {
        "id": "soiree",
        "name": "Soirée, Fête & Club",
        "icon": "fa-champagne-glasses",
        "color": "#a855f7",
        "badge": "🎉 Soirée & Fête",
        "keywords": ["soiree", "soirée", "fete", "fête", "party", "club", "dance", "boite", "dj"],
        "description": "Les hits ultimes pour danser et mettre l'ambiance en soirée",
        "tracks": [
            {"title": "One More Time", "artist": "Daft Punk", "query": "Daft Punk One More Time lyrics"},
            {"title": "Don't Start Now", "artist": "Dua Lipa", "query": "Dua Lipa Don't Start Now lyrics"},
            {"title": "Titanium", "artist": "David Guetta ft. Sia", "query": "David Guetta Titanium lyrics"},
            {"title": "I Gotta Feeling", "artist": "The Black Eyed Peas", "query": "Black Eyed Peas I Gotta Feeling lyrics"},
            {"title": "Alors on danse", "artist": "Stromae", "query": "Stromae Alors on danse lyrics"},
            {"title": "Can't Stop the Feeling!", "artist": "Justin Timberlake", "query": "Justin Timberlake Can't Stop the Feeling lyrics"},
            {"title": "Uptown Funk", "artist": "Mark Ronson ft. Bruno Mars", "query": "Mark Ronson Uptown Funk lyrics"},
            {"title": "Wake Me Up", "artist": "Avicii", "query": "Avicii Wake Me Up lyrics"},
            {"title": "Pepas", "artist": "Farruko", "query": "Farruko Pepas lyrics"},
            {"title": "Get Lucky", "artist": "Daft Punk ft. Pharrell Williams", "query": "Daft Punk Get Lucky lyrics"},
            {"title": "Danza Kuduro", "artist": "Don Omar ft. Lucenzo", "query": "Don Omar Danza Kuduro lyrics"},
            {"title": "Levels", "artist": "Avicii", "query": "Avicii Levels original mix audio"}
        ]
    },
    "sport": {
        "id": "sport",
        "name": "Sport & Motivation",
        "icon": "fa-dumbbell",
        "color": "#eab308",
        "badge": "🏋️ Sport & Motivation",
        "keywords": ["sport", "fitness", "workout", "gym", "motivation", "musculation", "training", "running"],
        "description": "L'énergie maximale pour booster vos séances de sport, musculation et running",
        "tracks": [
            {"title": "Eye of the Tiger", "artist": "Survivor", "query": "Survivor Eye of the Tiger lyrics"},
            {"title": "Lose Yourself", "artist": "Eminem", "query": "Eminem Lose Yourself lyrics"},
            {"title": "Stronger", "artist": "Kanye West", "query": "Kanye West Stronger lyrics"},
            {"title": "Till I Collapse", "artist": "Eminem", "query": "Eminem Till I Collapse lyrics"},
            {"title": "Can't Hold Us", "artist": "Macklemore & Ryan Lewis", "query": "Macklemore Can't Hold Us lyrics"},
            {"title": "Remember the Name", "artist": "Fort Minor", "query": "Fort Minor Remember the Name lyrics"},
            {"title": "Believer", "artist": "Imagine Dragons", "query": "Imagine Dragons Believer lyrics"},
            {"title": "Hall of Fame", "artist": "The Script ft. will.i.am", "query": "The Script Hall of Fame lyrics"},
            {"title": "Gonna Fly Now (Rocky Theme)", "artist": "Bill Conti", "query": "Bill Conti Gonna Fly Now Rocky Theme"},
            {"title": "Centuries", "artist": "Fall Out Boy", "query": "Fall Out Boy Centuries lyrics"},
            {"title": "Power", "artist": "Kanye West", "query": "Kanye West Power lyrics"},
            {"title": "Warriors", "artist": "Imagine Dragons", "query": "Imagine Dragons Warriors lyrics"}
        ]
    },
    "chill": {
        "id": "chill",
        "name": "Détente, Chill & Lofi",
        "icon": "fa-mug-hot",
        "color": "#06b6d4",
        "badge": "🧘 Détente & Relaxation",
        "keywords": ["chill", "detente", "détente", "calme", "relax", "relaxation", "lofi", "sommeil", "zen", "repos"],
        "description": "Musiques douces, Lofi beats et piano apaisant pour se relaxer",
        "tracks": [
            {"title": "Sunset Lover", "artist": "Petit Biscuit", "query": "Petit Biscuit Sunset Lover audio"},
            {"title": "River Flows in You", "artist": "Yiruma", "query": "Yiruma River Flows in You piano"},
            {"title": "Clair de Lune", "artist": "Claude Debussy", "query": "Claude Debussy Clair de Lune piano"},
            {"title": "Get You The Moon", "artist": "Kina ft. Snøw", "query": "Kina Get You The Moon lyrics"},
            {"title": "Weightless", "artist": "Marconi Union", "query": "Marconi Union Weightless audio"},
            {"title": "Death Bed (Coffee for Your Head)", "artist": "Powfu ft. beabadoobee", "query": "Powfu Death Bed lyrics"},
            {"title": "Experience", "artist": "Ludovico Einaudi", "query": "Ludovico Einaudi Experience audio"},
            {"title": "Nuvole Bianche", "artist": "Ludovico Einaudi", "query": "Ludovico Einaudi Nuvole Bianche audio"},
            {"title": "Gymnopédie No. 1", "artist": "Erik Satie", "query": "Erik Satie Gymnopedie No 1 piano"},
            {"title": "Comptine d'un autre été", "artist": "Yann Tiersen", "query": "Yann Tiersen Comptine dun autre ete audio"}
        ]
    },
    "gaming": {
        "id": "gaming",
        "name": "Gaming & Bass Électro",
        "icon": "fa-gamepad",
        "color": "#6366f1",
        "badge": "🎮 Gaming & Électro",
        "keywords": ["gaming", "game", "electro", "ncs", "synthwave", "jeux", "jeuxvideo", "streamer"],
        "description": "Les sons préférés des gamers et streamers (NCS, Bass, Électro)",
        "tracks": [
            {"title": "Faded", "artist": "Alan Walker", "query": "Alan Walker Faded lyrics"},
            {"title": "Monody", "artist": "TheFatRat", "query": "TheFatRat Monody lyrics"},
            {"title": "The Spectre", "artist": "Alan Walker", "query": "Alan Walker The Spectre lyrics"},
            {"title": "Unity", "artist": "TheFatRat", "query": "TheFatRat Unity lyrics"},
            {"title": "Alone", "artist": "Marshmello", "query": "Marshmello Alone lyrics"},
            {"title": "Heroes Tonight", "artist": "Janji ft. Johnning", "query": "Janji Heroes Tonight NCS lyrics"},
            {"title": "Spectre", "artist": "Alan Walker", "query": "Alan Walker Spectre NCS audio"},
            {"title": "Fly Away", "artist": "TheFatRat", "query": "TheFatRat Fly Away lyrics"},
            {"title": "Invincible", "artist": "Deaf Kev", "query": "Deaf Kev Invincible NCS audio"},
            {"title": "Mortals", "artist": "Warriyo ft. Laura Brehm", "query": "Warriyo Mortals NCS audio"}
        ]
    },
    "retro80": {
        "id": "retro80",
        "name": "Années 80 Cultes",
        "icon": "fa-compact-disc",
        "color": "#ec4899",
        "badge": "📻 Années 80 Cultes",
        "keywords": ["80", "annees 80", "années 80", "eighties", "vintage 80", "retro 80"],
        "description": "Les plus grands hits inoubliables des années 1980",
        "tracks": [
            {"title": "Take On Me", "artist": "A-ha", "query": "A-ha Take On Me lyrics"},
            {"title": "Billie Jean", "artist": "Michael Jackson", "query": "Michael Jackson Billie Jean lyrics"},
            {"title": "Sweet Child O' Mine", "artist": "Guns N' Roses", "query": "Guns N Roses Sweet Child O Mine lyrics"},
            {"title": "Girls Just Want to Have Fun", "artist": "Cyndi Lauper", "query": "Cyndi Lauper Girls Just Want to Have Fun lyrics"},
            {"title": "Never Gonna Give You Up", "artist": "Rick Astley", "query": "Rick Astley Never Gonna Give You Up lyrics"},
            {"title": "L'Aventurier", "artist": "Indochine", "query": "Indochine L Aventurier paroles"},
            {"title": "Les Démons de minuit", "artist": "Images", "query": "Images Les Demons de minuit paroles"},
            {"title": "Nuit de folie", "artist": "Début de Soirée", "query": "Debut de Soiree Nuit de folie paroles"},
            {"title": "Wake Me Up Before You Go-Go", "artist": "Wham!", "query": "Wham Wake Me Up Before You Go Go lyrics"},
            {"title": "Africa", "artist": "Toto", "query": "Toto Africa lyrics"},
            {"title": "Blue Monday", "artist": "New Order", "query": "New Order Blue Monday lyrics"},
            {"title": "Voyage Voyage", "artist": "Desireless", "query": "Desireless Voyage Voyage paroles"}
        ]
    },
    "retro90": {
        "id": "retro90",
        "name": "Années 90 & Eurodance",
        "icon": "fa-tape",
        "color": "#0ea5e9",
        "badge": "📼 Années 90 & Eurodance",
        "keywords": ["90", "annees 90", "années 90", "nineties", "eurodance", "boyband"],
        "description": "La folie des années 90, Eurodance, Grunge et tubes pop",
        "tracks": [
            {"title": "Smells Like Teen Spirit", "artist": "Nirvana", "query": "Nirvana Smells Like Teen Spirit lyrics"},
            {"title": "Wannabe", "artist": "Spice Girls", "query": "Spice Girls Wannabe lyrics"},
            {"title": "Rhythm Is a Dancer", "artist": "Snap!", "query": "Snap Rhythm Is a Dancer lyrics"},
            {"title": "What Is Love", "artist": "Haddaway", "query": "Haddaway What Is Love lyrics"},
            {"title": "Barbie Girl", "artist": "Aqua", "query": "Aqua Barbie Girl lyrics"},
            {"title": "Wonderwall", "artist": "Oasis", "query": "Oasis Wonderwall lyrics"},
            {"title": "No Limit", "artist": "2 Unlimited", "query": "2 Unlimited No Limit lyrics"},
            {"title": "Scatman (Ski-Ba-Bop-Ba-Dop-Bop)", "artist": "Scatman John", "query": "Scatman John Scatman lyrics"},
            {"title": "Zombie", "artist": "The Cranberries", "query": "The Cranberries Zombie lyrics"},
            {"title": "Macarena", "artist": "Los Del Rio", "query": "Los Del Rio Macarena lyrics"}
        ]
    },
    "annees2000": {
        "id": "annees2000",
        "name": "Années 2000 (R&B & Pop)",
        "icon": "fa-mobile-retro",
        "color": "#f43f5e",
        "badge": "💿 Années 2000 Nostalgie",
        "keywords": ["2000", "annees 2000", "années 2000", "nostalgie 2000", "rnb 2000"],
        "description": "Les plus grands hits du début des années 2000, R&B et tubes cultes",
        "tracks": [
            {"title": "Yeah!", "artist": "Usher ft. Lil Jon, Ludacris", "query": "Usher Yeah lyrics"},
            {"title": "Crazy in Love", "artist": "Beyoncé ft. Jay-Z", "query": "Beyonce Crazy in Love lyrics"},
            {"title": "In da Club", "artist": "50 Cent", "query": "50 Cent In da Club lyrics"},
            {"title": "Hips Don't Lie", "artist": "Shakira ft. Wyclef Jean", "query": "Shakira Hips Dont Lie lyrics"},
            {"title": "Toxic", "artist": "Britney Spears", "query": "Britney Spears Toxic lyrics"},
            {"title": "Femme Like U", "artist": "K.Maro", "query": "K Maro Femme Like U paroles"},
            {"title": "Umbrella", "artist": "Rihanna ft. Jay-Z", "query": "Rihanna Umbrella lyrics"},
            {"title": "Hey Ya!", "artist": "Outkast", "query": "Outkast Hey Ya lyrics"},
            {"title": "Désenchantée", "artist": "Kate Ryan", "query": "Kate Ryan Desenchantee lyrics"}
        ]
    },
    "disco70": {
        "id": "disco70",
        "name": "Années 70 & Disco Funk",
        "icon": "fa-record-vinyl",
        "color": "#e11d48",
        "badge": "🕺 Années 70 & Disco",
        "keywords": ["70", "annees 70", "années 70", "disco", "funk", "seventies"],
        "description": "Boules à facettes, disco étincelant et funk légendaire des 70's",
        "tracks": [
            {"title": "Stayin' Alive", "artist": "Bee Gees", "query": "Bee Gees Stayin Alive lyrics"},
            {"title": "Dancing Queen", "artist": "ABBA", "query": "ABBA Dancing Queen lyrics"},
            {"title": "September", "artist": "Earth, Wind & Fire", "query": "Earth Wind and Fire September lyrics"},
            {"title": "Rasputin", "artist": "Boney M.", "query": "Boney M Rasputin lyrics"},
            {"title": "Le Freak", "artist": "Chic", "query": "Chic Le Freak lyrics"},
            {"title": "Gimme! Gimme! Gimme!", "artist": "ABBA", "query": "ABBA Gimme Gimme Gimme lyrics"},
            {"title": "I Will Survive", "artist": "Gloria Gaynor", "query": "Gloria Gaynor I Will Survive lyrics"},
            {"title": "Daddy Cool", "artist": "Boney M.", "query": "Boney M Daddy Cool lyrics"}
        ]
    },
    "latino": {
        "id": "latino",
        "name": "Latino & Reggaeton",
        "icon": "fa-sun",
        "color": "#f59e0b",
        "badge": "🏖️ Latino & Reggaeton",
        "keywords": ["latino", "soleil", "ete", "été", "reggaeton", "plage", "vacances", "salsa"],
        "description": "Rythmes ensoleillés, reggaeton caliente et hits d'été",
        "tracks": [
            {"title": "Despacito", "artist": "Luis Fonsi ft. Daddy Yankee", "query": "Luis Fonsi Despacito lyrics"},
            {"title": "Danza Kuduro", "artist": "Don Omar ft. Lucenzo", "query": "Don Omar Danza Kuduro lyrics"},
            {"title": "Bailando", "artist": "Enrique Iglesias", "query": "Enrique Iglesias Bailando lyrics"},
            {"title": "Mi Gente", "artist": "J Balvin, Willy William", "query": "J Balvin Mi Gente lyrics"},
            {"title": "Pepas", "artist": "Farruko", "query": "Farruko Pepas lyrics"},
            {"title": "Calma", "artist": "Pedro Capó, Farruko", "query": "Pedro Capo Calma remix lyrics"},
            {"title": "Gasolina", "artist": "Daddy Yankee", "query": "Daddy Yankee Gasolina lyrics"},
            {"title": "Hawái", "artist": "Maluma", "query": "Maluma Hawai lyrics"},
            {"title": "Tusa", "artist": "KAROL G, Nicki Minaj", "query": "KAROL G Tusa lyrics"}
        ]
    },
    "rap_fr": {
        "id": "rap_fr",
        "name": "Rap Français",
        "icon": "fa-microphone-lines",
        "color": "#ef4444",
        "badge": "🇫🇷 Rap Français",
        "keywords": ["rap", "rap fr", "rap francais", "rap français", "banger", "jul", "ninho", "gims", "booba", "sch"],
        "description": "Les plus gros hits du rap et de la musique urbaine francophone",
        "tracks": [
            {"title": "Bande Organisée", "artist": "13 Organisé", "query": "13 Organise Bande Organisee paroles"},
            {"title": "Lettre à une femme", "artist": "Ninho", "query": "Ninho Lettre a une femme paroles"},
            {"title": "J'oublie tout", "artist": "Jul", "query": "Jul Joublie tout paroles"},
            {"title": "DKR", "artist": "Booba", "query": "Booba DKR paroles"},
            {"title": "Fade Up", "artist": "Zeg P ft. Hamza, SCH", "query": "Zeg P Fade Up paroles"},
            {"title": "Tout donner", "artist": "Gims", "query": "Maitre Gims Tout donner paroles"},
            {"title": "Sapés comme jamais", "artist": "Gims ft. Niska", "query": "Maitre Gims Sapes comme jamais paroles"},
            {"title": "Petrouchka", "artist": "Soso Maness ft. PLK", "query": "Soso Maness Petrouchka paroles"},
            {"title": "Mona Lisa", "artist": "Booba ft. JSX", "query": "Booba Mona Lisa paroles"},
            {"title": "Autobahn", "artist": "SCH", "query": "SCH Autobahn paroles"}
        ]
    },
    "rap_us": {
        "id": "rap_us",
        "name": "Rap US & Hip-Hop",
        "icon": "fa-microphone",
        "color": "#b91c1c",
        "badge": "🇺🇸 Rap US & Hip-Hop",
        "keywords": ["rap us", "hiphop", "hip-hop", "drill", "trap", "drake", "eminem", "travis"],
        "description": "Les maîtres incontestés du rap américain et de la trap US",
        "tracks": [
            {"title": "Godzilla", "artist": "Eminem ft. Juice WRLD", "query": "Eminem Godzilla lyrics"},
            {"title": "SICKO MODE", "artist": "Travis Scott", "query": "Travis Scott SICKO MODE lyrics"},
            {"title": "In My Feelings", "artist": "Drake", "query": "Drake In My Feelings lyrics"},
            {"title": "HUMBLE.", "artist": "Kendrick Lamar", "query": "Kendrick Lamar HUMBLE lyrics"},
            {"title": "Rockstar", "artist": "Post Malone ft. 21 Savage", "query": "Post Malone Rockstar lyrics"},
            {"title": "Lucid Dreams", "artist": "Juice WRLD", "query": "Juice WRLD Lucid Dreams lyrics"},
            {"title": "Old Town Road", "artist": "Lil Nas X", "query": "Lil Nas X Old Town Road lyrics"},
            {"title": "All The Stars", "artist": "Kendrick Lamar, SZA", "query": "Kendrick Lamar SZA All The Stars lyrics"}
        ]
    },
    "pop": {
        "id": "pop",
        "name": "Pop Internationale",
        "icon": "fa-star",
        "color": "#3b82f6",
        "badge": "🌟 Pop Internationale",
        "keywords": ["pop", "hits", "top", "chart", "tendance", "radio", "star"],
        "description": "Les plus grands hits pop mondiaux écoutés par des millions de personnes",
        "tracks": [
            {"title": "Blinding Lights", "artist": "The Weeknd", "query": "The Weeknd Blinding Lights lyrics"},
            {"title": "Levitating", "artist": "Dua Lipa", "query": "Dua Lipa Levitating lyrics"},
            {"title": "As It Was", "artist": "Harry Styles", "query": "Harry Styles As It Was lyrics"},
            {"title": "Flowers", "artist": "Miley Cyrus", "query": "Miley Cyrus Flowers lyrics"},
            {"title": "Bad Guy", "artist": "Billie Eilish", "query": "Billie Eilish Bad Guy lyrics"},
            {"title": "Shape of You", "artist": "Ed Sheeran", "query": "Ed Sheeran Shape of You lyrics"},
            {"title": "Cruel Summer", "artist": "Taylor Swift", "query": "Taylor Swift Cruel Summer lyrics"},
            {"title": "Stay", "artist": "The Kid LAROI, Justin Bieber", "query": "The Kid LAROI Justin Bieber Stay lyrics"},
            {"title": "Espresso", "artist": "Sabrina Carpenter", "query": "Sabrina Carpenter Espresso lyrics"}
        ]
    },
    "variete_fr": {
        "id": "variete_fr",
        "name": "Variété & Classiques Français",
        "icon": "fa-guitar",
        "color": "#8b5cf6",
        "badge": "🇫🇷 Variété Française",
        "keywords": ["francais", "français", "variete", "variété", "classique", "chanson", "france", "goldman", "hallyday"],
        "description": "Les plus beaux monuments et refrains de la chanson française",
        "tracks": [
            {"title": "Allumez le feu", "artist": "Johnny Hallyday", "query": "Johnny Hallyday Allumez le feu paroles"},
            {"title": "Mistral Gagnant", "artist": "Renaud", "query": "Renaud Mistral Gagnant paroles"},
            {"title": "Envole-moi", "artist": "Jean-Jacques Goldman", "query": "Jean-Jacques Goldman Envole-moi paroles"},
            {"title": "La Bohème", "artist": "Charles Aznavour", "query": "Charles Aznavour La Boheme paroles"},
            {"title": "Santiano", "artist": "Hugues Aufray", "query": "Hugues Aufray Santiano paroles"},
            {"title": "Champs-Élysées", "artist": "Joe Dassin", "query": "Joe Dassin Champs Elysees paroles"},
            {"title": "Je te promets", "artist": "Johnny Hallyday", "query": "Johnny Hallyday Je te promets paroles"},
            {"title": "Résiste", "artist": "France Gall", "query": "France Gall Resiste paroles"},
            {"title": "Je vole", "artist": "Michel Sardou", "query": "Michel Sardou Je vole paroles"}
        ]
    },
    "rock_metal": {
        "id": "rock_metal",
        "name": "Rock & Metal Légendes",
        "icon": "fa-bolt",
        "color": "#64748b",
        "badge": "⚡ Rock & Metal",
        "keywords": ["rock", "metal", "hardrock", "guitare", "solo", "queen", "acdc", "metallica"],
        "description": "Riffs de guitare légendaires, hymnes rock et solos mythiques",
        "tracks": [
            {"title": "Bohemian Rhapsody", "artist": "Queen", "query": "Queen Bohemian Rhapsody lyrics"},
            {"title": "Back In Black", "artist": "AC/DC", "query": "AC DC Back In Black lyrics"},
            {"title": "Enter Sandman", "artist": "Metallica", "query": "Metallica Enter Sandman lyrics"},
            {"title": "Smells Like Teen Spirit", "artist": "Nirvana", "query": "Nirvana Smells Like Teen Spirit lyrics"},
            {"title": "Stairway to Heaven", "artist": "Led Zeppelin", "query": "Led Zeppelin Stairway to Heaven audio"},
            {"title": "Numb", "artist": "Linkin Park", "query": "Linkin Park Numb lyrics"},
            {"title": "In the End", "artist": "Linkin Park", "query": "Linkin Park In the End lyrics"},
            {"title": "Dream On", "artist": "Aerosmith", "query": "Aerosmith Dream On lyrics"}
        ]
    },
    "electro_edm": {
        "id": "electro_edm",
        "name": "Électro, EDM & Festival",
        "icon": "fa-headphones",
        "color": "#14b8a6",
        "badge": "🎧 Électro & Festival",
        "keywords": ["electro", "edm", "house", "dj", "techno", "festival", "tomorrowland", "guetta", "avicii"],
        "description": "Les drops surpuissants et hymnes des plus grands festivals électro",
        "tracks": [
            {"title": "Titanium", "artist": "David Guetta ft. Sia", "query": "David Guetta Titanium lyrics"},
            {"title": "Wake Me Up", "artist": "Avicii", "query": "Avicii Wake Me Up lyrics"},
            {"title": "Animals", "artist": "Martin Garrix", "query": "Martin Garrix Animals original mix"},
            {"title": "Summer", "artist": "Calvin Harris", "query": "Calvin Harris Summer lyrics"},
            {"title": "Lean On", "artist": "Major Lazer & DJ Snake", "query": "Major Lazer DJ Snake Lean On lyrics"},
            {"title": "Turn Down for What", "artist": "DJ Snake, Lil Jon", "query": "DJ Snake Turn Down for What lyrics"},
            {"title": "Don't You Worry Child", "artist": "Swedish House Mafia", "query": "Swedish House Mafia Dont You Worry Child lyrics"}
        ]
    },
    "roadtrip": {
        "id": "roadtrip",
        "name": "Voyage & Roadtrip",
        "icon": "fa-car",
        "color": "#0284c7",
        "badge": "🚗 Voyage & Roadtrip",
        "keywords": ["voyage", "roadtrip", "route", "voiture", "vacances", "evasion", "liberte"],
        "description": "Les morceaux parfaits pour rouler les fenêtres ouvertes vers l'aventure",
        "tracks": [
            {"title": "Take Me Home, Country Roads", "artist": "John Denver", "query": "John Denver Take Me Home Country Roads lyrics"},
            {"title": "Riptide", "artist": "Vance Joy", "query": "Vance Joy Riptide lyrics"},
            {"title": "Send Me on My Way", "artist": "Rusted Root", "query": "Rusted Root Send Me on My Way lyrics"},
            {"title": "Fast Car", "artist": "Tracy Chapman", "query": "Tracy Chapman Fast Car lyrics"},
            {"title": "Budapest", "artist": "George Ezra", "query": "George Ezra Budapest lyrics"},
            {"title": "Shotgun", "artist": "George Ezra", "query": "George Ezra Shotgun lyrics"},
            {"title": "I'm Gonna Be (500 Miles)", "artist": "The Proclaimers", "query": "The Proclaimers 500 Miles lyrics"}
        ]
    },
    "etude_focus": {
        "id": "etude_focus",
        "name": "Étude & Concentration",
        "icon": "fa-brain",
        "color": "#818cf8",
        "badge": "📚 Concentration & Étude",
        "keywords": ["etude", "focus", "concentration", "revision", "travail", "boulot", "calme"],
        "description": "Ambiances calmes, mélodies de piano et ondes propices à la concentration",
        "tracks": [
            {"title": "River Flows in You", "artist": "Yiruma", "query": "Yiruma River Flows in You piano"},
            {"title": "Experience", "artist": "Ludovico Einaudi", "query": "Ludovico Einaudi Experience audio"},
            {"title": "Interstellar Main Theme", "artist": "Hans Zimmer", "query": "Hans Zimmer Interstellar Theme audio"},
            {"title": "Time", "artist": "Hans Zimmer", "query": "Hans Zimmer Time Inception audio"},
            {"title": "Nuvole Bianche", "artist": "Ludovico Einaudi", "query": "Ludovico Einaudi Nuvole Bianche piano"},
            {"title": "Aura", "artist": "Bicep", "query": "Bicep Aura original mix audio"}
        ]
    },
    "disney_enfants": {
        "id": "disney_enfants",
        "name": "Disney & Dessins Animés",
        "icon": "fa-wand-magic-sparkles",
        "color": "#ec4899",
        "badge": "✨ Disney & Dessins Animés",
        "keywords": ["disney", "enfant", "enfants", "dessin anime", "dessins animes", "roi lion", "reine des neiges"],
        "description": "Les chansons magiques Disney et dessins animés préférés de toute la famille",
        "tracks": [
            {"title": "L'Histoire de la vie (Le Roi Lion)", "artist": "Disney", "query": "Histoire de la vie Roi Lion paroles"},
            {"title": "Libérée, Délivrée (La Reine des Neiges)", "artist": "Disney", "query": "Liberee Delivree Reine des neiges paroles"},
            {"title": "Ce rêve bleu (Aladdin)", "artist": "Disney", "query": "Ce reve bleu Aladdin paroles"},
            {"title": "Hakuna Matata", "artist": "Le Roi Lion", "query": "Hakuna Matata Roi Lion paroles"},
            {"title": "Sous l'océan (La Petite Sirène)", "artist": "Disney", "query": "Sous locean La Petite Sirene paroles"},
            {"title": "Il en faut peu pour être heureux", "artist": "Le Livre de la Jungle", "query": "Il en faut peu pour etre heureux paroles"}
        ]
    },
    "afrobeat": {
        "id": "afrobeat",
        "name": "Afrobeat & Amapiano",
        "icon": "fa-drum",
        "color": "#d97706",
        "badge": "🥁 Afrobeat & Amapiano",
        "keywords": ["afrobeat", "afro", "amapiano", "burna", "rema", "nigeria", "afrique"],
        "description": "Les rythmes envoûtants d'Afrique qui font vibrer le monde entier",
        "tracks": [
            {"title": "Calm Down", "artist": "Rema", "query": "Rema Calm Down lyrics"},
            {"title": "Last Last", "artist": "Burna Boy", "query": "Burna Boy Last Last lyrics"},
            {"title": "Love Nwantiti", "artist": "CKay", "query": "CKay Love Nwantiti lyrics"},
            {"title": "Jerusalema", "artist": "Master KG ft. Nomcebo", "query": "Master KG Jerusalema lyrics"},
            {"title": "Water", "artist": "Tyla", "query": "Tyla Water lyrics"},
            {"title": "Rush", "artist": "Ayra Starr", "query": "Ayra Starr Rush lyrics"}
        ]
    },
    "reggae": {
        "id": "reggae",
        "name": "Reggae & Soleil",
        "icon": "fa-peace",
        "color": "#16a34a",
        "badge": "🌴 Reggae & Soleil",
        "keywords": ["reggae", "bob marley", "roots", "peace", "soleil", "jamaica", "ska"],
        "description": "Good vibes, message de paix et sonorités chaleureuses de Jamaïque",
        "tracks": [
            {"title": "Could You Be Loved", "artist": "Bob Marley", "query": "Bob Marley Could You Be Loved lyrics"},
            {"title": "Three Little Birds", "artist": "Bob Marley", "query": "Bob Marley Three Little Birds lyrics"},
            {"title": "One Love / People Get Ready", "artist": "Bob Marley", "query": "Bob Marley One Love lyrics"},
            {"title": "Red Red Wine", "artist": "UB40", "query": "UB40 Red Red Wine lyrics"},
            {"title": "Sweet Fanta Diallo", "artist": "Alpha Blondy", "query": "Alpha Blondy Sweet Fanta Diallo lyrics"},
            {"title": "Plus rien ne m'étonne", "artist": "Tiken Jah Fakoly", "query": "Tiken Jah Fakoly Plus rien ne metonne paroles"}
        ]
    },
    "jazz_lounge": {
        "id": "jazz_lounge",
        "name": "Jazz & Bar Lounge",
        "icon": "fa-saxophone",
        "color": "#78716c",
        "badge": "🎷 Jazz & Bar Lounge",
        "keywords": ["jazz", "lounge", "saxo", "saxophone", "trompette", "bar", "cocktail"],
        "description": "Ambiance feutrée, saxophones suaves et grands classiques du jazz",
        "tracks": [
            {"title": "Fly Me to the Moon", "artist": "Frank Sinatra", "query": "Frank Sinatra Fly Me to the Moon lyrics"},
            {"title": "What a Wonderful World", "artist": "Louis Armstrong", "query": "Louis Armstrong What a Wonderful World lyrics"},
            {"title": "Take Five", "artist": "The Dave Brubeck Quartet", "query": "Dave Brubeck Take Five audio"},
            {"title": "Autumn Leaves", "artist": "Miles Davis", "query": "Miles Davis Autumn Leaves audio"},
            {"title": "Don't Know Why", "artist": "Norah Jones", "query": "Norah Jones Don't Know Why lyrics"},
            {"title": "Feeling Good", "artist": "Nina Simone", "query": "Nina Simone Feeling Good lyrics"}
        ]
    },
    "classique": {
        "id": "classique",
        "name": "Musique Classique & Opéra",
        "icon": "fa-music",
        "color": "#475569",
        "badge": "🎻 Musique Classique",
        "keywords": ["classique", "opera", "opéra", "orchestre", "violon", "piano classique", "mozart", "beethoven"],
        "description": "Les plus grands chefs-d'œuvre symphoniques de l'histoire de la musique",
        "tracks": [
            {"title": "Les Quatre Saisons : Le Printemps", "artist": "Antonio Vivaldi", "query": "Vivaldi Quatre Saisons Printemps audio"},
            {"title": "Symphonie No. 5 en ut mineur", "artist": "Ludwig van Beethoven", "query": "Beethoven Symphonie 5 audio"},
            {"title": "Clair de Lune", "artist": "Claude Debussy", "query": "Debussy Clair de Lune piano audio"},
            {"title": "Nocturne Op. 9 No. 2", "artist": "Frédéric Chopin", "query": "Chopin Nocturne Op 9 No 2 piano audio"},
            {"title": "Le Lac des Cygnes (Scène)", "artist": "Piotr Ilitch Tchaïkovski", "query": "Tchaikovsky Lac des Cygnes scene audio"},
            {"title": "Canon en Ré Majeur", "artist": "Johann Pachelbel", "query": "Pachelbel Canon en re majeur audio"}
        ]
    },
    "sommeil_zen": {
        "id": "sommeil_zen",
        "name": "Sommeil & Méditation Zen",
        "icon": "fa-moon",
        "color": "#312e81",
        "badge": "🌙 Sommeil & Méditation",
        "keywords": ["sommeil", "zen", "meditation", "méditation", "dormir", "bruit blanc", "ondes", "nature"],
        "description": "Sons apaisants, bruits de pluie et ondes douces pour s'endormir sereinement",
        "tracks": [
            {"title": "Weightless (Extended Sleep)", "artist": "Marconi Union", "query": "Marconi Union Weightless audio"},
            {"title": "Deep Sleep Piano", "artist": "Relaxing Piano Music", "query": "Deep Sleep Piano soothing music"},
            {"title": "Rain Sounds for Sleep", "artist": "Nature Soundscapes", "query": "gentle rain sounds for sleeping audio"},
            {"title": "Ocean Waves Calm", "artist": "Meditation Sounds", "query": "ocean waves relaxing calm sound"},
            {"title": "Spiegel im Spiegel", "artist": "Arvo Pärt", "query": "Arvo Part Spiegel im Spiegel audio"}
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
