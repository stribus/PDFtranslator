
from typing import List
import pymupdf
import time
from deep_translator import GoogleTranslator
import os
import sys
from enum import Enum

class TextProcessingMode(Enum):
    PARAGRAFO = "paragrafo"
    QUEBRA_DE_LINHA = "quebra_de_linha"
    QUEBRA_DE_LINHA_DINAMICO = "quebra_de_linha_dinamico"
    TAMANHO = "tamanho"
    TAMANHO_DINAMICO = "tamanho_dinamico_max"

def quebraTexto(texto: str, splitCondition: TextProcessingMode = TextProcessingMode.PARAGRAFO, tamanho: int = 125)->List[str]:
    if splitCondition == TextProcessingMode.PARAGRAFO:
        retorno = texto.split(".\n")
    elif splitCondition == TextProcessingMode.QUEBRA_DE_LINHA:
        retorno = texto.split("\n")
    elif splitCondition == TextProcessingMode.TAMANHO:
        retorno = [texto[i:i+tamanho] for i in range(0, len(texto), tamanho)]
    elif splitCondition == TextProcessingMode.TAMANHO_DINAMICO:
        retorno = []
        splited = texto.split(' ')
        texto = ''
        for i in range(len(splited)):
            if len(texto+' '+splited[i]) > tamanho:                
                retorno.append(texto)
                texto = ''
            texto += splited[i] + ' '
        if texto:
            retorno.append(texto)
    elif splitCondition == TextProcessingMode.QUEBRA_DE_LINHA_DINAMICO:
        retorno = []
        splited = texto.split('\n')
        texto = ''
        for i in splited:
            if len(texto+' '+i) > tamanho:
                retorno.append(texto)
                texto = ''
            if texto:
                texto += '\n'
            texto += i
        if texto:
            retorno.append(texto)
    else:
        retorno = [texto]
    return retorno

def traduzirTextoGrande(texto: str,splitCondition: TextProcessingMode = TextProcessingMode.PARAGRAFO)->str:
    retorno = ''
    tamanho = 125
    if splitCondition == TextProcessingMode.QUEBRA_DE_LINHA_DINAMICO:
        tamanho = 3000
    for textoQuebrado in quebraTexto(texto, splitCondition, tamanho):
        if len(textoQuebrado) < 200:
            retorno += to_portugues.translate(textoQuebrado)
            retorno += "\n"
        elif len(textoQuebrado) < 4000:
            t = to_portugues.translate(textoQuebrado)
            if t.count('\n') < 1:
                s = quebraTexto(t, TextProcessingMode.TAMANHO_DINAMICO, 125)
                for i in s:
                    retorno += i+'\n'
            else:
                retorno += t + '\n'
        elif splitCondition != TextProcessingMode.QUEBRA_DE_LINHA_DINAMICO and splitCondition != TextProcessingMode.QUEBRA_DE_LINHA:
            retorno += traduzirTextoGrande(textoQuebrado, TextProcessingMode.QUEBRA_DE_LINHA_DINAMICO)
        elif splitCondition != TextProcessingMode.QUEBRA_DE_LINHA:
            retorno += traduzirTextoGrande(textoQuebrado, TextProcessingMode.QUEBRA_DE_LINHA)
        else:
            retorno += traduzirTextoGrande(textoQuebrado, TextProcessingMode.TAMANHO)
        time.sleep(0.3)
    return retorno

# if len(sys.argv) < 2:
#     print("Usage: python script.py <pdf file> [skipPages]")
#     sys.exit(1)
    
pdf_file = '.\EJ1149107_250326_172306 (1).pdf' #sys.argv[1]

if not os.path.exists(pdf_file):    
    print(f"File {pdf_file} not found.")
    sys.exit(1)


skipPages = 0
if len(sys.argv) > 2:
    skipPages = int(sys.argv[2])

auxFileNames = pdf_file
if auxFileNames.index("\\")>0 or auxFileNames.index("/")>0:
    auxFileNames = auxFileNames.split("\\")[-1]
    auxFileNames = auxFileNames.split("/")[-1]
    
auxFileNames = auxFileNames.split(".")[0]
#remove espaços em branco
auxFileNames = auxFileNames.replace(" ", "_")
auxFileNames = auxFileNames.replace("-", "_")

# Define color "white"
WHITE = pymupdf.pdfcolor["white"]

# This flag ensures that text will be dehyphenated after extraction.
textflags = pymupdf.TEXT_DEHYPHENATE

# Configure the desired translator
to_portugues = GoogleTranslator(source="en", target="pt")

# Open the document
doc = pymupdf.open(pdf_file)

fileTxten = open(f"{auxFileNames}-en.txt", "a", encoding='utf-8', errors='ignore')
fileTxtpt = open(f"{auxFileNames}-pt.txt", "a", encoding='utf-8', errors='ignore')

# Define an Optional Content layer in the document named "portugues".
# Activate it by default.
ocg_xref = doc.add_ocg("Portuguese", on=True)

countPages = 0
maxPages = 320
# Iterate over all pages
for page in doc:
    countPages += 1
    try:
        print(f"Processing page {countPages}...")
        if countPages < skipPages:
            continue
        if countPages > maxPages:
            break
        # Extract text grouped like lines in a paragraph.
        blocks = page.get_text("blocks", flags=textflags)

        if len(blocks) == 0:
            print(f"Page {countPages} has no text.")
            continue
        # Every block of text is contained in a rectangle ("bbox")
        for block in blocks:
            bbox = block[:4]  # area containing the text
            
            text = block[4]  # the text of this block
            
            # Check if the text is empty or contains only whitespace/newlines
            if not text.strip():
                fileTxten.write(text)
                fileTxtpt.write(text)
                continue
            
            try:
                if len(text) < 200:
                    fileTxten.write(text)
                    # Invoke the actual translation to deliver us a portugues string
                    portugues = to_portugues.translate(text)
                    if portugues:
                        fileTxtpt.write(portugues + "\n")  # Adiciona a tradução seguida de uma nova linha
                    else:
                        fileTxtpt.write("\n")  # Adiciona apenas uma linha em branco
                else:
                    fileTxten.write(text)
                    portugues = traduzirTextoGrande(text)
                    fileTxtpt.write(portugues)
                    

                # Cover the English text with a white rectangle.
                page.draw_rect(bbox, color=None, fill=WHITE, oc=ocg_xref)

                # Write the portugues text into the original rectangle
                page.insert_htmlbox(
                    bbox, portugues, css="* {font-family: sans-serif;}", oc=ocg_xref
                )
                # sleep for 1 second to avoid being blocked by Google
                time.sleep(0.3)
            except Exception as e:
                print(f"Error processing block: {e}")
                continue
            
        time.sleep(1)
        fileTxten.flush()
        fileTxtpt.flush()
    except Exception as e:
        print(f"Error processing page {countPages}: {e}")
        continue
        
        

doc.subset_fonts()
doc.ez_save(f"{auxFileNames}-pt.pdf")