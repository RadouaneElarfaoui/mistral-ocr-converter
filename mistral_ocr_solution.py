# -*- coding: utf-8 -*-
"""
structured_ocr_v1_0_1.py

Version améliorée du script OCR Mistral original
Développée pour une compatibilité avec mistralai 1.7.0+
"""

# --- Importation des bibliothèques nécessaires ---
import os
import time
import tempfile
import traceback
import re
import shutil
import zipfile
import base64
from pathlib import Path
from typing import Tuple, List, Dict, Optional, Union
import io

# Importation de Gradio pour l'interface utilisateur
import gradio as gr

# Importation des composants Mistral AI (version 1.7.0+)
from mistralai import Mistral

# --- Configuration et initialisation ---
# Clé API Mistral (À remplacer par votre propre clé)
API_KEY = "rQaeYPaRSTkGAEEjf8Z5wwFXvghBD4a2"

# Initialisation du client Mistral
try:
    client = Mistral(api_key=API_KEY)
    print("✅ Client Mistral initialisé avec succès")
except Exception as e:
    print(f"❌ Erreur lors de l'initialisation du client Mistral: {e}")
    raise

# --- Fonctions de traitement des images et du texte ---
def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """
    Remplace les références d'images par leur contenu base64 dans le markdown.
    
    Args:
        markdown_str: Texte markdown contenant des références d'images
        images_dict: Dictionnaire associant ID d'image à leur contenu base64
        
    Returns:
        Le texte markdown avec les images intégrées en base64
    """
    if not markdown_str or not images_dict:
        return markdown_str
        
    for img_name, base64_str in images_dict.items():
        # Vérifier que la chaîne base64 contient le préfixe nécessaire
        if not base64_str.startswith('data:image'):
            # Détecter automatiquement le format d'image
            if base64_str.startswith('/9j/'): # JPEG
                mime_type = 'image/jpeg'
            elif base64_str.startswith('iVBOR'): # PNG
                mime_type = 'image/png'
            elif base64_str.startswith('R0lGO'): # GIF
                mime_type = 'image/gif'
            else:
                mime_type = 'image/png' # Format par défaut
                
            base64_str = f"data:{mime_type};base64,{base64_str}"

        # Remplacer les références d'image par leur contenu base64
        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})"
        )
        
    return markdown_str

def get_combined_markdown(ocr_response, embed_images=True) -> str:
    """
    Combine les pages OCR en un seul document markdown.
    
    Args:
        ocr_response: Réponse OCR de l'API Mistral
        embed_images: Si True, intègre les images en base64, sinon les laisse en références simples
        
    Returns:
        Document markdown combiné
    """
    markdowns = []
    
    # Vérifier si la réponse OCR est valide
    if not ocr_response or not hasattr(ocr_response, 'pages') or not ocr_response.pages:
        return "Erreur: La réponse OCR semble vide ou invalide."

    # Traiter chaque page
    for page_num, page in enumerate(ocr_response.pages, 1):
        image_data = {}
        
        # Extraction des images
        if hasattr(page, 'images') and page.images:
            for img in page.images:
                if hasattr(img, 'id') and hasattr(img, 'image_base64'):
                    # Utiliser le même format d'ID d'image que dans extract_images_from_ocr_response
                    img_name = f"page{page_num}_{img.id}"
                    image_data[img_name] = img.image_base64
                    
                    # Modifier le markdown pour utiliser ce format d'ID
                    if hasattr(page, 'markdown'):
                        page.markdown = page.markdown.replace(
                            f"![{img.id}]({img.id})",
                            f"![{img_name}]({img_name})"
                        )
        
        # Extraction du markdown
        page_markdown = getattr(page, 'markdown', '')
        
        # Traitement des images selon le mode choisi
        if embed_images:
            processed_page = replace_images_in_markdown(page_markdown, image_data)
        else:
            # Laisser les références d'images telles quelles pour traitement ultérieur
            processed_page = page_markdown
        
        # Ajouter un en-tête de page pour une meilleure organisation
        processed_markdown = f"## Page {page_num}\n\n{processed_page}"
        markdowns.append(processed_markdown)

    return "\n\n" + "\n\n".join(markdowns)

