import os
import asyncio
import hashlib
import logging
import re
from collections import OrderedDict
from typing import Dict, List, Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from mistralai.client import MistralClient
except ImportError:
    MistralClient = None

logger = logging.getLogger(__name__)


class LocalKnowledgeBase:
    """Local knowledge base for generating contextual responses without API keys."""
    
    def __init__(self):
        self.knowledge: Dict[str, Dict] = {}
        self._initialize_knowledge()
    
    def _initialize_knowledge(self):
        """Initialize with common knowledge topics."""
        self.knowledge = {
            "reinforcement_learning": {
                "keywords": ["reinforcement learning", "rl", "reward", "agent", "policy", "q-learning", "deep q"],
                "response": (
                    "Reinforcement Learning (RL) is a type of machine learning where an agent learns to make decisions "
                    "by taking actions in an environment to maximize cumulative rewards.\n\n"
                    "Key concepts:\n"
                    "• Agent: The learner/decision-maker\n"
                    "• Environment: The world the agent interacts with\n"
                    "• Actions: Choices the agent can make\n"
                    "• Rewards: Feedback signals (positive or negative)\n"
                    "• Policy: The strategy the agent follows\n"
                    "• Value Function: Expected future rewards\n\n"
                    "Common algorithms:\n"
                    "• Q-Learning: Model-free value-based method\n"
                    "• SARSA: On-policy temporal difference learning\n"
                    "• PPO (Proximal Policy Optimization): Policy gradient method\n"
                    "• DQN (Deep Q-Network): Uses neural networks for Q-values\n\n"
                    "Applications:\n"
                    "• Game playing (AlphaGo, Atari games)\n"
                    "• Robotics and automation\n"
                    "• Autonomous vehicles\n"
                    "• Recommendation systems\n"
                    "• Resource management\n\n"
                    "RL differs from supervised learning (learns from labeled data) and unsupervised learning "
                    "(finds patterns in unlabeled data) by learning through trial and error with feedback."
                )
            },
            "machine_learning": {
                "keywords": ["machine learning", "ml", "supervised", "unsupervised", "neural network", "deep learning", "training", "model"],
                "response": (
                    "Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn "
                    "and improve from experience without explicit programming.\n\n"
                    "Types of ML:\n"
                    "• Supervised Learning: Learns from labeled data (classification, regression)\n"
                    "• Unsupervised Learning: Finds patterns in unlabeled data (clustering, dimensionality reduction)\n"
                    "• Semi-supervised Learning: Uses both labeled and unlabeled data\n"
                    "• Reinforcement Learning: Learns through trial and error with rewards\n\n"
                    "Key concepts:\n"
                    "• Features: Input variables\n"
                    "• Labels: Output variables (in supervised learning)\n"
                    "• Training: Process of teaching the model\n"
                    "• Overfitting: Model learns noise in training data\n"
                    "• Generalization: Model performs well on new data\n\n"
                    "Common algorithms:\n"
                    "• Linear/Logistic Regression\n"
                    "• Decision Trees, Random Forests\n"
                    "• Support Vector Machines (SVM)\n"
                    "• Neural Networks (Deep Learning)\n"
                    "• K-Means Clustering\n\n"
                    "Applications: Image recognition, natural language processing, recommendation systems, "
                    "fraud detection, medical diagnosis, and many more."
                )
            },
            "artificial_intelligence": {
                "keywords": ["artificial intelligence", "ai", "cognitive", "intelligent", "automation"],
                "response": (
                    "Artificial Intelligence (AI) is the simulation of human intelligence by machines, "
                    "enabling them to perform tasks that typically require human intelligence.\n\n"
                    "Branches of AI:\n"
                    "• Machine Learning: Systems that learn from data\n"
                    "• Deep Learning: Neural networks with multiple layers\n"
                    "• Natural Language Processing (NLP): Understanding human language\n"
                    "• Computer Vision: Interpreting visual information\n"
                    "• Robotics: Physical agents interacting with the world\n"
                    "• Expert Systems: Rule-based decision making\n\n"
                    "AI Applications:\n"
                    "• Virtual assistants (Siri, Alexa, Mitra!)\n"
                    "• Image and speech recognition\n"
                    "• Autonomous vehicles\n"
                    "• Medical diagnosis\n"
                    "• Financial trading\n"
                    "• Game playing (chess, Go)\n\n"
                    "AI is transforming industries and creating new possibilities, while also raising important "
                    "ethical considerations about privacy, bias, and job displacement."
                )
            },
            "python_programming": {
                "keywords": ["python", "programming", "coding", "code", "script", "django", "flask"],
                "response": (
                    "Python is a high-level, versatile programming language known for its readability and simplicity.\n\n"
                    "Key features:\n"
                    "• Easy to learn and read\n"
                    "• Extensive standard library\n"
                    "• Dynamic typing\n"
                    "• Multiple programming paradigms (OOP, functional, procedural)\n"
                    "• Large community and ecosystem\n\n"
                    "Popular frameworks/libraries:\n"
                    "• Web: Django, Flask, FastAPI\n"
                    "• Data Science: NumPy, Pandas, Matplotlib\n"
                    "• ML/AI: TensorFlow, PyTorch, scikit-learn\n"
                    "• Automation: Selenium, BeautifulSoup\n"
                    "• APIs: Requests, httpx\n\n"
                    "Use cases:\n"
                    "• Web development\n"
                    "• Data analysis and visualization\n"
                    "• Machine learning and AI\n"
                    "• Automation and scripting\n"
                    "• Scientific computing\n"
                    "• Game development\n\n"
                    "Python is one of the most popular languages worldwide and is used by companies like "
                    "Google, Netflix, Instagram, and Spotify."
                )
            },
            "javascript": {
                "keywords": ["javascript", "js", "react", "node", "frontend", "web development", "typescript"],
                "response": (
                    "JavaScript (JS) is a programming language primarily used for web development.\n\n"
                    "Key features:\n"
                    "• Runs in browsers and servers (Node.js)\n"
                    "• Event-driven and asynchronous\n"
                    "• Dynamic typing\n"
                    "• Prototype-based OOP\n\n"
                    "Popular frameworks/libraries:\n"
                    "• Frontend: React, Angular, Vue.js\n"
                    "• Backend: Node.js, Express.js, Fastify\n"
                    "• Mobile: React Native, Ionic\n"
                    "• Full-stack: Next.js, Nuxt.js\n\n"
                    "Use cases:\n"
                    "• Interactive web applications\n"
                    "• Single-page applications (SPAs)\n"
                    "• Server-side rendering\n"
                    "• Mobile apps\n"
                    "• Desktop apps (Electron)\n"
                    "• Game development\n\n"
                    "JavaScript is the most widely used programming language for web development, "
                    "with TypeScript adding static typing for larger projects."
                )
            },
            "api_web_services": {
                "keywords": ["api", "rest", "graphql", "endpoint", "web service", "http", "request", "response"],
                "response": (
                    "An API (Application Programming Interface) is a set of rules that allows different software "
                    "applications to communicate with each other.\n\n"
                    "Types of APIs:\n"
                    "• REST API: Uses HTTP methods (GET, POST, PUT, DELETE) with JSON/XML\n"
                    "• GraphQL: Query language for APIs, allows requesting specific data\n"
                    "• WebSocket: Real-time bidirectional communication\n"
                    "• gRPC: High-performance RPC framework\n\n"
                    "REST API Principles:\n"
                    "• Stateless: Each request contains all needed information\n"
                    "• Resource-based: URLs represent resources\n"
                    "• HTTP methods: GET (read), POST (create), PUT (update), DELETE (remove)\n"
                    "• Status codes: 200 (success), 404 (not found), 500 (error)\n\n"
                    "API Authentication:\n"
                    "• API Keys\n"
                    "• OAuth 2.0\n"
                    "• JWT (JSON Web Tokens)\n"
                    "• Basic Auth\n\n"
                    "APIs are essential for building modern applications, enabling microservices architecture, "
                    "and integrating different services together."
                )
            },
            "database": {
                "keywords": ["database", "sql", "mysql", "postgresql", "mongodb", "nosql", "data storage", "query"],
                "response": (
                    "Databases are organized collections of structured data stored electronically.\n\n"
                    "Types:\n"
                    "• Relational (SQL): MySQL, PostgreSQL, SQLite, Oracle\n"
                    "  - Uses tables with rows and columns\n"
                    "  - Structured Query Language (SQL)\n"
                    "  - ACID compliance\n\n"
                    "• Non-relational (NoSQL): MongoDB, Redis, Cassandra\n"
                    "  - Flexible schemas\n"
                    "  - Horizontal scaling\n"
                    "  - Various data models (document, key-value, graph)\n\n"
                    "Key concepts:\n"
                    "• Normalization: Organizing data to reduce redundancy\n"
                    "• Indexing: Speeding up data retrieval\n"
                    "• Transactions: Groups of operations treated as one unit\n"
                    "• Replication: Copying data for reliability\n"
                    "• Sharding: Distributing data across multiple servers\n\n"
                    "Choosing depends on your use case: SQL for structured data with relationships, "
                    "NoSQL for flexible schemas and high scalability."
                )
            },
            "networking": {
                "keywords": ["network", "internet", "tcp", "udp", "ip", "http", "protocol", "socket", "port"],
                "response": (
                    "Computer networking connects devices to share resources and communicate.\n\n"
                    "Key protocols:\n"
                    "• TCP/IP: Reliable transmission, connection-oriented\n"
                    "• UDP: Fast, connectionless, no guarantee of delivery\n"
                    "• HTTP/HTTPS: Web protocol (secure with TLS/SSL)\n"
                    "• DNS: Domain name resolution\n"
                    "• DHCP: Automatic IP configuration\n\n"
                    "Network layers (OSI model):\n"
                    "1. Physical: Cables, hardware\n"
                    "2. Data Link: MAC addresses, frames\n"
                    "3. Network: IP addresses, routing\n"
                    "4. Transport: TCP/UDP, ports\n"
                    "5. Session: Connection management\n"
                    "6. Presentation: Data formatting\n"
                    "7. Application: HTTP, FTP, SMTP\n\n"
                    "Common concepts:\n"
                    "• IP Address: Device identifier (IPv4/IPv6)\n"
                    "• Port: Application endpoint (80 for HTTP, 443 for HTTPS)\n"
                    "• Firewall: Security barrier\n"
                    "• NAT: Network Address Translation\n\n"
                    "Networking enables the internet, cloud computing, and modern distributed systems."
                )
            },
            "cybersecurity": {
                "keywords": ["security", "cybersecurity", "hack", "encryption", "firewall", "vulnerability", "malware", "password"],
                "response": (
                    "Cybersecurity protects systems, networks, and data from digital attacks.\n\n"
                    "Common threats:\n"
                    "• Malware: Viruses, ransomware, spyware\n"
                    "• Phishing: Deceptive emails/websites\n"
                    "• Man-in-the-middle: Intercepting communications\n"
                    "• DDoS: Overwhelming systems with traffic\n"
                    "• SQL Injection: Database attacks\n\n"
                    "Protection measures:\n"
                    "• Encryption: Protecting data (AES, RSA, TLS)\n"
                    "• Authentication: Verifying identity (MFA, biometrics)\n"
                    "• Firewalls: Filtering network traffic\n"
                    "• Updates: Patching vulnerabilities\n"
                    "• Backups: Data recovery\n\n"
                    "Best practices:\n"
                    "• Use strong, unique passwords\n"
                    "• Enable multi-factor authentication\n"
                    "• Be cautious of suspicious links/attachments\n"
                    "• Regular software updates\n"
                    "• VPN for secure connections\n\n"
                    "Cybersecurity is critical for protecting personal, corporate, and national assets."
                )
            },
            "cloud_computing": {
                "keywords": ["cloud", "aws", "azure", "google cloud", "hosting", "server", "deployment", "saas", "paas", "iaas"],
                "response": (
                    "Cloud computing delivers computing services over the internet.\n\n"
                    "Service models:\n"
                    "• IaaS (Infrastructure as a Service): Virtual machines, storage (AWS EC2, Azure VMs)\n"
                    "• PaaS (Platform as a Service): Development platforms (Heroku, Google App Engine)\n"
                    "• SaaS (Software as a Service): Applications (Gmail, Office 365)\n\n"
                    "Major providers:\n"
                    "• AWS (Amazon Web Services): Most comprehensive\n"
                    "• Microsoft Azure: Enterprise-focused\n"
                    "• Google Cloud Platform: AI/ML strengths\n\n"
                    "Benefits:\n"
                    "• Scalability: Adjust resources on demand\n"
                    "• Cost-effective: Pay only for what you use\n"
                    "• Reliability: Built-in redundancy\n"
                    "• Global reach: Data centers worldwide\n\n"
                    "Use cases:\n"
                    "• Web application hosting\n"
                    "• Data storage and backup\n"
                    "• Machine learning and AI\n"
                    "• DevOps and CI/CD\n"
                    "• IoT and edge computing\n\n"
                    "Cloud has become the default for modern application deployment."
                )
            },
            "data_science": {
                "keywords": ["data science", "analytics", "visualization", "statistics", "big data", "pandas", "numpy"],
                "response": (
                    "Data Science combines statistics, programming, and domain knowledge to extract insights from data.\n\n"
                    "Key components:\n"
                    "• Data Collection: Gathering relevant data\n"
                    "• Data Cleaning: Handling missing values, outliers\n"
                    "• Exploratory Data Analysis (EDA): Understanding patterns\n"
                    "• Feature Engineering: Creating useful variables\n"
                    "• Modeling: Applying ML algorithms\n"
                    "• Communication: Presenting findings\n\n"
                    "Essential tools:\n"
                    "• Python: Pandas, NumPy, Matplotlib, Seaborn\n"
                    "• R: ggplot2, dplyr\n"
                    "• SQL: Data querying\n"
                    "• Tableau/Power BI: Visualization\n"
                    "• Jupyter Notebooks: Interactive analysis\n\n"
                    "Applications:\n"
                    "• Business intelligence\n"
                    "• Predictive analytics\n"
                    "• Customer segmentation\n"
                    "• Fraud detection\n"
                    "• Healthcare analytics\n"
                    "• Scientific research\n\n"
                    "Data scientists need a mix of technical skills, statistical knowledge, and business acumen."
                )
            },
            "devops": {
                "keywords": ["devops", "ci/cd", "docker", "kubernetes", "container", "pipeline", "deployment", "automation"],
                "response": (
                    "DevOps combines development and operations to improve software delivery.\n\n"
                    "Key practices:\n"
                    "• Continuous Integration (CI): Frequent code integration and testing\n"
                    "• Continuous Delivery (CD): Automated deployment\n"
                    "• Infrastructure as Code (IaC): Automated infrastructure management\n"
                    "• Monitoring and Logging: System observability\n\n"
                    "Popular tools:\n"
                    "• Containers: Docker, Podman\n"
                    "• Orchestration: Kubernetes, Docker Swarm\n"
                    "• CI/CD: Jenkins, GitHub Actions, GitLab CI\n"
                    "• IaC: Terraform, Ansible, CloudFormation\n"
                    "• Monitoring: Prometheus, Grafana, ELK Stack\n\n"
                    "Benefits:\n"
                    "• Faster deployment cycles\n"
                    "• Improved reliability\n"
                    "• Better collaboration\n"
                    "• Automated testing and deployment\n"
                    "• Scalability\n\n"
                    "DevOps culture emphasizes communication, collaboration, and automation between development and operations teams."
                )
            },
            "phone": {
                "keywords": ["phone", "mobile", "call", "telephone", "smartphone"],
                "response": (
                    "A phone (smartphone) is a mobile device that combines communication, computing, and internet capabilities.\n\n"
                    "Key features:\n"
                    "• Voice calls and messaging\n"
                    "• Internet access and web browsing\n"
                    "• Camera and photo/video capture\n"
                    "• GPS navigation\n"
                    "• App ecosystem\n"
                    "• Touchscreen interface\n\n"
                    "Major operating systems:\n"
                    "• iOS (Apple iPhone)\n"
                    "• Android (Samsung, Google Pixel, etc.)\n\n"
                    "Common uses:\n"
                    "• Communication (calls, texts, social media)\n"
                    "• Photography and video\n"
                    "• Navigation and maps\n"
                    "• Entertainment (games, streaming)\n"
                    "• Productivity (email, documents)\n"
                    "• Online shopping and banking\n\n"
                    "Modern smartphones are powerful computers that fit in your pocket, enabling constant connectivity."
                )
            },
            "computer": {
                "keywords": ["computer", "pc", "laptop", "desktop", "hardware", "software", "operating system"],
                "response": (
                    "A computer is an electronic device that processes data to produce information.\n\n"
                    "Key components:\n"
                    "Hardware:\n"
                    "• CPU (Central Processing Unit): The brain\n"
                    "• RAM (Random Access Memory): Working memory\n"
                    "• Storage (HDD/SSD): Data storage\n"
                    "• GPU (Graphics Processing Unit): Visual processing\n"
                    "• Motherboard: Connects all components\n\n"
                    "Software:\n"
                    "• Operating System: Windows, macOS, Linux\n"
                    "• Applications: Programs for specific tasks\n"
                    "• Drivers: Hardware communication\n\n"
                    "Types:\n"
                    "• Desktop: Stationary, powerful\n"
                    "• Laptop: Portable, integrated\n"
                    "• Server: High-performance for networks\n"
                    "• Embedded: Specialized functions\n\n"
                    "Computers are essential tools for work, education, entertainment, and communication in the modern world."
                )
            },
            "internet": {
                "keywords": ["internet", "web", "website", "online", "browser", "www"],
                "response": (
                    "The internet is a global network of interconnected computer networks.\n\n"
                    "How it works:\n"
                    "• Data is broken into packets\n"
                    "• Packets travel through routers\n"
                    "• Packets are reassembled at destination\n"
                    "• Protocols (TCP/IP) ensure reliable delivery\n\n"
                    "Key technologies:\n"
                    "• HTTP/HTTPS: Web browsing\n"
                    "• DNS: Translates domain names to IP addresses\n"
                    "• SSL/TLS: Encryption for security\n"
                    "• CDN: Content delivery networks\n\n"
                    "Internet services:\n"
                    "• World Wide Web: Websites and web applications\n"
                    "• Email: Electronic messaging\n"
                    "• File Transfer: FTP, cloud storage\n"
                    "• Streaming: Video, audio, gaming\n"
                    "• Social Media: Online communities\n\n"
                    "The internet has revolutionized communication, commerce, education, and entertainment, "
                    "connecting billions of people worldwide."
                )
            },
            "blockchain": {
                "keywords": ["blockchain", "crypto", "bitcoin", "ethereum", "cryptocurrency", "token", "nft", "defi"],
                "response": (
                    "Blockchain is a distributed, immutable ledger technology.\n\n"
                    "Key concepts:\n"
                    "• Block: Group of transactions\n"
                    "• Chain: Linked blocks using cryptography\n"
                    "• Distributed: Copies across many computers\n"
                    "• Immutable: Cannot be altered once added\n\n"
                    "How it works:\n"
                    "1. Transaction is requested\n"
                    "2. Transaction is broadcast to network\n"
                    "3. Network validates the transaction\n"
                    "4. Transaction is combined with others in a block\n"
                    "5. Block is added to the chain\n"
                    "6. Transaction is complete\n\n"
                    "Applications:\n"
                    "• Cryptocurrency: Bitcoin, Ethereum\n"
                    "• Smart Contracts: Self-executing agreements\n"
                    "• Supply Chain: Tracking goods\n"
                    "• Healthcare: Medical records\n"
                    "• Voting: Secure elections\n\n"
                    "Blockchain enables trustless transactions without intermediaries."
                )
            },
            "quantum_computing": {
                "keywords": ["quantum", "qubit", "quantum computing", "superposition", "entanglement"],
                "response": (
                    "Quantum computing uses quantum mechanics to process information.\n\n"
                    "Key concepts:\n"
                    "• Qubit: Quantum bit (0, 1, or both simultaneously)\n"
                    "• Superposition: Multiple states at once\n"
                    "• Entanglement: Connected qubits\n"
                    "• Quantum Gate: Operations on qubits\n\n"
                    "Advantages:\n"
                    "• Exponential speedup for certain problems\n"
                    "• Parallel processing through superposition\n"
                    "• Better optimization and simulation\n\n"
                    "Applications:\n"
                    "• Cryptography: Breaking/creating secure codes\n"
                    "• Drug Discovery: Molecular simulation\n"
                    "• Financial Modeling: Portfolio optimization\n"
                    "• Climate Modeling: Complex simulations\n"
                    "• Artificial Intelligence: Faster training\n\n"
                    "Current limitations:\n"
                    "• Qubits are fragile (decoherence)\n"
                    "• Requires extreme cooling\n"
                    "• High error rates\n\n"
                    "Companies like IBM, Google, and startups are advancing quantum computing technology."
                )
            },
            "robotics": {
                "keywords": ["robot", "robotics", "automation", "android", "humanoid", "drone"],
                "response": (
                    "Robotics combines engineering, computer science, and AI to create machines that can perform tasks.\n\n"
                    "Types of robots:\n"
                    "• Industrial: Manufacturing, assembly lines\n"
                    "• Service: Healthcare, hospitality\n"
                    "• Military: Defense applications\n"
                    "• Medical: Surgery, rehabilitation\n"
                    "• Domestic: Vacuum cleaners, lawn mowers\n\n"
                    "Key components:\n"
                    "• Sensors: Input from environment\n"
                    "• Actuators: Movement (motors, hydraulics)\n"
                    "• Controller: Processing and decision-making\n"
                    "• Power Source: Batteries, electricity\n\n"
                    "AI in robotics:\n"
                    "• Computer Vision: Seeing and recognizing objects\n"
                    "• Motion Planning: Navigating environments\n"
                    "• Natural Language: Understanding commands\n"
                    "• Machine Learning: Improving performance\n\n"
                    "Applications:\n"
                    "• Manufacturing and logistics\n"
                    "• Healthcare and surgery\n"
                    "• Space exploration\n"
                    "• Disaster response\n"
                    "• Agriculture\n\n"
                    "Robotics is transforming industries and creating new possibilities for automation."
                )
            }
        }
    
    def find_response(self, query: str) -> Optional[str]:
        """Find a response based on query keywords."""
        query_lower = query.lower()
        
        # Score each topic by keyword matches
        scores: Dict[str, int] = {}
        for topic, data in self.knowledge.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword in query_lower:
                    # Longer keywords get more weight
                    score += len(keyword.split())
            if score > 0:
                scores[topic] = score
        
        # Return best matching response
        if scores:
            best_topic = max(scores, key=scores.get)
            return self.knowledge[best_topic]["response"]
        
        return None


