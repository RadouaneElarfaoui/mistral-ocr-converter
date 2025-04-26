# MistralOCR-Converter

Une application permettant de convertir des documents PDF en texte structuré à l'aide de l'API OCR de Mistral AI.

![Capture d'écran 2025-04-26 123152](https://github.com/user-attachments/assets/8a8b0179-eeb9-49f0-9aba-44ec43dca484)

![Capture d'écran 2025-04-26 123237](https://github.com/user-attachments/assets/66f6a5cb-1e98-4126-9f24-4f4e594fb177)

## Fonctionnalités

- Extraction de texte et d'images à partir de documents PDF
- Conversion dans différents formats :
  - **Markdown** : Format texte avec images intégrées en base64
  - **HTML** : Document HTML pour visualisation dans un navigateur
  - **ZIP** : Fichier ZIP contenant le markdown sans base64 et les images dans un dossier séparé
- Interface utilisateur conviviale propulsée par Gradio


## Utilisation avec Google Colab

Vous pouvez exécuter ce projet directement sur Google Colab sans avoir besoin de configurer un environnement local. Cliquez sur le bouton ci-dessous pour démarrer :

<a href="https://colab.research.google.com/github/RadouaneElarfaoui/mistral-ocr-converter/blob/master/mistral_ocr_solution.ipynb" target="_parent">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>


## Installation

1. Clonez ce dépôt :
```bash
git clone https://github.com/votre-nom/mistral-ocr-converter.git
cd mistral-ocr-converter
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Obtenez une clé API Mistral sur [https://docs.mistral.ai/](https://docs.mistral.ai/)

## Utilisation

Lancez l'application avec :

```bash
python mistral_ocr_solution.py
```

1. Téléchargez un fichier PDF
2. Sélectionnez le format de sortie souhaité (Markdown, HTML, ZIP)
3. Cliquez sur "Lancer le traitement OCR"
4. Consultez le résultat ou téléchargez le fichier généré

## Structure du projet

```
mistral-ocr-converter/
├── README.md                    # Documentation du projet
├── requirements.txt             # Dépendances
├── mistral_ocr_solution.py      # Script principal
├── examples/                    # Dossier pour exemples
│   ├── input/                   # PDFs d'exemple
│   └── output/                  # Résultats d'exemple
└── docs/                        # Documentation supplémentaire
```

## Licence

Ce projet est distribué sous licence MIT. 
