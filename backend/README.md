This backend integrates Artificial Intelligence (AI) with real-world utility to act as a digital safety companion that not only responds empathetically but also provides practical help when it matters most.

The  AI-powered agent called EnhancedSheGuardiaAgent, built using LangChain and DeepSeek models. The agent is capable of understanding user queries, identifying intent, and generating human-like, context-aware responses. It uses a Retrieval-Augmented Generation (RAG) approach, which allows the model to access a structured knowledge base built on Chroma vector stores and HuggingFace embeddings. This ensures that the AI provides reliable, verified safety information rather than generic responses.

It also includes a set of specialized agent tools that extend its capabilities beyond normal chat. These tools handle real-world safety functions, such as finding nearby hospitals, police stations, or safe shelters, as well as helping users report incidents efficiently. When a user sends a message, the system first performs intent classification — determining whether it’s an emergency, location query, safety concern, or general conversation. Based on that intent, the backend decides whether to call a tool, search the knowledge base, or respond directly through the AI model.
For example:

“Is there a police station near me?” -> triggers the location tool.

“I’m feeling unsafe.” -> activates the emergency module to provide quick actions, helpline numbers, and emotional reassurance.

The backend is built with FastAPI, making it lightweight, fast, and easily integrable with the mobile frontend. Environment variables and API keys are managed securely using dotenv, and dependencies are maintained through a requirements.txt file for easy setup. The system is modular and scalable, allowing future upgrades such as new safety tools, better personalization, or multilingual support.
