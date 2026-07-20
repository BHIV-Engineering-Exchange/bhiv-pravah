"""
seed_compliance_data.py — Seeds ChromaDB with realistic state and national curriculum chunks
to support deterministic routing and adversarial isolation testing.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app services
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Reconfigure stdout to UTF-8 to prevent CP1252/UnicodeEncodeError on Windows
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from app.services.vector_store import VectorStoreService
    from app.core.config import settings
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Could not import VectorStoreService or settings. Make sure python path is correct.")

# Curriculum chunks mock dataset matching physical textbooks
CHUNKS_DATA = [
    # ── 1. BALBHARATI MARATHI STANDARD 10 ────────────────────────────────────
    {
        "text": (
            "गुरुत्वाकर्षण (Gravitation): गुरुत्वाकर्षणाचा शोध सर आयझॅक न्यूटन यांनी लावला. "
            "सफरचंद झाडावरून खाली पडताना पाहून त्यांनी गुरुत्वाकर्षण बलाचा शोध घेतला. "
            "केपलरचे नियम (Kepler's Laws): १. ग्रहाची कक्षा ही लंबवर्तुळाकार असून सूर्य त्या कक्षेच्या एका नाभीवर असतो. "
            "२. ग्रहाला सूर्याशी जोडणारी सरळ रेषा समान कालावधीत समान क्षेत्रफळ व्यापन करते."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "mr",
            "class_std": 10,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Gravitation",
            "textbook_code": "MSB-S10-MR",
            "chunk_id": "bb-mr-10-s1-c1-01",
            "source": "Balbharati Class 10 Science Part 1 - Chapter 1, Page 1"
        }
    },
    {
        "text": (
            "मुक्त पतन (Free Fall): जेव्हा एखादी वस्तू केवळ गुरुत्वीय बलाच्या प्रभावाने गतिमान असते, "
            "तेव्हा त्या गतीला मुक्त पतन म्हणतात. मुक्त पतनात सुरुवातीचा वेग शून्य असतो आणि काळानुसार तो वाढत जातो. "
            "मुक्ती वेग (Escape Velocity): पृथ्वीच्या गुरुत्वीय आकर्षणातून बाहेर पडण्यासाठी वस्तूचा आवश्यक असलेला किमान वेग "
            "म्हणजे मुक्ती वेग होय. मुक्ती वेगाचे सूत्र v_esc = sqrt(2GM/R) असे आहे."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "mr",
            "class_std": 10,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Gravitation",
            "textbook_code": "MSB-S10-MR",
            "chunk_id": "bb-mr-10-s1-c1-02",
            "source": "Balbharati Class 10 Science Part 1 - Chapter 1, Page 11"
        }
    },
    
    # ── 2. BALBHARATI ENGLISH STANDARD 10 ────────────────────────────────────
    {
        "text": (
            "Gravitation: The phenomenon of gravitation was discovered by Sir Isaac Newton. "
            "Newton concluded that the force of attraction exists between any two objects in the universe. "
            "Kepler's Laws: 1. The orbit of a planet is an ellipse with the Sun at one of the foci. "
            "2. The line joining the planet and the Sun sweeps equal areas in equal intervals of time."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "en",
            "class_std": 10,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Gravitation",
            "textbook_code": "MSB-S10-EN",
            "chunk_id": "bb-en-10-s1-c1-01",
            "source": "Balbharati Class 10 Science Part 1 (English) - Chapter 1, Page 1"
        }
    },
    
    # ── 3. NCERT ENGLISH STANDARD 10 ─────────────────────────────────────────
    {
        "text": (
            "Chemical Reactions and Equations: A chemical reaction is a process where the reactant substances "
            "transform into product substances. A balanced chemical equation has an equal number of atoms of "
            "each element on both the reactant and product sides. For example, 2H2 + O2 -> 2H2O represents "
            "the combination reaction of hydrogen and oxygen forming water."
        ),
        "metadata": {
            "board": "NCERT",
            "medium": "en",
            "class_std": 10,
            "subject": "science",
            "chapter": 1,
            "chapter_title": "Chemical Reactions and Equations",
            "textbook_code": "NCERT-S10-EN",
            "chunk_id": "nc-en-10-s-c1-01",
            "source": "NCERT Class 10 Science - Chapter 1, Page 3"
        }
    },
    {
        "text": (
            "Combination and Decomposition Reactions: In a combination reaction, two or more reactants "
            "combine to form a single product. In a decomposition reaction, a single reactant breaks down "
            "into two or more products when energy in the form of heat, light or electricity is supplied. "
            "Thermal decomposition of Calcium Carbonate gives Calcium Oxide and Carbon Dioxide."
        ),
        "metadata": {
            "board": "NCERT",
            "medium": "en",
            "class_std": 10,
            "subject": "science",
            "chapter": 1,
            "chapter_title": "Chemical Reactions and Equations",
            "textbook_code": "NCERT-S10-EN",
            "chunk_id": "nc-en-10-s-c1-02",
            "source": "NCERT Class 10 Science - Chapter 1, Page 7"
        }
    },
    
    # ── 4. NCERT ENGLISH STANDARD 9 ──────────────────────────────────────────
    {
        "text": (
            "Matter in Our Surroundings: Everything in this universe is made up of material which scientists "
            "have named 'matter'. Matter occupies space and has mass. The particles of matter are very small, "
            "have spaces between them, are continuously moving, and attract each other. Matter exists in "
            "three primary physical states: solid, liquid, and gas."
        ),
        "metadata": {
            "board": "NCERT",
            "medium": "en",
            "class_std": 9,
            "subject": "science",
            "chapter": 1,
            "chapter_title": "Matter in Our Surroundings",
            "textbook_code": "NCERT-S09-EN",
            "chunk_id": "nc-en-09-s-c1-01",
            "source": "NCERT Class 9 Science - Chapter 1, Page 1"
        }
    },
    
    # ── 5. NCERT ENGLISH STANDARD 8 ──────────────────────────────────────────
    {
        "text": (
            "Crop Production and Management: All living organisms require food. Plants can make their food "
            "themselves. In order to provide food for a large population - regular production, proper "
            "management and distribution is necessary. The same kind of plants grown and cultivated at one "
            "place on a large scale is called a crop (e.g., wheat, rice)."
        ),
        "metadata": {
            "board": "NCERT",
            "medium": "en",
            "class_std": 8,
            "subject": "science",
            "chapter": 1,
            "chapter_title": "Crop Production and Management",
            "textbook_code": "NCERT-S08-EN",
            "chunk_id": "nc-en-08-s-c1-01",
            "source": "NCERT Class 8 Science - Chapter 1, Page 1"
        }
    },
    
    # ── 6. NCERT ENGLISH STANDARD 7 ──────────────────────────────────────────
    {
        "text": (
            "Nutrition in Plants: Nutrients are necessary for our body. Carbohydrates, proteins, fats, "
            "vitamins and minerals are components of food. Plants are the only organisms that can prepare "
            "food for themselves by using water, carbon dioxide and minerals. Photosynthesis is the food "
            "making process in green plants, facilitated by chlorophyll."
        ),
        "metadata": {
            "board": "NCERT",
            "medium": "en",
            "class_std": 7,
            "subject": "science",
            "chapter": 1,
            "chapter_title": "Nutrition in Plants",
            "textbook_code": "NCERT-S07-EN",
            "chunk_id": "nc-en-07-s-c1-01",
            "source": "NCERT Class 7 Science - Chapter 1, Page 1"
        }
    },
    
    # ── 7. NCERT ENGLISH STANDARD 6 ──────────────────────────────────────────
    {
        "text": (
            "Components of Food: The food that we eat contains various nutrients needed by our body. "
            "The major nutrients in our food are carbohydrates, proteins, fats, vitamins and minerals. "
            "In addition, food contains dietary fibres and water which are also needed by our body. "
            "Carbohydrates and fats mainly provide energy to our body, while proteins build muscles."
        ),
        "metadata": {
            "board": "NCERT",
            "medium": "en",
            "class_std": 6,
            "subject": "science",
            "chapter": 1,
            "chapter_title": "Components of Food",
            "textbook_code": "NCERT-S06-EN",
            "chunk_id": "nc-en-06-s-c1-01",
            "source": "NCERT Class 6 Science - Chapter 1, Page 1"
        }
    },

    # ── 8. BALBHARATI MARATHI STANDARD 9 ─────────────────────────────────────
    {
        "text": (
            "गतीचे नियम (Laws of Motion): जेव्हा एखाद्या वस्तूची जागा आजूबाजूच्या वस्तूंच्या संदर्भात बदलते, तेव्हा ती वस्तू गतिमान आहे असे म्हणतात. "
            "न्यूटनचे गतीचे नियम: १. पहिला नियम (जडत्वाचा नियम) - जोपर्यंत वस्तूवर बाह्य बल कार्यरत नसते, तोपर्यंत ती वस्तू स्थिर किंवा एकाच गतीने मार्गक्रमण करत राहते."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "mr",
            "class_std": 9,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Laws of Motion",
            "textbook_code": "MSB-S09-MR",
            "chunk_id": "bb-mr-09-s1-c1-01",
            "source": "Balbharati Class 9 Science - Chapter 1, Page 1"
        }
    },

    # ── 9. BALBHARATI MARATHI STANDARD 8 ─────────────────────────────────────
    {
        "text": (
            "सजीव सृष्टी व सूक्ष्मजीवांचे वर्गीकरण (Living World and Classification of Microbes): पृथ्वीवरील सजीवांचे वर्गीकरण करण्यासाठी "
            "रॉबर्ट व्हिटाकर यांनी पाच सृष्टी पद्धती (Five Kingdom System) मांडली. यामध्ये मोनेरा, प्रोटिस्टा, कवक, वनस्पती व प्राणी या पाच सृष्टींचा समावेश होतो."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "mr",
            "class_std": 8,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Living World and Classification of Microbes",
            "textbook_code": "MSB-S08-MR",
            "chunk_id": "bb-mr-08-s1-c1-01",
            "source": "Balbharati Class 8 Science - Chapter 1, Page 1"
        }
    },

    # ── 10. BALBHARATI MARATHI STANDARD 7 ────────────────────────────────────
    {
        "text": (
            "सजीव सृष्टी: अनुकूलन आणि वर्गीकरण (The Living World: Adaptations and Classification). सजीवांमध्ये त्यांच्या राहण्याच्या आणि "
            "वातावरणाशी जुळवून घेण्याच्या क्षमतेनुसार जे बदल घडून येतात, त्याला अनुकूलन (Adaptation) म्हणतात. वाळवंटी वनस्पतींमध्ये पाण्याचे बाष्पीभवन रोखण्यासाठी पाने काट्यांमध्ये बदलतात."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "mr",
            "class_std": 7,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "The Living World: Adaptations and Classification",
            "textbook_code": "MSB-S07-MR",
            "chunk_id": "bb-mr-07-s1-c1-01",
            "source": "Balbharati Class 7 Science - Chapter 1, Page 1"
        }
    },

    # ── 11. BALBHARATI MARATHI STANDARD 6 ────────────────────────────────────
    {
        "text": (
            "नैसर्गिक संसाधने - हवा, पाणी आणि जमीन (Natural Resources - Air, Water and Land): पृथ्वीवरील सजीव सृष्टी टिकून राहण्यासाठी "
            "हवा, पाणी आणि जमीन हे अत्यंत महत्त्वाचे घटक आहेत. हवेमध्ये प्रामुख्याने नायट्रोजन, ऑक्सिजन, कार्बन डायऑक्साइड आणि इतर निष्क्रिय वायूंचा समावेश असतो."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "mr",
            "class_std": 6,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Natural Resources - Air, Water and Land",
            "textbook_code": "MSB-S06-MR",
            "chunk_id": "bb-mr-06-s1-c1-01",
            "source": "Balbharati Class 6 Science - Chapter 1, Page 1"
        }
    },

    # ── 12. BALBHARATI ENGLISH STANDARD 9 ────────────────────────────────────
    {
        "text": (
            "Laws of Motion: Motion is a relative concept. If the position of an object is changing with respect to its surroundings, "
            "then it is said to be in motion. Newton's First Law of Motion explains inertia, stating that an object continues at rest unless acted upon by an external unbalanced force."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "en",
            "class_std": 9,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Laws of Motion",
            "textbook_code": "MSB-S09-EN",
            "chunk_id": "bb-en-09-s1-c1-01",
            "source": "Balbharati Class 9 Science (English) - Chapter 1, Page 1"
        }
    },

    # ── 13. BALBHARATI ENGLISH STANDARD 8 ────────────────────────────────────
    {
        "text": (
            "Living World and Classification of Microbes: Robert Whittaker proposed the Five Kingdom System of classification in 1969. "
            "The five kingdoms are Monera, Protista, Fungi, Plantae, and Animalia, helping systematic study of biological diversity."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "en",
            "class_std": 8,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Living World and Classification of Microbes",
            "textbook_code": "MSB-S08-EN",
            "chunk_id": "bb-en-08-s1-c1-01",
            "source": "Balbharati Class 8 Science (English) - Chapter 1, Page 1"
        }
    },

    # ── 14. BALBHARATI ENGLISH STANDARD 7 ────────────────────────────────────
    {
        "text": (
            "The Living World: Adaptations and Classification. Adaptation is the gradual change occurring in the body parts and behavior "
            "of organisms which helps them to adjust to their surroundings. Plants in desert areas have thorns instead of leaves to reduce transpiration."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "en",
            "class_std": 7,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "The Living World: Adaptations and Classification",
            "textbook_code": "MSB-S07-EN",
            "chunk_id": "bb-en-07-s1-c1-01",
            "source": "Balbharati Class 7 Science (English) - Chapter 1, Page 1"
        }
    },

    # ── 15. BALBHARATI ENGLISH STANDARD 6 ────────────────────────────────────
    {
        "text": (
            "Natural Resources - Air, Water and Land: The substances available in nature which satisfy the basic needs of living things "
            "are called natural resources. Air, water, and land are crucial natural resources. Air contains nitrogen (78%), oxygen (21%), and other gases."
        ),
        "metadata": {
            "board": "BALBHARATI",
            "medium": "en",
            "class_std": 6,
            "subject": "science_and_technology_1",
            "chapter": 1,
            "chapter_title": "Natural Resources - Air, Water and Land",
            "textbook_code": "MSB-S06-EN",
            "chunk_id": "bb-en-06-s1-c1-01",
            "source": "Balbharati Class 6 Science (English) - Chapter 1, Page 1"
        }
    }
]

def main():
    if not ML_AVAILABLE:
        print("ML dependencies not available. Skipping seeding.")
        return
        
    print("Initializing VectorStoreService...")
    vector_store = VectorStoreService(
        backend=settings.VECTOR_STORE_BACKEND,
        collection_name=settings.VECTOR_STORE_COLLECTION
    )
    
    print("Clearing existing vector collection...")
    try:
        vector_store.clear_collection()
        print("Collection cleared successfully.")
    except Exception as e:
        print(f"Failed to clear collection: {e}")
        
    print(f"Seeding {len(CHUNKS_DATA)} realistic curriculum chunks...")
    count = 0
    for chunk in CHUNKS_DATA:
        result = vector_store.add_knowledge(
            text=chunk["text"],
            metadata=chunk["metadata"]
        )
        print(f" -> Added chunk {chunk['metadata']['chunk_id']}: {result['chunks_added']} chunks")
        count += result["chunks_added"]
        
    print(f"Successfully seeded a total of {count} chunks in ChromaDB!")
    
    # Run a test search to verify metadata filtering
    print("\nRunning Verification Search (Balbharati MR standard 10)...")
    results = vector_store.search(
        query="गुरुत्वाकर्षण आणि केपलरचे नियम",
        top_k=2,
        filter_metadata={"board": "BALBHARATI", "medium": "mr", "class_std": 10}
    )
    print(f"Found {len(results)} matching chunks:")
    for r in results:
        print(f" - [{r['metadata']['chunk_id']}] Score: {r['score']:.4f}")
        print(f"   Text: {r['text'][:120]}...")
        print(f"   Source: {r['metadata']['source']}")

if __name__ == "__main__":
    main()
