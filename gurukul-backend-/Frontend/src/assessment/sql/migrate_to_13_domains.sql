-- ========================================
-- MIGRATE TO 13 DOMAIN SYSTEM
-- ========================================
-- This script migrates from old study fields to new 13-domain system
-- Domains: IoT, Blockchain, Humanoid Robotics, AI/ML/DS, Drone Tech, 
--          Biotechnology, Pharma Tech, Gaming, VR/AR/Immersive, CyberSecurity,
--          Web Development, 3D Printing, Quantum Computing

-- Step 1: Backup existing data
CREATE TABLE IF NOT EXISTS backup_question_banks AS SELECT * FROM question_banks;
CREATE TABLE IF NOT EXISTS backup_study_fields AS SELECT * FROM study_fields;
CREATE TABLE IF NOT EXISTS backup_question_categories AS SELECT * FROM question_categories;

-- Step 2: Clear old data
TRUNCATE TABLE question_field_mapping CASCADE;
TRUNCATE TABLE question_banks CASCADE;
TRUNCATE TABLE study_fields CASCADE;
TRUNCATE TABLE question_categories CASCADE;
TRUNCATE TABLE question_usage_stats CASCADE;

-- Step 3: Create 13 new domains in study_fields
INSERT INTO study_fields (field_id, name, short_name, description, subcategories, question_weights, difficulty_distribution, is_active) VALUES
('iot', 'Internet of Things (IoT)', 'IoT', 
 'IoT devices, networks, sensors, edge computing, LPWAN, MQTT, firmware updates, and smart systems',
 '["IoT Protocols", "Sensor Networks", "Edge Computing", "LPWAN", "IoT Security", "Firmware Management"]',
 '{"IoT": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('blockchain', 'Blockchain Technology', 'Blockchain', 
 'Blockchain, distributed ledgers, smart contracts, cryptography, consensus mechanisms, Layer-2 solutions',
 '["Distributed Ledgers", "Smart Contracts", "Cryptography", "Consensus", "DeFi", "Layer-2 Scaling"]',
 '{"Blockchain": 100}',
 '{"easy": 25, "medium": 50, "hard": 25}', true),

('humanoid_robotics', 'Humanoid Robotics', 'Humanoid Robotics', 
 'Humanoid robots, locomotion, ZMP, tactile sensors, manipulation, whole-body control',
 '["Biped Locomotion", "Tactile Sensing", "Manipulation", "Control Systems", "Human-Robot Interaction"]',
 '{"Humanoid Robotics": 100}',
 '{"easy": 25, "medium": 50, "hard": 25}', true),

('ai_ml_ds', 'AI/ML/Data Science', 'AI/ML/DS', 
 'Artificial Intelligence, Machine Learning, Deep Learning, Data Science, embeddings, continual learning',
 '["Supervised Learning", "Deep Learning", "NLP", "Computer Vision", "Reinforcement Learning", "Data Analysis"]',
 '{"AI/ML/DS": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('drone_tech', 'Drone Technology', 'Drone Tech', 
 'Drones, UAVs, ESC, autonomous navigation, GPS/GNSS, Visual-Inertial Odometry, aerial systems',
 '["Flight Control", "Navigation", "Autonomous Systems", "Sensor Fusion", "Aerial Photography"]',
 '{"Drone Tech": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('biotechnology', 'Biotechnology', 'Biotech', 
 'Genetic engineering, CRISPR, PCR, cell culture, bioreactors, bioprocessing, molecular biology',
 '["Genetic Engineering", "Cell Culture", "Bioprocessing", "Molecular Biology", "Protein Engineering"]',
 '{"Biotechnology": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('pharma_tech', 'Pharmaceutical Technology', 'Pharma Tech', 
 'Drug development, clinical trials, GMP, regulatory affairs, pharmacology, bioequivalence',
 '["Drug Development", "Clinical Trials", "Quality Control", "Regulatory Affairs", "Pharmacology"]',
 '{"Pharma Tech": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('gaming', 'Gaming & Game Development', 'Gaming', 
 'Game engines, Unity, graphics programming, physics engines, multiplayer systems, game design',
 '["Game Engines", "Graphics Programming", "Physics Simulation", "Multiplayer", "Game Design"]',
 '{"Gaming": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('vr_ar_immersive', 'VR/AR/Immersive Tech', 'VR/AR', 
 'Virtual Reality, Augmented Reality, foveated rendering, motion tracking, spatial computing',
 '["Virtual Reality", "Augmented Reality", "Motion Tracking", "3D Rendering", "Spatial Audio"]',
 '{"VR/AR": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('cybersecurity', 'Cybersecurity', 'CyberSecurity', 
 'Network security, incident response, threat detection, encryption, penetration testing, zero trust',
 '["Network Security", "Threat Detection", "Cryptography", "Penetration Testing", "Incident Response"]',
 '{"CyberSecurity": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('web_dev', 'Web Development (Full-stack + AI)', 'Web Dev', 
 'Frontend, backend, Jamstack, APIs, reverse proxy, CI/CD, RAG systems, full-stack development',
 '["Frontend Development", "Backend Development", "APIs", "DevOps", "AI Integration", "Cloud Services"]',
 '{"Web Development": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('3d_printing', '3D Printing / Additive Manufacturing', '3D Printing', 
 'FDM, SLA, SLS, additive manufacturing, prototyping, metal printing, materials science',
 '["FDM Printing", "Metal Printing", "Materials", "CAD Design", "Post-Processing"]',
 '{"3D Printing": 100}',
 '{"easy": 30, "medium": 50, "hard": 20}', true),