# Global knowledge base instance
knowledge_base = LocalKnowledgeBase()


class LLMBridge:
    # Bounded LRU cache to prevent memory leaks
    MAX_CACHE_SIZE = int(os.getenv("LLM_CACHE_MAX_SIZE", "500"))

    def __init__(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

        self.openai_client = AsyncOpenAI(api_key=openai_key) if AsyncOpenAI and openai_key else None
        self.groq_client = AsyncGroq(api_key=groq_key) if AsyncGroq and groq_key else None
        self.google_key = os.getenv("GOOGLE_API_KEY")
        mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = MistralClient(api_key=mistral_key) if MistralClient and mistral_key else None

        if genai and self.google_key:
            genai.configure(api_key=self.google_key)

        # Bounded LRU cache (OrderedDict)
        self.cache: OrderedDict[str, str] = OrderedDict()

    async def call_llm(self, model: str, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")

        prompt = prompt.strip()
        key = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

        if key in self.cache:
            return self.cache[key]

        try:
            # ----- OPENAI -----
            if model == "chatgpt":
                if not self.openai_client:
                    if AsyncOpenAI is None:
                        raise ImportError("openai package is not installed")
                    raise ValueError("OPENAI_API_KEY is not configured")
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GROQ -----
            elif model == "groq":
                if not self.groq_client:
                    if AsyncGroq is None:
                        raise ImportError("groq package is not installed")
                    raise ValueError("GROQ_API_KEY is not configured")
                response = await self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = response.choices[0].message.content

            # ----- GEMINI -----
            elif model == "gemini":
                if not genai:
                    raise ImportError("google-generativeai not installed")
                gemini_model = genai.GenerativeModel("gemini-pro")
                result = await asyncio.to_thread(
                    gemini_model.generate_content,
                    prompt,
                    generation_config={"temperature": 0},
                )
                output = result.text

            # ----- MISTRAL -----
            elif model == "mistral":
                if not self.mistral_client:
                    raise ImportError("mistralai not installed")
                result = await asyncio.to_thread(
                    self.mistral_client.chat,
                    model="mistral-medium",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                output = result.choices[0].message["content"]

            # ----- UNIGURU -----
            elif model == "uniguru":
                # Use local knowledge base for meaningful responses
                # Extract the user query from the prompt
                user_query_match = re.search(r"User request:\s*(.+?)(?:\n|$)", prompt)
                if user_query_match:
                    user_query = user_query_match.group(1).strip()
                else:
                    # Try to extract from the end of the prompt
                    lines = prompt.strip().split("\n")
                    user_query = lines[-1] if lines else prompt[:100]
                
                # Check cache first
                key = hashlib.sha256(f"uniguru:{user_query}".encode()).hexdigest()
                if key in self.cache:
                    output = self.cache[key]
                else:
                    # Try to find a response from knowledge base
                    kb_response = knowledge_base.find_response(user_query)
                    if kb_response:
                        output = kb_response
                    else:
                        # Generic helpful response
                        output = (
                            f"Regarding your question about '{user_query[:50]}...': "
                            f"I can help with that! While I don't have real-time internet access, "
                            f"I can provide information based on my training data.\n\n"
                            f"Could you be more specific about what aspect you'd like me to explain?"
                        )

            else:
                raise ValueError(f"Unsupported model: {model}")

        except Exception as e:
            logger.warning("LLM fallback triggered for model %s: %s", model, e)
            # Fallback to mock response on any error
            output = f"[{model.capitalize()} Mock] Response to: Context: {prompt[:50]}..."

        # Cache with LRU eviction
        # Don't cache uniguru responses to ensure fresh knowledge base responses
        if model != "uniguru":
            self.cache[key] = output
            if len(self.cache) > self.MAX_CACHE_SIZE:
                self.cache.popitem(last=False)  # Remove oldest entry

        return output


llm_bridge = LLMBridge()
