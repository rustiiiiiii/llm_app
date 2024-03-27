from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import whisper
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from gtts import gTTS
from pyngrok import ngrok
import os
import uuid

class ConversationInput(BaseModel):
    audio_file: Optional[UploadFile] = None
    user_input: Optional[str] = None
    input_method: Optional[str] = None
    output_method: Optional[str] = None
    prompt_template: Optional[str] = None
    conversation_id: str

# Define prompt templates
prompt_templates: Dict[str, ChatPromptTemplate] = {
    'Small talk between two strangers at a bus stand': ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "You are 'Sam', a business analyst on your way to work on a cloudy day. You enjoy a good cup of coffee."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    ),
    'Talking to your co-worker': ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "You are 'John', working in the IT sector. You enjoy reading books and watching movies, but today you're feeling exhausted from work."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    ),
    'Conversing with a person in a professional networking event': ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "You are a professional attending a networking event, engaging in conversations with other professionals."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
    )
}
conversations: Dict[str, LLMChain] = {}

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process/")
async def process_conversation(background_tasks: BackgroundTasks, conversation_input: ConversationInput):
    response_text = ""
    print(conversation_input)

    # Get or create LLMChain for the provided conversation_id
    if conversation_input.conversation_id not in conversations:
        llm = Ollama(model="orca-mini")
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        conversations[conversation_input.conversation_id] = LLMChain(
            llm=llm,
            prompt=prompt_templates[conversation_input.prompt_template],
            verbose=True,
            memory=memory
        )
    conversation = conversations[conversation_input.conversation_id]

    # Process audio input
    if conversation_input.audio_file and conversation_input.input_method == "Speech":
        contents = await conversation_input.audio_file.read()
        audio_path = f"temp_audio_{uuid.uuid4()}.wav"
        with open(audio_path, 'wb') as f:
            f.write(contents)
        conversation_input.user_input = transcribe(audio_path)
        os.remove(audio_path)

    # Generate response based on the provided input
    if conversation_input.user_input:
        if conversation_input.prompt_template in prompt_templates:
            response_text = conversation.run(input=conversation_input.user_input)
        else:
            return JSONResponse(content={"error": "Invalid prompt template"}, status_code=400)
    else:
        print(conversation_input.user_input)
        return JSONResponse(content={"error": "No user input provided"}, status_code=400)

    # Process output
    if conversation_input.output_method == "Speech":
        response_audio_path = await text_to_speech(response_text, background_tasks)
        return FileResponse(response_audio_path, media_type='audio/mp3')
    else:
        return {"response": response_text}

def transcribe(audio_file_path: str) -> str:
    audio = whisper.load_audio(audio_file_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)
    options = whisper.DecodingOptions(fp16=False)
    result = whisper.decode(whisper_model, mel, options)
    return result.text

async def text_to_speech(text: str, background_tasks: BackgroundTasks) -> str:
    audio_path = f"temp_response_{uuid.uuid4()}.mp3"
    tts = gTTS(text=text, lang='en')
    tts.save(audio_path)
    return audio_path

if __name__ == "__main__":
    import uvicorn
    # Start ngrok tunnel
    uvicorn.run(app, host="0.0.0.0", port=8000)