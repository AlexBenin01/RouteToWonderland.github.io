"""
Libreria per l'estrazione delle informazioni dal testo utilizzando il modello NuExtract-2.0-2B
"""

import json
import sys
import os
from typing import Dict, Any, Optional, Tuple

# Aggiungi la directory corrente al path per permettere l'import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import extract_entities

class NuExtract:
    def __init__(self):
        pass

    def process_extraction(self, text: str, empty_template: Dict[str, Any], saved_template: Dict[str, Any]) -> Tuple[Dict[str, Any]]:
        """
        Elabora il testo e aggiorna il template con le nuove informazioni.
        Aggiorna tutti i campi se il nuovo valore è valido (non None e non "null").
        
        Args:
            text: Il testo da analizzare
            empty_template: Il template vuoto che definisce la struttura
            saved_template: Il template con i dati già salvati
            
        Returns:
            Tuple[Dict[str, Any], bool]: Il template aggiornato e un flag che indica se sono state trovate nuove informazioni
        """
        print(f"Empty template Nuestract: {empty_template}")
        print(f"Saved template Nuestract: {saved_template}")
        # Verifica che il modello esista
        try:
            # Usa la funzione extract_entities da utils.py per ottenere la risposta dal modello
            result = extract_entities(
                text=text,
                template=json.dumps(empty_template, ensure_ascii=False)
            )
            
            # Converti la risposta in JSON
            try:
                extracted_data = json.loads(result)
                print(f"Dati estratti: {extracted_data}")
            except json.JSONDecodeError:
                print(f"Errore nel parsing della risposta JSON: {result}")
                return saved_template
            
            # Inizializza il template aggiornato come copia del template salvato
            template_aggiornato = saved_template.copy()
            print(f"Dati template aggiornato Nuestract: {template_aggiornato}")
            # Aggiorna il template con i nuovi dati estratti
            for key, value in extracted_data.items():
                print(f"\nConfronto per chiave '{key}':")
                print(f"Valore estratto: {value} (tipo: {type(value)})")
                print(f"Valore nel template: {template_aggiornato.get(key)} (tipo: {type(template_aggiornato.get(key))})")
                
                # Se il valore è una lista
                if isinstance(value, list):
                    # Se la chiave esiste già nel template e contiene una lista
                    if key in template_aggiornato and isinstance(template_aggiornato[key], list):
                        # Aggiungi solo gli elementi che non sono già presenti
                        for item in value:
                            if item not in template_aggiornato[key]:
                                template_aggiornato[key].append(item)
                                print(f"AGGIUNGO elemento alla lista {key}: {item}")
                    # Se la chiave non esiste o non contiene una lista, sostituisci con la nuova lista
                    elif value:  # solo se la lista non è vuota
                        print(f"AGGIORNO: {key} da {template_aggiornato.get(key)} a {value}")
                        template_aggiornato[key] = value
                # Per valori non-lista, aggiorna solo se non è null
                elif value is not None and value != "null":
                    print(f"AGGIORNO: {key} da {template_aggiornato.get(key)} a {value}")
                    template_aggiornato[key] = value
                else:
                    print(f"NON AGGIORNO: {key} - mantengo il valore esistente {template_aggiornato.get(key)}")
            
            print(f"\nTemplate finale: {template_aggiornato}")
            return template_aggiornato
            
        except Exception as e:
            print(f"Errore durante l'estrazione: {str(e)}")
            return saved_template

    def process_exit(self, text: str, empty_template: Dict[str, Any]) -> Tuple[bool]:
        """
        Elabora il testo e aggiorna il template con le nuove informazioni.
        Aggiorna tutti i campi se il nuovo valore è valido (non None e non "null").
        
        Args:
            text: Il testo da analizzare
            empty_template: Il template vuoto che definisce la struttura
            saved_template: Il template con i dati già salvati
            
        Returns:
            Tuple[Dict[str, Any], bool]: Il template aggiornato e un flag che indica se sono state trovate nuove informazioni
        """
        try:
            # Usa la funzione extract_entities da utils.py per ottenere la risposta dal modello
            result = extract_entities(
                text=text,
                template=json.dumps(empty_template, ensure_ascii=False)
            )
            
            # Converti la risposta in JSON
            try:
                extracted_data = json.loads(result)
                print(f"Dati estratti: {extracted_data}")
            except json.JSONDecodeError:
                print(f"Errore nel parsing della risposta JSON: {result}")
                return False
            
            # Se almeno uno dei valori è True, significa che vogliamo uscire
            if extracted_data.get('next_step') is True or extracted_data.get('exit') is True or extracted_data.get('quit') is True:
                print("imposto a True - Vogliamo uscire")
                return True
            
            # Se next_step è False o exit è False, significa che vogliamo uscire
            return False
            

            
        except Exception as e:
            print(f"Errore durante l'estrazione: {str(e)}")
            return False