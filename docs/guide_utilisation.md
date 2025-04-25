# Guide d'utilisation de MistralOCR-Converter

Ce guide vous explique en détail comment utiliser l'application MistralOCR-Converter pour extraire du texte et des images à partir de documents PDF.

## Prérequis

- Python 3.7 ou supérieur
- Une clé API Mistral valide

## Configuration de l'API

Avant d'utiliser l'application, vous devez configurer votre clé API Mistral :

1. Obtenez une clé API depuis la plateforme Mistral AI
2. Dans le fichier `mistral_ocr_solution.py`, remplacez la valeur de `API_KEY` par votre propre clé :

```python
# Clé API Mistral (À remplacer par votre propre clé)
API_KEY = "votre-clé-api-ici"
```

## Interface utilisateur

L'interface utilisateur est divisée en plusieurs parties :

1. **Zone de téléchargement** : Permet de télécharger un fichier PDF
2. **Sélection du modèle** : Choix du modèle OCR à utiliser
3. **Format de sortie** : Choix entre Markdown, HTML ou ZIP
4. **Journal de traitement** : Affiche les étapes du traitement en temps réel
5. **Onglets de résultat** :
   - **Résultat** : Aperçu du markdown généré
   - **Téléchargement** : Lien pour télécharger le fichier généré
   - **À propos** : Informations sur l'application

## Formats de sortie

### Markdown

Le format Markdown intègre les images directement dans le texte en base64, ce qui crée un fichier autonome contenant à la fois le texte et les images. Ce format est pratique pour un partage simple, mais peut générer des fichiers volumineux.

### HTML

Le format HTML convertit le markdown en une page web simple que vous pouvez ouvrir dans n'importe quel navigateur. Ce format offre une meilleure mise en page et permet une visualisation immédiate du contenu.

### ZIP

Le format ZIP crée une archive contenant :
- Un fichier markdown propre (sans base64)
- Un dossier "images" avec toutes les images extraites

Le markdown fait référence aux images par leurs chemins relatifs. Ce format est idéal pour :
- Réduire la taille du fichier
- Faciliter l'édition ultérieure du markdown
- Permettre l'accès direct aux images extraites

## Exemples d'utilisation

### Extraction de texte à partir d'un rapport

1. Téléchargez votre rapport PDF
2. Sélectionnez le format "Markdown"
3. Cliquez sur "Lancer le traitement OCR"
4. Attendez que le traitement soit terminé
5. Téléchargez le résultat depuis l'onglet "Téléchargement"

### Création d'une version web d'un document

1. Téléchargez votre document PDF
2. Sélectionnez le format "HTML"
3. Cliquez sur "Lancer le traitement OCR"
4. Téléchargez le fichier HTML généré
5. Ouvrez-le dans votre navigateur préféré

## Dépannage

### Erreur d'API

Si vous obtenez une erreur liée à l'API, vérifiez :
- Que votre clé API est correcte et active
- Que vous avez une connexion internet stable
- Que vous n'avez pas dépassé votre quota d'utilisation

### Problèmes de traitement

Si les résultats OCR ne sont pas satisfaisants :
- Assurez-vous que le PDF est de bonne qualité
- Vérifiez que le document ne dépasse pas les limites (50 Mo, 1000 pages)
- Essayez de reconvertir des parties spécifiques du document 