def extract_images_from_ocr_response(ocr_response) -> Dict[str, str]:
    """
    Extrait toutes les images de la réponse OCR.
    
    Args:
        ocr_response: Réponse OCR de l'API Mistral
        
    Returns:
        Dictionnaire {nom_image: contenu_base64}
    """
    images_dict = {}
    
    if not ocr_response or not hasattr(ocr_response, 'pages'):
        return images_dict
    
    for page_num, page in enumerate(ocr_response.pages, 1):
        if hasattr(page, 'images') and page.images:
            for img in page.images:
                if hasattr(img, 'id') and hasattr(img, 'image_base64'):
                    # Nommer les images par page et index pour éviter les doublons
                    img_name = f"page{page_num}_{img.id}"
                    images_dict[img_name] = img.image_base64
    
    return images_dict

def create_zip_with_images(markdown_content: str, images_dict: Dict[str, str], output_path: str) -> str:
    """
    Crée un fichier ZIP contenant le fichier markdown et les images dans un dossier séparé.
    Le markdown généré ne contient PAS les images en base64, mais des références aux fichiers images.
    
    Args:
        markdown_content: Contenu markdown à inclure
        images_dict: Dictionnaire des images {nom_image: contenu_base64}
        output_path: Chemin de sortie pour le ZIP sans extension
        
    Returns:
        Chemin du fichier ZIP créé
    """
    # Ajouter l'extension ZIP si nécessaire
    if not output_path.lower().endswith('.zip'):
        output_path += '.zip'
    
    # Créer un dossier temporaire pour préparer le contenu du ZIP
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Créer le dossier images
        images_dir = os.path.join(temp_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Préparation du markdown propre
        clean_markdown = markdown_content
        
        # Dictionnaire pour associer les IDs d'images aux noms de fichiers
        img_filename_map = {}
        
        # Extraire et sauvegarder toutes les images
        for img_name, base64_str in images_dict.items():
            # Déterminer le format de l'image
            if base64_str.startswith('data:'):
                mime_type, b64data = base64_str.split(',', 1)
                ext = mime_type.split('/')[1].split(';')[0]
            else:
                # Détecter automatiquement le format d'image
                if base64_str.startswith('/9j/'): # JPEG
                    ext = 'jpg'
                    b64data = base64_str
                elif base64_str.startswith('iVBOR'): # PNG
                    ext = 'png'
                    b64data = base64_str
                elif base64_str.startswith('R0lGO'): # GIF
                    ext = 'gif'
                    b64data = base64_str
                else:
                    ext = 'png'  # Format par défaut
                    b64data = base64_str
            
            # Générer un nom de fichier
            img_filename = f"{img_name}.{ext}"
            img_filename_map[img_name] = img_filename
            
            # On garde aussi une référence avec juste l'ID sans le préfixe "page{num}_"
            # pour capturer tous les cas possibles
            if img_name.startswith("page") and "_" in img_name:
                original_id = img_name.split("_", 1)[1]
                img_filename_map[original_id] = img_filename
            
            # Écrire l'image
            with open(os.path.join(images_dir, img_filename), 'wb') as f:
                f.write(base64.b64decode(b64data))
        
        # Rechercher tous les motifs d'images dans le markdown en utilisant une expression régulière générale
        # pour trouver toutes les syntaxes de type ![quelquechose](reference)
        img_pattern = r'!\[(.*?)\]\((.*?)\)'
        
        # Fonction de callback pour remplacer les références
        def replace_img_refs(match):
            alt_text = match.group(1)
            img_ref = match.group(2)
            
            # Si la référence est dans notre dictionnaire, utilisez-la
            if img_ref in img_filename_map:
                return f'![{alt_text}](images/{img_filename_map[img_ref]})'
            
            # Si c'est une référence base64, rechercher par texte alternatif
            if img_ref.startswith('data:image') and alt_text in img_filename_map:
                return f'![{alt_text}](images/{img_filename_map[alt_text]})'
                
            # Si on ne trouve toujours pas, garder telle quelle
            return match.group(0)
        
        # Appliquer le remplacement
        clean_markdown = re.sub(img_pattern, replace_img_refs, clean_markdown)
        
        # Écrire le fichier markdown propre
        with open(os.path.join(temp_dir, "document.md"), 'w', encoding='utf-8') as f:
            f.write(clean_markdown)
        
        # Créer le fichier ZIP
        with zipfile.ZipFile(output_path, 'w') as zipf:
            # Ajouter le fichier markdown
            zipf.write(os.path.join(temp_dir, "document.md"), "document.md")
            
            # Ajouter les images
            for root, _, files in os.walk(images_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join("images", file)
                    zipf.write(file_path, arcname)
        
        return output_path
    
    finally:
        # Nettoyer le dossier temporaire
        shutil.rmtree(temp_dir)

def create_html_file(markdown_content: str, output_path: str) -> str:
    """
    Convertit le contenu markdown en HTML simple pour être visualisé dans un navigateur.
    
    Args:
        markdown_content: Contenu markdown à convertir
        output_path: Chemin de sortie pour le HTML sans extension
        
    Returns:
        Chemin du fichier HTML créé
    """
    # Ajouter l'extension HTML si nécessaire
    if not output_path.lower().endswith('.html'):
        output_path += '.html'
    
    # Conversion manuelle simple de markdown en HTML basique
    # Note: Ceci est une implémentation simple qui pourrait être améliorée
    html_content = markdown_content
    
    # Convertir les titres
    html_content = re.sub(r'## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    
    # Convertir les paragraphes (lignes sans titres)
    html_content = re.sub(r'^(?!<h[1-6]>)(.*?)$', r'<p>\1</p>', html_content, flags=re.MULTILINE)
    
    # Convertir les sauts de ligne multiples en un seul
    html_content = re.sub(r'<\/p>\s*<p><\/p>\s*<p>', r'</p><p>', html_content)
    
    # Nettoyage des paragraphes vides
    html_content = re.sub(r'<p><\/p>', r'', html_content)
    
    # Ajouter la structure HTML de base
    html_output = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Résultat OCR</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #333; margin-top: 24px; }}
        h2 {{ color: #444; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 20px; }}
        img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0; }}
        p {{ margin-bottom: 16px; }}
    </style>
</head>
<body>
    <h1>Résultat de l'OCR</h1>
    {html_content}
</body>
</html>
"""
    
    # Écrire le fichier HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    return output_path

# --- Fonction principale de traitement OCR ---
def process_pdf_with_ocr(uploaded_file_obj, model_name="mistral-ocr-latest", output_format="markdown", show_progress=True):
    """
    Traite un fichier PDF avec OCR Mistral et retourne le contenu selon le format demandé.
    
    Args:
        uploaded_file_obj: Objet fichier téléchargé via Gradio
        model_name: Nom du modèle OCR à utiliser
        output_format: Format de sortie ("markdown", "html", "zip")
        show_progress: Afficher les messages de progression dans la console
        
    Returns:
        Tuple contenant (contenu_markdown, chemin_fichier, messages_log)
    """
    log_messages = []
    uploaded_file_mistral = None
    temp_files = []
    
    def log(message):
        """Fonction d'aide pour enregistrer les messages de progression"""
        if show_progress:
            print(message)
        log_messages.append(message)
    
    # Vérifier si un fichier a été téléchargé
    if uploaded_file_obj is None:
        log("❌ Erreur: Veuillez télécharger un fichier PDF.")
        return "Veuillez télécharger un fichier PDF.", None, "\n".join(log_messages)

    try:
        # Récupérer le chemin du fichier temporaire créé par Gradio
        input_pdf_path = Path(uploaded_file_obj.name)
        log(f"📄 Traitement du fichier: {input_pdf_path.name}")

        # 1. Télécharger le fichier PDF vers Mistral
        log("🔄 Téléchargement du fichier vers Mistral...")
        start_upload = time.time()
        
        uploaded_file_mistral = client.files.upload(
            file={
                "file_name": input_pdf_path.name,
                "content": input_pdf_path.read_bytes(),
            },
            purpose="ocr",
        )
        
        upload_time = time.time() - start_upload
        log(f"✅ Fichier téléchargé avec l'ID: {uploaded_file_mistral.id} en {upload_time:.2f} secondes")

        # 2. Obtenir l'URL signée (validité courte)
        log("🔄 Obtention de l'URL signée...")
        signed_url = client.files.get_signed_url(file_id=uploaded_file_mistral.id, expiry=60)
        log("✅ URL signée obtenue")

        # 3. Traitement OCR - Utilisation de l'API OCR de Mistral selon la documentation officielle
        log(f"🔄 Démarrage du traitement OCR avec le modèle {model_name}...")
        start_time = time.time()
        
        pdf_response = client.ocr.process(
            model=model_name,
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            },
            include_image_base64=True
        )
        
        processing_time = time.time() - start_time
        log(f"✅ Traitement OCR terminé en {processing_time:.2f} secondes")

        # 4. Génération du markdown combiné
        log("🔄 Génération du markdown...")
        if output_format == "zip":
            # Pour le ZIP, on génère un markdown sans intégrer les images en base64
            final_markdown_content = get_combined_markdown(pdf_response, embed_images=False)
            log("✅ Génération du markdown sans images base64 terminée")
        else:
            # Pour les autres formats, on intègre les images en base64
            final_markdown_content = get_combined_markdown(pdf_response, embed_images=True)
            log("✅ Génération du markdown avec images base64 terminée")
        
        # 5. Extraction des images si nécessaire
        images_dict = {}
        if output_format in ["html", "zip"]:
            log("🔄 Extraction des images...")
            images_dict = extract_images_from_ocr_response(pdf_response)
            log(f"✅ {len(images_dict)} images extraites")

        # 6. Préparation des fichiers selon le format demandé
        log(f"🔄 Préparation du fichier au format {output_format}...")
        temp_dir = tempfile.gettempdir()
        base_filename = input_pdf_path.stem
        
        if output_format == "markdown":
            # Format Markdown standard
            output_filename = f"{base_filename}_ocr_result.md"
            output_path = os.path.join(temp_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown_content)
            
            temp_files.append(output_path)
            log(f"✅ Fichier Markdown enregistré: {output_path}")
        
        elif output_format == "html":
            # Conversion en HTML
            output_filename = f"{base_filename}_ocr_result.html"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Créer le HTML
            create_html_file(final_markdown_content, output_path)
            
            temp_files.append(output_path)
            log(f"✅ Fichier HTML enregistré: {output_path}")
        
        elif output_format == "zip":
            # Création d'un ZIP avec les images séparées
            output_filename = f"{base_filename}_ocr_result.zip"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Créer le ZIP avec markdown sans base64
            create_zip_with_images(final_markdown_content, images_dict, output_path)
            
            temp_files.append(output_path)
            log(f"✅ Fichier ZIP enregistré: {output_path}")
        
        else:
            # Format par défaut (markdown)
            output_filename = f"{base_filename}_ocr_result.md"
            output_path = os.path.join(temp_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown_content)
            
            temp_files.append(output_path)
            log(f"✅ Fichier Markdown enregistré: {output_path}")

        # Retourner le contenu markdown, le chemin du fichier et les logs
        return final_markdown_content, output_path, "\n".join(log_messages)

    except Exception as e:
        error_message = f"❌ Une erreur est survenue: {e}"
        log(error_message)
        log(traceback.format_exc())
        return f"### Erreur\n{error_message}\n\nVeuillez vérifier votre connexion et votre clé API.", None, "\n".join(log_messages)
        
    finally:
        # Nettoyage facultatif: supprimer le fichier téléchargé du stockage Mistral
        try:
            if uploaded_file_mistral:
                log(f"🔄 Suppression du fichier {uploaded_file_mistral.id} du stockage Mistral...")
                client.files.delete(file_id=uploaded_file_mistral.id)
                log("✅ Fichier supprimé du stockage Mistral")
        except Exception as delete_e:
            log(f"⚠️ Impossible de supprimer le fichier {uploaded_file_mistral.id}: {delete_e}")

# --- Interface utilisateur Gradio ---
def create_interface():
    """Crée et lance l'interface utilisateur Gradio"""
    
    # Style CSS personnalisé pour une meilleure apparence
    custom_css = """
    .success-text { color: green; font-weight: bold; }
    .error-text { color: red; font-weight: bold; }
    .info-text { color: blue; }
    """
    
    # Création de l'interface
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft(primary_hue="blue")) as iface:
        gr.Markdown("# 📝 Interface OCR Mistral PDF")
        gr.Markdown("""
        Cette application utilise l'API Mistral OCR pour extraire du texte et des images à partir de fichiers PDF.
        Téléchargez un PDF pour obtenir son contenu au format Markdown avec images intégrées.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(label="Télécharger un PDF", file_types=['.pdf'])
                model_dropdown = gr.Dropdown(
                    choices=["mistral-ocr-latest"], 
                    value="mistral-ocr-latest",
                    label="Modèle OCR"
                )
                format_dropdown = gr.Dropdown(
                    choices=["markdown", "html", "zip"], 
                    value="markdown",
                    label="Format de sortie"
                )
                process_button = gr.Button("🚀 Lancer le traitement OCR", variant="primary")
                
            with gr.Column(scale=2):
                log_output = gr.Textbox(label="Journal de traitement", lines=10)
        
        with gr.Tabs():
            with gr.TabItem("Résultat"):
                markdown_output = gr.Markdown(label="Résultat OCR (Markdown avec images)")
                
            with gr.TabItem("Téléchargement"):
                file_output = gr.File(label="Télécharger le résultat")
                
            with gr.TabItem("À propos"):
                gr.Markdown("""
                ## À propos de cette application
                
                Cette interface utilise l'API Mistral OCR pour effectuer la reconnaissance optique de caractères (OCR) sur des documents PDF.
                
                ### Fonctionnalités
                - Extraction de texte et d'images à partir de PDF
                - Génération de fichier Markdown avec images intégrées
                - Exportation en différents formats (Markdown, HTML, ZIP avec images séparées)
                - Visualisation directe du résultat
                
                ### Formats de sortie disponibles
                - **Markdown** : Format texte avec images intégrées en base64
                - **HTML** : Document HTML pour visualisation dans un navigateur
                - **ZIP** : Fichier ZIP contenant le markdown sans base64 et les images dans un dossier séparé
                
                ### Détails des formats
                - Le format **Markdown** intègre les images directement dans le texte en base64, ce qui donne un fichier autonome mais plus volumineux.
                - Le format **HTML** permet une visualisation directe dans un navigateur, avec mise en page et formatage.
                - Le format **ZIP** est idéal pour un partage efficace - il contient un fichier markdown propre (sans base64) et un dossier 'images' séparé. Les références dans le markdown pointent vers ce dossier d'images, ce qui rend le contenu plus lisible et éditable.
                
                ### Remarques
                - Une clé API Mistral valide est nécessaire pour utiliser ce service
                - Les documents volumineux peuvent prendre plus de temps à traiter
                - Limite de taille : 50 Mo maximum et 1000 pages maximum par document
                
                Version: 1.0.1
                
                ### Référence
                Cette application est basée sur [la documentation officielle de Mistral AI](https://docs.mistral.ai/capabilities/document/)
                """)
                
        # Connexion du bouton de traitement à la fonction OCR
        process_button.click(
            fn=process_pdf_with_ocr,
            inputs=[pdf_input, model_dropdown, format_dropdown],
            outputs=[markdown_output, file_output, log_output]
        )

    # Lancement de l'interface
    iface.launch(share=False, debug=True)

# --- Point d'entrée principal ---
if __name__ == "__main__":
    print("🚀 Démarrage de l'interface OCR Mistral...")
    create_interface() 