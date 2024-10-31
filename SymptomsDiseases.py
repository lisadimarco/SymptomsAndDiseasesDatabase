import sqlite3
import pandas as pd
from typing import List, Dict
import tkinter as tk
from tkinter import ttk

class DiagnosticSupport:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.symptom_weights = {}  # Per pesare i sintomi in base alla specificità
        
    def get_all_symptoms(self) -> List[Dict]:
        """Recupera tutti i sintomi disponibili"""
        query = """
        SELECT symptom_id, symptom_name, system_name, severity_scale
        FROM Symptoms s
        JOIN BodySystems b ON s.system_id = b.system_id
        ORDER BY system_name, symptom_name
        """
        return pd.read_sql(query, self.conn).to_dict('records')
    
    def find_possible_diseases(self, symptom_ids: List[int]) -> pd.DataFrame:
        """Trova possibili malattie basate sui sintomi inseriti"""
        if not symptom_ids:
            return pd.DataFrame()
            
        placeholders = ','.join('?' * len(symptom_ids))
        query = f"""
        WITH SymptomMatch AS (
            SELECT 
                d.disease_id,
                d.disease_name,
                d.description,
                COUNT(DISTINCT ds1.symptom_id) as matching_symptoms,
                COUNT(DISTINCT ds2.symptom_id) as total_disease_symptoms,
                AVG(ds1.specificity) as avg_specificity
            FROM Diseases d
            JOIN DiseaseSymptoms ds1 ON d.disease_id = ds1.disease_id
            LEFT JOIN DiseaseSymptoms ds2 ON d.disease_id = ds2.disease_id
            WHERE ds1.symptom_id IN ({placeholders})
            GROUP BY d.disease_id
        )
        SELECT 
            disease_name,
            description,
            matching_symptoms,
            total_disease_symptoms,
            ROUND(matching_symptoms * 1.0 / total_disease_symptoms * 100, 2) as match_percentage,
            ROUND(avg_specificity * 100, 2) as specificity_score
        FROM SymptomMatch
        WHERE matching_symptoms >= 2  -- Almeno 2 sintomi matching
        ORDER BY match_percentage * avg_specificity DESC
        LIMIT 10
        """
        
        return pd.read_sql(query, self.conn, params=symptom_ids)
    
    def get_risk_factors(self, disease_id: int) -> pd.DataFrame:
        """Recupera i fattori di rischio per una malattia"""
        query = """
        SELECT 
            rf.factor_name,
            rf.description,
            drf.risk_level
        FROM RiskFactors rf
        JOIN DiseaseRiskFactors drf ON rf.factor_id = drf.factor_id
        WHERE drf.disease_id = ?
        ORDER BY 
            CASE drf.risk_level
                WHEN 'Alto' THEN 1
                WHEN 'Medio' THEN 2
                WHEN 'Basso' THEN 3
            END
        """
        return pd.read_sql(query, self.conn, params=[disease_id])

class DiagnosticGUI:
    def __init__(self, diagnostic_system: DiagnosticSupport):
        self.ds = diagnostic_system
        self.window = tk.Tk()
        self.window.title("Sistema Supporto Diagnostico")
        self.selected_symptoms = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame sintomi
        symptoms_frame = ttk.LabelFrame(self.window, text="Seleziona Sintomi")
        symptoms_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        
        # Lista sintomi raggruppati per sistema
        self.symptoms_tree = ttk.Treeview(symptoms_frame, columns=("severity",))
        self.symptoms_tree.heading("#0", text="Sintomo")
        self.symptoms_tree.heading("severity", text="Gravità")
        
        symptoms = self.ds.get_all_symptoms()
        current_system = None
        for symptom in symptoms:
            if symptom['system_name'] != current_system:
                current_system = symptom['system_name']
                system_id = self.symptoms_tree.insert("", "end", text=current_system)
            
            self.symptoms_tree.insert(system_id, "end", 
                                    text=symptom['symptom_name'],
                                    values=(f"{symptom['severity_scale']}/5",))
        
        self.symptoms_tree.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Frame risultati
        results_frame = ttk.LabelFrame(self.window, text="Possibili Diagnosi")
        results_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        
        self.results_text = tk.Text(results_frame, width=50, height=20)
        self.results_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Bottone analisi
        ttk.Button(self.window, text="Analizza Sintomi", 
                  command=self.analyze_symptoms).grid(row=1, column=0, 
                                                    columnspan=2, pady=10)
        
    def analyze_symptoms(self):
        selected_items = self.symptoms_tree.selection()
        selected_symptoms = [self.symptoms_tree.item(item)["text"] 
                           for item in selected_items 
                           if self.symptoms_tree.parent(item) != ""]
        
        if not selected_symptoms:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Seleziona almeno un sintomo")
            return
        
        # Ottieni ID sintomi
        symptom_ids = []  # Qui dovresti ottenere gli ID dal database
        
        # Trova possibili malattie
        diseases = self.ds.find_possible_diseases(symptom_ids)
        
        # Mostra risultati
        self.results_text.delete(1.0, tk.END)
        for _, disease in diseases.iterrows():
            self.results_text.insert(tk.END, 
                f"\n{disease['disease_name']} ({disease['match_percentage']}% match)\n")
            self.results_text.insert(tk.END, f"Specificità: {disease['specificity_score']}%\n")
            self.results_text.insert(tk.END, f"{disease['description']}\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n")

if __name__ == "__main__":
    ds = DiagnosticSupport('diagnostic.db')
    gui = DiagnosticGUI(ds)
    gui.window.mainloop()
