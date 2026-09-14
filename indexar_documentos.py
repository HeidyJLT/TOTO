"""
indexar_documentos.py — Pre-calcula el índice de RAG

Ejecútalo una sola vez (o cada vez que cambien los PDFs de
data/documentos/) para evitar volver a parsear los PDF y a normalizar
el texto en cada arranque del agente:

    python indexar_documentos.py

Genera data/indice.json, que core/rag.py carga directamente si existe.
"""
import json

from dotenv import load_dotenv
load_dotenv()

from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.rag import (
    INDICE_PATH,
    TAMANO_FRAGMENTO,
    SUPERPOSICION_FRAGMENTO,
    _cargar_pdfs,
    _cargar_csv,
    palabras_clave,
)


def _serializar(documentos):
    return [
        {
            "page_content": doc.page_content,
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page", 0),
            "keywords": sorted(palabras_clave(doc.page_content)),
        }
        for doc in documentos
    ]


def main():
    documentos = _cargar_pdfs() + _cargar_csv()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TAMANO_FRAGMENTO, chunk_overlap=SUPERPOSICION_FRAGMENTO
    )
    fragmentos = splitter.split_documents(documentos)

    indice = {
        "fragmentos": _serializar(fragmentos),
        "paginas": _serializar(documentos),
    }

    INDICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDICE_PATH.write_text(json.dumps(indice, ensure_ascii=False), encoding="utf-8")

    print(
        f"📦 Índice generado en {INDICE_PATH}: "
        f"{len(documentos)} documento(s), {len(fragmentos)} fragmento(s), "
        f"{len(documentos)} página(s) indexada(s)."
    )


if __name__ == "__main__":
    main()
