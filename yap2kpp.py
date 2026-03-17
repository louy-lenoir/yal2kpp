import json
from PIL import Image

def main(template, model, ascent, espace):
    """
    Génère un fragment JSON décrivant une police bitmap à partir d'un template et d'une image modèle.

    Paramètres :
        template (str) : chemin vers le fichier .txt contenant les caractères
        model (str) : chemin vers l'image PNG (avec transparence)
        ascent (int) : valeur d'ascension pour tous les glyphes
        espace (int) : largeur du glyphe d'espace (nombre de points)

    Retourne :
        str : fragment JSON sur une seule ligne
    """
    # Lecture du template
    with open(template, 'r', encoding='utf-8') as f:
        lignes = [ligne.rstrip('\n') for ligne in f]

    # Nom de la police (fixe pour l'exemple)
    nom_police = "font"

    # Début du JSON
    retour = f'{{"{nom_police}":{{"charSpacing":"1",'

    # Glyphe pour l'espace
    points = '.' * espace
    glyph_espace = [points] * 32  # 32 lignes (hauteur fixe)
    glyph_espace_str = json.dumps(glyph_espace)
    retour += f'" ":{{"ascent":"{ascent}","glyph":{glyph_espace_str}}},'

    # Parcours de tous les caractères du template
    for i, ligne in enumerate(lignes):
        for j, car in enumerate(ligne):
            if car == ' ':
                continue
            # Identification du petit carré
            vmin, umin, vmax, umax = IdentificationPetitCarre(j, i, model)
            # Génération du fragment pour ce caractère
            fragment = RedactionJson(car, model, ascent, vmin, umin, vmax, umax)
            retour += fragment

    # Retourner le texte (pas d'accolade fermante)
    return retour


def Coordonnees(template, caractere):
    """
    Recherche la position (j, i) d'un caractère dans un fichier template.
    Le template est un fichier texte où chaque ligne représente une rangée.
    Les coordonnées (j, i) sont respectivement la colonne et la ligne, en partant de (0,0) en haut à gauche.

    Paramètres :
        template (str) : chemin vers le fichier .txt contenant le template
        caractere (str) : caractère unicode à rechercher (un seul caractère)

    Retourne :
        tuple (j, i) si trouvé, sinon lève une exception ValueError.
    """
    with open(template, 'r', encoding='utf-8') as f:
        lignes = f.read().splitlines()  # splitlines conserve les lignes sans les retours chariot

    for i, ligne in enumerate(lignes):
        for j, c in enumerate(ligne):
            if c == caractere:
                return (j, i)
    raise ValueError(f"Le caractère '{caractere}' n'a pas été trouvé dans le template.")



def IdentificationPetitCarre(j, i, model):
    """
    Détermine les bornes horizontales (vmin, vmax) du premier et dernier pixel non transparent
    dans un rectangle de l'image model défini par (j, i). Les bornes verticales sont constantes
    (umin = 1, umax = 32).

    Paramètres :
        j, i (int) : indices du grand rectangle (coin haut-gauche = (j*25+1, i*33+1),
                     coin bas-droit = ((j+1)*25-1, (i+1)*33-1))
        model (str ou PIL.Image) : chemin vers l'image PNG ou objet Image déjà ouvert

    Retourne :
        tuple (vmin, umin, vmax, umax), en coordonnées absolues.
        Si aucun pixel non transparent n'est trouvé, vmin = vmax = 0.
    """
    # Charger l'image et s'assurer qu'elle est en mode RGBA
    if isinstance(model, str):
        img = Image.open(model).convert('RGBA')
    else:
        img = model.convert('RGBA')

    # Coordonnées absolues du rectangle
    x_start = j * 25 + 1
    x_end = (j + 1) * 25 - 1
    y_start = i * 33 + 1
    y_end = (i + 1) * 33 - 1

    vmin = None
    vmax = None

    # Parcourir chaque colonne du rectangle
    for x in range(x_start, x_end + 1):
        for y in range(y_start, y_end + 1):
            r, g, b, a = img.getpixel((x, y))
            if a > 0:  # Pixel non transparent
                if vmin is None:
                    vmin = x
                vmax = x
                break  # On passe à la colonne suivante

    # Gestion du cas où aucun pixel non transparent n'est trouvé
    if vmin is None:
        return (0, y_start, 0, y_end)
    else:
        return (vmin, y_start, vmax, y_end)


def RedactionJson(lettre, model, ascent, vmin, umin, vmax, umax):
    """
    Extrait une région rectangulaire d'une image PNG (model) définie par
    (vmin, umin) à (vmax, umax) et génère une chaîne JSON représentant
    le glyphe de la lettre avec sa hauteur d'ascension.

    Paramètres :
        lettre (str) : caractère associé au glyphe
        model (str) : chemin vers l'image PNG (avec transparence)
        ascent (int) : valeur d'ascension à inclure dans le JSON
        vmin, vmax (int) : bornes horizontales (longueur) inclusives
        umin, umax (int) : bornes verticales (hauteur) inclusives

    Retourne :
        str : fragment JSON au format ' "L":{{"ascent":"A","glyph":[...]}}, '
    """
    # Charger l'image et s'assurer qu'elle est en mode RGBA (avec canal alpha)
    img = Image.open(model).convert('RGBA')
    
    glyph = []
    # Parcourir les lignes de umin à umax incluses
    for y in range(umin, umax + 1):
        ligne = []
        # Parcourir les colonnes de vmin à vmax incluses
        for x in range(vmin, vmax + 1):
            r, g, b, a = img.getpixel((x, y))
            # Si le pixel est non transparent (alpha > 0) -> '#', sinon '.'
            caractere = '#' if a > 0 else '.'
            ligne.append(caractere)
        glyph.append(''.join(ligne))
    
    # Construire le fragment JSON
    # On utilise json.dumps pour obtenir une représentation correcte des chaînes (avec guillemets doubles)
    fragment = f'"{lettre}":{{"ascent":"{ascent}","glyph":{json.dumps(glyph)}}},'
    return fragment
