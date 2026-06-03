import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi.responses import StreamingResponse
import fastapi

from .schemas import CopilotChatPayload, CopilotStructuredResponse
from .ollama_client import OllamaClient
from .intent_router import IntentRouter
from .context_builder import ContextBuilder
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .tools.design_state import DesignStateTool
from .tools.prediction_tool import PredictionTool
from .rag.indexer import Indexer

BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/data/rag_index")

def run_copilot_stream(payload: CopilotChatPayload) -> StreamingResponse:
    """
    Executes a chat session in a streaming fashion.
    Yields NDJSON tokens and appends the final structured config_patch at the end.
    """
    config_dict = payload.config.model_dump()

    # 0. Sanitize inputs and check for malicious scripts / prompt injections
    from .validators import sanitize_input_text, detect_malicious_input
    
    # Sanitize config string values to prevent injection
    for key, val in config_dict.items():
        if isinstance(val, str):
            config_dict[key] = sanitize_input_text(val)
            
    is_malicious = False
    malicious_msg = ""
    if payload.messages:
        latest_msg = payload.messages[-1]
        if latest_msg.role == "user":
            latest_msg.content = sanitize_input_text(latest_msg.content)
            mal_flag, mal_desc = detect_malicious_input(latest_msg.content)
            if mal_flag:
                is_malicious = True
                malicious_msg = mal_desc
            
    if is_malicious:
        # If malicious input is detected, return immediate block response without LLM
        def security_block_generator():
            block_text = f"Acción denegada por seguridad: {malicious_msg} Por favor, realiza consultas técnicas legítimas sobre diseño 3D o parámetros mecánicos."
            # Yield token by token for realistic typing effect/stream compatibility
            for token in block_text.split(" "):
                yield json.dumps({"type": "token", "content": token + " "}) + "\n"
            
            # Yield final structured response conforming to schema
            from .schemas import CopilotStructuredResponse, AIAnalysis, VariantData, ConfigPatch
            structured_resp = CopilotStructuredResponse(
                analysis=AIAnalysis(
                    text=block_text,
                    objective_detected="security_block",
                    key_findings="Entrada maliciosa bloqueada.",
                    mechanical_justification="El sistema de seguridad previno el procesamiento de este script o instrucción no segura."
                ),
                variants=[
                    VariantData(
                        id="security_block",
                        name="Bloqueo de Seguridad",
                        description="Se detectó y bloqueó un intento de inyección o script malicioso.",
                        score=0.0,
                        compression_score=0.0,
                        energy_absorption_score=0.0,
                        stability_score=0.0,
                        printability_score=0.0,
                        risk_level="HIGH",
                        estimated_print_time="0m",
                        estimated_mass="0g",
                        warnings=[malicious_msg],
                        config_patch=ConfigPatch()
                    )
                ],
                recommended_variant="security_block",
                ui_actions=[]
            )
            yield json.dumps({"type": "final", "response": structured_resp.model_dump()}) + "\n"
            
        return StreamingResponse(security_block_generator(), media_type="application/x-ndjson")

    client = OllamaClient()
    
    # 1. Intent routing
    latest_query = payload.messages[-1].content if payload.messages else ""
    intent_data = IntentRouter.classify_intent(latest_query)
    intent = intent_data["intent"]

    # 2. Context Builder
    builder = ContextBuilder()
    context = builder.build_context(latest_query, config_dict, intent)

    # 3. Format system prompt
    config_summary = DesignStateTool.format_design_summary(config_dict)
    system_prompt = PromptBuilder.build_system_prompt(config_summary, context, intent=intent)

    # 4. Compile messages for Ollama
    ollama_messages = [{"role": "system", "content": system_prompt}]
    for msg in payload.messages:
        ollama_messages.append({"role": msg.role, "content": msg.content})

    # 5. Involve Ollama chat stream
    try:
        stream_generator = client.chat_stream(ollama_messages)
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=503,
            detail=f"Ollama server is unavailable: {str(e)}"
        )

    def event_generator():
        assistant_response_acc = []
        
        try:
            for line in stream_generator:
                if not line:
                    continue
                    
                line_data = json.loads(line)
                
                # Check for errors in Ollama stream
                if "error" in line_data:
                    yield json.dumps({"type": "error", "content": line_data["error"]}) + "\n"
                    return
                
                # Extract token content
                token = line_data.get("message", {}).get("content", "")
                if token:
                    assistant_response_acc.append(token)
                    yield json.dumps({"type": "token", "content": token}) + "\n"
                
                # If finished, run the structured response extraction
                if line_data.get("done", False):
                    full_text = "".join(assistant_response_acc)
                    
                    if intent == "casual_chat":
                        # Bypass LLM extraction parser for casual chat
                        from .schemas import CopilotStructuredResponse, AIAnalysis
                        structured_resp = CopilotStructuredResponse(
                            analysis=AIAnalysis(
                                text=full_text,
                                objective_detected="casual_chat",
                                key_findings="Conversación casual.",
                                mechanical_justification="No se requieren cambios paramétricos para charla informal."
                            ),
                            variants=[],
                            recommended_variant="",
                            ui_actions=[]
                        )
                    else:
                        # Call extractor in background
                        parser = ResponseParser(client)
                        structured_resp = parser.extract_structured_response(
                            conversation_history=[m.model_dump() for m in payload.messages],
                            assistant_response=full_text,
                            current_config=config_dict,
                            context_data=context
                        )
                    
                    yield json.dumps({"type": "final", "response": structured_resp.model_dump()}) + "\n"
                    break
        except Exception as e:
            yield json.dumps({"type": "error", "content": f"Streaming runtime error: {str(e)}"}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

def recommend_config(payload: CopilotChatPayload) -> CopilotStructuredResponse:
    """
    Non-streaming endpoint that directly returns a structured recommendation 
    and configuration patch.
    """
    config_dict = payload.config.model_dump()

    # 0. Sanitize inputs and check for malicious scripts / prompt injections
    from .validators import sanitize_input_text, detect_malicious_input
    
    # Sanitize config string values to prevent injection
    for key, val in config_dict.items():
        if isinstance(val, str):
            config_dict[key] = sanitize_input_text(val)
            
    is_malicious = False
    malicious_msg = ""
    if payload.messages:
        latest_msg = payload.messages[-1]
        if latest_msg.role == "user":
            latest_msg.content = sanitize_input_text(latest_msg.content)
            mal_flag, mal_desc = detect_malicious_input(latest_msg.content)
            if mal_flag:
                is_malicious = True
                malicious_msg = mal_desc
            
    if is_malicious:
        from .schemas import CopilotStructuredResponse, AIAnalysis, VariantData, ConfigPatch
        block_text = f"Acción denegada por seguridad: {malicious_msg} Por favor, realiza consultas técnicas legítimas sobre diseño 3D o parámetros mecánicos."
        return CopilotStructuredResponse(
            analysis=AIAnalysis(
                text=block_text,
                objective_detected="security_block",
                key_findings="Entrada maliciosa bloqueada.",
                mechanical_justification="El sistema de seguridad previno el procesamiento de este script o instrucción no segura."
            ),
            variants=[
                VariantData(
                    id="security_block",
                    name="Bloqueo de Seguridad",
                    description="Se detectó y bloqueó un intento de inyección o script malicioso.",
                    score=0.0,
                    compression_score=0.0,
                    energy_absorption_score=0.0,
                    stability_score=0.0,
                    printability_score=0.0,
                    risk_level="HIGH",
                    estimated_print_time="0m",
                    estimated_mass="0g",
                    warnings=[malicious_msg],
                    config_patch=ConfigPatch()
                )
            ],
            recommended_variant="security_block",
            ui_actions=[]
        )

    client = OllamaClient()
    latest_query = payload.messages[-1].content if payload.messages else ""
    intent_data = IntentRouter.classify_intent(latest_query)
    intent = intent_data["intent"]

    builder = ContextBuilder()
    context = builder.build_context(latest_query, config_dict, intent)

    config_summary = DesignStateTool.format_design_summary(config_dict)
    system_prompt = PromptBuilder.build_system_prompt(config_summary, context, intent=intent)

    ollama_messages = [{"role": "system", "content": system_prompt}]
    for msg in payload.messages:
        ollama_messages.append({"role": msg.role, "content": msg.content})

    # Call Ollama non-streaming
    ollama_payload = {
        "model": client.select_best_chat_model(),
        "messages": ollama_messages,
        "stream": False,
        "keep_alive": client.keep_alive,
        "options": {"temperature": 0.1, "num_ctx": client.num_ctx}
    }

    url = f"{client.base_url}/api/chat"
    import urllib.request
    req = urllib.request.Request(
        url,
        data=json.dumps(ollama_payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=120.0) as response:
            res_data = json.loads(response.read().decode())
            assistant_text = res_data.get("message", {}).get("content", "")
            
            if intent == "casual_chat":
                from .schemas import CopilotStructuredResponse, AIAnalysis
                return CopilotStructuredResponse(
                    analysis=AIAnalysis(
                        text=assistant_text,
                        objective_detected="casual_chat",
                        key_findings="Conversación casual.",
                        mechanical_justification="No se requieren cambios paramétricos para charla informal."
                    ),
                    variants=[],
                    recommended_variant="",
                    ui_actions=[]
                )
                
            parser = ResponseParser(client)
            return parser.extract_structured_response(
                conversation_history=[m.model_dump() for m in payload.messages],
                assistant_response=assistant_text,
                current_config=config_dict,
                context_data=context
            )
    except Exception as e:
        # Generate error fallback
        parser = ResponseParser(client)
        return parser._generate_fallback(
            message="No se pudo obtener la sugerencia debido a un error de conexión con Ollama.",
            current_config=config_dict,
            context_data=context,
            errors=[str(e)]
        )
