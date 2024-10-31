-- Tabella Sistemi/Apparati
CREATE TABLE BodySystems (
    system_id INT PRIMARY KEY,
    system_name VARCHAR(50),
    description TEXT
);

-- Tabella Sintomi
CREATE TABLE Symptoms (
    symptom_id INT PRIMARY KEY,
    system_id INT,
    symptom_name VARCHAR(100),
    description TEXT,
    severity_scale INT CHECK (severity_scale BETWEEN 1 AND 5),
    is_emergency BOOLEAN,
    FOREIGN KEY (system_id) REFERENCES BodySystems(system_id)
);

-- Tabella Malattie
CREATE TABLE Diseases (
    disease_id INT PRIMARY KEY,
    disease_name VARCHAR(100),
    description TEXT,
    icd_code VARCHAR(10),  -- Codice ICD-10
    prevalence VARCHAR(50),
    typical_age_range VARCHAR(50)
);

-- Tabella di collegamento Sintomi-Malattie
CREATE TABLE DiseaseSymptoms (
    disease_id INT,
    symptom_id INT,
    frequency VARCHAR(20), -- 'Comune', 'Raro', 'Molto comune'
    specificity DECIMAL(3,2), -- Quanto il sintomo è specifico per questa malattia (0-1)
    PRIMARY KEY (disease_id, symptom_id),
    FOREIGN KEY (disease_id) REFERENCES Diseases(disease_id),
    FOREIGN KEY (symptom_id) REFERENCES Symptoms(symptom_id)
);

-- Tabella Fattori di Rischio
CREATE TABLE RiskFactors (
    factor_id INT PRIMARY KEY,
    factor_name VARCHAR(100),
    description TEXT
);

-- Collegamento Malattie-Fattori di Rischio
CREATE TABLE DiseaseRiskFactors (
    disease_id INT,
    factor_id INT,
    risk_level VARCHAR(20), -- 'Alto', 'Medio', 'Basso'
    PRIMARY KEY (disease_id, factor_id),
    FOREIGN KEY (disease_id) REFERENCES Diseases(disease_id),
    FOREIGN KEY (factor_id) REFERENCES RiskFactors(factor_id)
);

-- Query di esempio per trovare malattie basate sui sintomi
CREATE VIEW PossibleDiagnoses AS
SELECT 
    d.disease_name,
    d.description,
    COUNT(ds.symptom_id) as matching_symptoms,
    AVG(ds.specificity) as avg_specificity,
    GROUP_CONCAT(DISTINCT s.symptom_name) as symptoms_list
FROM Diseases d
JOIN DiseaseSymptoms ds ON d.disease_id = ds.disease_id
JOIN Symptoms s ON ds.symptom_id = s.symptom_id
GROUP BY d.disease_id;
