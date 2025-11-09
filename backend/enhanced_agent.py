from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from agent_tools import AgentTools
from rag_knowledge import setup_knowledge_base
from dotenv import load_dotenv
from typing import List, Dict, Optional
import os
import re

load_dotenv()

class EnhancedSheGuardiaAgent:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.1,
            max_tokens=1000,
            timeout=180,
            max_retries=5,
            api_key=os.getenv('DEEPSEEK_API_KEY')
        )
        
        # Custom RAG prompt template
        self.custom_prompt_template = """
You are SheGuardia - a caring companion, protector, and trusted friend for women. You're like a wise, supportive sister who's always there to listen, guide, and empower.

**Core Identity:**
- Warm, empathetic, and genuinely caring - never robotic or generic
- Balance practical safety advice with emotional support and motivation
- Remember past conversations to provide personalized, meaningful responses
- Focus on building confidence and strength, not fear

**How to Respond:**
- Keep responses engaging, conversational, and interactive - up to 100 words
- Use natural, warm language like texting a close friend
- Reference previous messages to show continuity and that you're listening
- Ask follow-up questions to make it feel like a real conversation
- For safety concerns: Validate feelings + 1-2 immediate actionable tips + question about current status
- For emotional moments: Validate + supportive encouragement + question to learn more
- For daily life: Encouragement or celebration + relatable comment
- Outside scope: Gently redirect to safety/wellbeing while asking how you can help
- Multiple concerns: Address urgent first (safety > emotional > general), tie back to previous context

**Key Behaviors:**
- Greetings: "Hey lovely! How can I help you today? 💜"
- Unsafe situations: "I'm here with you. Are you safe now? [1-2 quick safety steps] Let's keep you secure."
- Anxiety/worry: "That sounds really tough. I'm listening - tell me more about what's going on?"
- Achievements: "That's amazing! You should be so proud! What's next for you?"
- Always end with a question to continue dialogue unless it's a clear closing

**Use Context Effectively:**
- Provide specific, accurate information from the knowledge base
- If information isn't available, be honest while still offering general support and asking for clarification
- Connect safety tips to empowerment and confidence-building
- Frame advice as "you've got this" rather than "be careful"
- Reference conversation history to make responses personal

**Remember:**
- Be like a caring friend: supportive, engaging, and always there
- Every interaction should leave her feeling heard, stronger, and connected
- Be her cheerleader, her midnight companion, her voice of reason
- Adapt your energy: gentle for vulnerable moments, enthusiastic for celebrations, steady for crises

Context: {context}
Question: {question}

Respond as her trusted friend who genuinely cares. Make it engaging and reference history where appropriate.
"""
        
        # Load RAG knowledge base
        try:
            kb = setup_knowledge_base()
            self.vector_store = kb.vectorstore
            print("✅ RAG knowledge base loaded successfully")
        except Exception as e:
            print(f"❌ Error loading RAG knowledge base: {e}")
            self.vector_store = None
        
        # Initialize agent tools
        try:
            self.agent_tools = AgentTools()
            self.tools = self.agent_tools.get_tools()
            print(f"✅ Loaded {len(self.tools)} agent tools")
        except Exception as e:
            print(f"❌ Error loading agent tools: {e}")
            self.tools = []
        
        # Create agent
        if self.tools:
            self.agent = self._create_agent()
        else:
            self.agent = None
    
    def _create_agent(self):
        """Create ReAct agent with tools"""
        prompt_template = """
You are SheGuardia, an AI assistant specialized in women's safety and emergency services.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Be empathetic, helpful, and provide practical safety advice.

IMPORTANT: After writing a line starting with "Thought:", the VERY NEXT line MUST be either:
- "Action:" followed by one of [{tool_names}] and an "Action Input:" line, or
- "Final Answer:" if you are ready to answer.
Do not write any other text between "Thought:" and the required next line.

Question: {input}
Thought: {agent_scratchpad}
"""
        
        prompt = PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
            template=prompt_template
        )
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors="I couldn't follow the tool format perfectly. Here's my best direct answer.",
            max_iterations=20,  
            max_execution_time=180, 
            return_intermediate_steps=True
        )
    
    def search_knowledge_base(self, query: str, k: int = 3) -> str:
        """Search RAG knowledge base"""
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search(query, k=k)
                return "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                print(f"Error searching knowledge base: {e}")
                return "Knowledge base search failed."
        return "Knowledge base not available."
    
    def classify_intent(self, query: str, conversation_history: List[Dict] = None) -> str:
        """Main intent classification method that uses LLM exclusively"""
        # Build context from conversation history
        context_messages = []
        if conversation_history:
            # Get last 8 messages for context
            recent_messages = conversation_history[-8:]
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "SheGuardia"
                context_messages.append(f"{role}: {msg['content']}")
        
        # Add current query
        context_messages.append(f"User: {query}")
        
        # Create full context
        full_context = "\n".join(context_messages)
        
        # Create prompt for intent classification with detailed examples
        classification_prompt = f"""
You are an intent classifier for the SheGuardia women's safety chatbot.
Based on the user's message and conversation history, classify the intent into one of these categories:

1. greeting - For greetings, introductions, and initial conversations
   Examples: "hello", "hi there", "good morning", "how are you"

2. emergency - ONLY for actual emergency situations where someone is in immediate danger
   Examples: "someone is following me", "I'm being threatened", "I'm in danger", "I need urgent help"
   Note: Context matters! "Help me please" alone is NOT an emergency unless context suggests danger

3. location - For queries about finding nearby services or locations
   Examples: "where is the nearest hospital", "find police stations near me", "safe places nearby"

4. safety - For questions about safety tips, advice, general help requests, or emotional support
   Examples: "how to stay safe at night", "what should I do if I feel uncomfortable", "I need advice"

5. general - For other general conversation or topics not directly related to safety
   Examples: "what's the weather", "tell me a joke", "what can you do"

Conversation History:
{full_context}

Current Query: "{query}"

Analyze the FULL CONVERSATION CONTEXT carefully before deciding. Consider:
1. Is there immediate danger mentioned in the current message or recent history?
2. Is the user asking about locations or nearby services?
3. Is the user seeking safety advice or emotional support?
4. Is this just a greeting or general conversation?

Respond with ONLY ONE WORD - the intent category that best matches.
"""
        
        try:
            response = self.llm.invoke(classification_prompt)
            intent = response.content.strip().lower()
            
            # Validate the intent is one of our categories
            valid_intents = ['greeting', 'emergency', 'location', 'safety', 'general']
            if intent not in valid_intents:
                # Default to safety for unrecognized intents
                intent = 'safety'
                
            print(f"LLM classified intent: {intent}")
            return intent
        except Exception as e:
            print(f"Error in LLM intent classification: {e}")
            # If LLM fails, default to safety as the most reasonable fallback
            print("Defaulting to 'safety' intent due to LLM error")
            return 'safety'
    
    def process_query(self, query: str, conversation_history: List[Dict] = None) -> str:
        """Process user query with enhanced capabilities and conversation memory"""
        
        # Build context from conversation history
        context_messages = []
        if conversation_history:
            # Get last 4 messages for context
            recent_messages = conversation_history[-8:]
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "SheGuardia"
                context_messages.append(f"{role}: {msg['content']}")
        
        # Add current query
        context_messages.append(f"User: {query}")
        
        # Create full context
        full_context = "\n".join(context_messages)
        
        # Use LLM-based intent classification
        intent = self.classify_intent(query, conversation_history)
        
        try:
            if intent == 'greeting':
                return "Welcome, how can I help you?"
            
            elif intent == 'emergency':
                # Handle emergency situations with personalized response
                # First, get any location-based information if needed
                location_info = ""
                if 'near' in query.lower() or 'location' in query.lower() or 'follow' in query.lower():
                    try:
                        agent_response = self.agent.invoke({"input": full_context})
                        location_info = agent_response['output']
                    except Exception as e:
                        print(f"Error getting location info: {e}")
                        location_info = ""
                
                # Create a personalized emergency prompt
                emergency_prompt = f"""
{self.custom_prompt_template}

Conversation History:
{full_context}

Context: This is an EMERGENCY situation. The user needs immediate help and personalized guidance.
Additional location information: {location_info}

Question: {query}

Respond as a caring, supportive friend who understands this is an emergency. 
Include these critical emergency numbers:
- Police: 100
- Ambulance: 102
- Women Helpline: 1091
- All Emergency: 112

Provide specific, actionable advice for their exact situation. Be calm, clear, and reassuring.
Include both immediate safety steps AND emotional support.
"""
                
                try:
                    # Get personalized emergency response
                    response = self.llm.invoke(emergency_prompt)
                    return response.content
                except Exception as e:
                    print(f"Error getting personalized emergency response: {e}")
                    # Fallback to standard emergency response
                    emergency_response = """
🚨 **EMERGENCY ASSISTANCE**

I'm here with you. This sounds serious, and your safety is the priority right now.

**Immediate Actions:**
1. 📞 **Call Emergency Services:**
   - Police: 100
   - Ambulance: 102
   - Women Helpline: 1091
   - All Emergency: 112

2. 📍 **Share your location** with trusted contacts
3. 🏃‍♀️ **Move to a safe, public place** if possible
4. 📱 **Keep your phone charged** and accessible

Stay on the line with me. How can I help you right now?
"""
                    if location_info:
                        emergency_response += "\n\n" + location_info
                    
                    return emergency_response
            
            elif intent == 'location':
                # Use agent for location-based queries with context
                response = self.agent.invoke({"input": full_context})
                return response['output']
            
            elif intent == 'safety':
                # Use RAG for safety knowledge with custom prompt and context
                knowledge = self.search_knowledge_base(query)
                
                if knowledge and knowledge != "Knowledge base not available.":
                    # Use the custom prompt template with conversation context
                    formatted_prompt = f"""
{self.custom_prompt_template}

Conversation History:
{full_context}

Context: {knowledge}
Question: {query}

Provide a clear, informative response in up to 100 words. Be caring and supportive.
"""
                    
                    response = self.llm.invoke(formatted_prompt)
                    return response.content
                else:
                    # Fallback response when no context available
                    return "I don't have specific information about that in my knowledge base. However, I'm here to help with women's safety. Could you ask me something more specific about safety tips, precautions, or emergency situations?"
            
            else:
                # General conversation with context-aware response
                knowledge = ""
                if any(word in query.lower() for word in ['women', 'safety', 'secure', 'protect']):
                    knowledge = self.search_knowledge_base(query)
                    if not knowledge or knowledge == "Knowledge base not available.":
                        knowledge = "No specific knowledge available. Provide general support."
                else:
                    knowledge = "No specific knowledge available. If off-topic, gently redirect to safety topics while referencing history."

                formatted_prompt = f"""
{self.custom_prompt_template}

Conversation History:
{full_context}

Context: {knowledge}
Question: {query}

Respond as her trusted friend who genuinely cares. Make it engaging and reference history where appropriate.
"""
                response = self.llm.invoke(formatted_prompt)
                return response.content
                
                # Non-safety related queries
                return "I am the SheGuardia Women Safety Bot."
        
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. "
            
            # Provide emergency numbers as fallback
            if intent == 'emergency' or intent == 'location':
                error_msg += "\n\n🚨 **Emergency Numbers:**\n"
                error_msg += "• Police: 100\n"
                error_msg += "• Ambulance: 102\n"
                error_msg += "• Women Helpline: 1091\n"
                error_msg += "• All Emergency: 112"
            
            return error_msg
    
    def get_agent_info(self) -> dict:
        """Get information about the agent's capabilities"""
        return {
            "tools_available": len(self.tools),
            "tool_names": [tool.name for tool in self.tools],
            "rag_available": self.vector_store is not None,
            "llm_model": "deepseek-chat"
        }
