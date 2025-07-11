"""
Libreria per la gestione del template trasporto.json
Gestisce le preferenze per i mezzi di trasporto
"""

import json
from typing import Dict, Any, Tuple, List
from datetime import datetime
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pathlib import Path
from .template_manager import TemplateManager
from .base_template import BaseTemplate
from .database import get_db_connection

class TrasportoTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Template {self.template_name} non trovato, uso il template di default")
            with open("template/trasporto.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def verifica_luogo(self, data: Dict[str, Any], model_path: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica il luogo di partenza usando gli embedding.
        Controlla che il luogo inserito corrisponda a una destinazione valida nel database.
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        try:
            if 'luogo_partenza' not in data or not data['luogo_partenza']:
                print("Luogo di partenza mancante o vuoto")
                data['luogo_partenza'] = None
                return True, "Luogo di partenza mancante", data

            print(f"Verifica luogo di partenza: {data['luogo_partenza']}")
            
            print("Tentativo di connessione al database...")
            conn = get_db_connection()
            print("Connessione al database stabilita con successo")
            cursor = conn.cursor()

            try:
                print("Generazione embedding per il luogo di partenza...")
                print(f"Testo da convertire in embedding: '{data['luogo_partenza']}'")
                luogo_partenza_embedding = self.model.encode(data['luogo_partenza'])
                print(f"Embedding generato con successo, dimensione: {len(luogo_partenza_embedding)}")
                luogo_partenza_embedding = luogo_partenza_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                data['luogo_partenza'] = None
                return True, "Errore nella generazione dell'embedding", data

            print("Esecuzione query per trovare il luogo più simile...")
            cursor.execute("""
                SELECT luogo, embedding_luogo <=> %s::vector as distanza
                FROM destinazioni_locali
                WHERE embedding_luogo IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (luogo_partenza_embedding,))
            
            risultato = cursor.fetchall()
            print(f"Risultato query: {risultato}")
            
            if risultato:
                luogo_corretto, distanza = risultato[0]
                print(f"Distanza trovata: {distanza}")
                if distanza > 0.4:
                    print(f"Distanza troppo grande ({distanza} > 0.4), rimuovo il valore")
                    data['luogo_partenza'] = None
                    return True, "Nessun luogo simile trovato nel database", data
                
                print(f"Aggiornamento luogo da '{data['luogo_partenza']}' a '{luogo_corretto}'")
                data['luogo_partenza'] = luogo_corretto
                return True, "Luogo di partenza verificato e corretto", data
            else:
                print("Nessun risultato trovato nel database, rimuovo il valore")
                data['luogo_partenza'] = None
                return True, "Nessun luogo trovato nel database", data

        except Exception as e:
            print(f"Errore durante la verifica del luogo: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            data['luogo_partenza'] = None
            return True, f"Errore durante la verifica del luogo: {str(e)}", data
        finally:
            if 'cursor' in locals():
                print("Chiusura cursor")
                cursor.close()
            if 'conn' in locals():
                print("Chiusura connessione")
                conn.close()

    def verifica_tipo_veicolo(self, data: Dict[str, Any], model_path: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica il tipo di veicolo usando gli embedding.
        Controlla che il veicolo inserito corrisponda a uno disponibile nel database.
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        try:
            if 'tipo_veicolo' not in data or not data['tipo_veicolo']:
                print("Tipo di veicolo mancante o vuoto")
                data['tipo_veicolo'] = None
                return True, "Tipo di veicolo mancante", data

            print(f"Verifica tipo di veicolo: {data['tipo_veicolo']}")
            
            print("Tentativo di connessione al database...")
            conn = get_db_connection()
            print("Connessione al database stabilita con successo")
            cursor = conn.cursor()

            try:
                print("Generazione embedding per il tipo di veicolo...")
                print(f"Testo da convertire in embedding: '{data['tipo_veicolo']}'")
                tipo_veicolo_embedding = self.model.encode(data['tipo_veicolo'])
                print(f"Embedding generato con successo, dimensione: {len(tipo_veicolo_embedding)}")
                tipo_veicolo_embedding = tipo_veicolo_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                data['tipo_veicolo'] = None
                return True, "Errore nella generazione dell'embedding", data

            print("Esecuzione query per trovare il tipo di veicolo più simile...")
            cursor.execute("""
                SELECT veicolo, embedding_veicolo <=> %s::vector as distanza
                FROM tipo_trasporto
                WHERE embedding_veicolo IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (tipo_veicolo_embedding,))
            
            risultato = cursor.fetchall()
            print(f"Risultato query: {risultato}")
            
            if risultato:
                tipo_veicolo_corretto, distanza = risultato[0]
                print(f"Distanza trovata: {distanza}")
                if distanza > 0.4:
                    print(f"Distanza troppo grande ({distanza} > 0.4), rimuovo il valore")
                    data['tipo_veicolo'] = None
                    return True, "Nessun tipo di veicolo simile trovato nel database", data
                
                print(f"Aggiornamento tipo di veicolo da '{data['tipo_veicolo']}' a '{tipo_veicolo_corretto}'")
                data['tipo_veicolo'] = tipo_veicolo_corretto
                return True, "Tipo di veicolo verificato e corretto", data
            else:
                print("Nessun risultato trovato nel database, rimuovo il valore")
                data['tipo_veicolo'] = None
                return True, "Nessun tipo di veicolo trovato nel database", data

        except Exception as e:
            print(f"Errore durante la verifica del tipo di veicolo: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            data['tipo_veicolo'] = None
            return True, f"Errore durante la verifica del tipo di veicolo: {str(e)}", data
        finally:
            if 'cursor' in locals():
                print("Chiusura cursor")
                cursor.close()
            if 'conn' in locals():
                print("Chiusura connessione")
                conn.close()

    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        print("[DEBUG] Inizio validazione dati trasporto")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        
        try:
            # Validazione tipo_veicolo usando verifica_tipo_veicolo
            if 'tipo_veicolo' in data:
                print(f"[DEBUG] Validazione tipo_veicolo: {data['tipo_veicolo']}")
                is_valid, msg, updated_data = self.verifica_tipo_veicolo(data)
                corrected_data.update(updated_data)
                print(f"[DEBUG] tipo_veicolo validato: {corrected_data.get('tipo_veicolo')}")

            # Validazione luogo_partenza usando verifica_luogo
            if 'luogo_partenza' in data:
                print(f"[DEBUG] Validazione luogo_partenza: {data['luogo_partenza']}")
                is_valid, msg, updated_data = self.verifica_luogo(data)
                corrected_data.update(updated_data)
                print(f"[DEBUG] luogo_partenza validato: {corrected_data.get('luogo_partenza')}")
            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template trasporto
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        warnings = []
        errors = []
        original_data = data.copy()
        # Inizializza updated_data con tutti i campi del template, impostando quelli mancanti a None
        updated_data = {campo: None for campo in self.get_template_data().keys()}
        # Aggiorna con i dati ricevuti
        updated_data.update(data)
        try:
            
            # 4. Chiama il metodo della classe base per la validazione standard
            updated_data, base_warnings, base_errors = super().verifica_template(updated_data)
            warnings.extend(base_warnings)
            errors.extend(base_errors)

            data_was_different = self.are_data_different(original_data, updated_data)
            #verifica se è completo
            template_completo = all(
                campo in updated_data and (
                    updated_data[campo] is not None and 
                    (isinstance(updated_data[campo], bool) or updated_data[campo])
                )
                for campo in self.get_template_data().keys()
            )
            print(f"[DEBUG] Template completo: {template_completo}")
            
            # Se il template è completo, imposta data_was_different a True
            if template_completo:
                data_was_different = True
                print("[DEBUG] Template completo, data_was_different impostato a True")
            
            return updated_data, data_was_different, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            data_was_different = self.are_data_different(original_data, updated_data)
            return updated_data, data_was_different, warnings, errors