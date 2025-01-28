
import pymupdf
import time
from deep_translator import GoogleTranslator
import os
import sys

if len(sys.argv) < 2:
    print("Usage: python script.py <pdf file>")
    sys.exit(1)
    
pdf_file = sys.argv[1]

if not os.path.exists(pdf_file):    
    print(f"File {pdf_file} not found.")
    sys.exit(1)

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
skipPages = 0
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
            try:

                fileTxten.write(text)
                # Invoke the actual translation to deliver us a portugues string
                portugues = to_portugues.translate(text)
                if portugues:
                    fileTxtpt.write(portugues + "\n")  # Adiciona a tradução seguida de uma nova linha
                else:
                    fileTxtpt.write("\n")  # Adiciona apenas uma linha em branco

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