('quantum_computing', 'Quantum Computing', 'Quantum', 
 'Qubits, superposition, quantum algorithms, quantum error correction, quantum cryptography',
 '["Quantum Algorithms", "Qubits", "Quantum Gates", "Error Correction", "Quantum Cryptography"]',
 '{"Quantum Computing": 100}',
 '{"easy": 25, "medium": 50, "hard": 25}', true)

ON CONFLICT (field_id) DO UPDATE SET
    name = EXCLUDED.name,
    short_name = EXCLUDED.short_name,
    description = EXCLUDED.description,
    subcategories = EXCLUDED.subcategories,
    question_weights = EXCLUDED.question_weights,
    difficulty_distribution = EXCLUDED.difficulty_distribution,
    updated_at = NOW();

-- Step 4: Create domain entries in question_categories (for backward compatibility)
INSERT INTO question_categories (category_id, name, description, icon, color, display_order, is_active, is_system) VALUES
('iot', 'IoT', 'Internet of Things questions', 'Cpu', 'text-blue-400 bg-blue-400/10 border-blue-400/20', 1, true, true),
('blockchain', 'Blockchain', 'Blockchain technology questions', 'Link', 'text-purple-400 bg-purple-400/10 border-purple-400/20', 2, true, true),
('humanoid_robotics', 'Humanoid Robotics', 'Humanoid robotics questions', 'Bot', 'text-green-400 bg-green-400/10 border-green-400/20', 3, true, true),
('ai_ml_ds', 'AI/ML/DS', 'AI, ML, and Data Science questions', 'Brain', 'text-pink-400 bg-pink-400/10 border-pink-400/20', 4, true, true),
('drone_tech', 'Drone Tech', 'Drone technology questions', 'Plane', 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20', 5, true, true),
('biotechnology', 'Biotechnology', 'Biotechnology questions', 'Dna', 'text-lime-400 bg-lime-400/10 border-lime-400/20', 6, true, true),
('pharma_tech', 'Pharma Tech', 'Pharmaceutical technology questions', 'Pill', 'text-rose-400 bg-rose-400/10 border-rose-400/20', 7, true, true),
('gaming', 'Gaming', 'Gaming and game development questions', 'Gamepad2', 'text-orange-400 bg-orange-400/10 border-orange-400/20', 8, true, true),
('vr_ar_immersive', 'VR/AR', 'VR/AR immersive tech questions', 'Glasses', 'text-violet-400 bg-violet-400/10 border-violet-400/20', 9, true, true),
('cybersecurity', 'CyberSecurity', 'Cybersecurity questions', 'Shield', 'text-red-400 bg-red-400/10 border-red-400/20', 10, true, true),
('web_dev', 'Web Development', 'Web development questions', 'Code', 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20', 11, true, true),
('3d_printing', '3D Printing', '3D printing questions', 'Box', 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20', 12, true, true),
('quantum_computing', 'Quantum Computing', 'Quantum computing questions', 'Atom', 'text-fuchsia-400 bg-fuchsia-400/10 border-fuchsia-400/20', 13, true, true)

ON CONFLICT (category_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    color = EXCLUDED.color,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

-- Success message
SELECT '✅ Successfully migrated to 13-domain system! Ready to insert 70 questions.' as status;
