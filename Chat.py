import os
import json
from pathlib import Path
#import openai
from anthropic import Anthropic, AsyncAnthropic
#from openrouter import OpenRouter 
#import google.generativeai as genai

# Map of model shortcodes to full model names
MODELS = {
    # GPT by OpenAI
    'gm': 'gpt-4o-mini',
    'g': 'gpt-4o-2024-11-20',
    
    # o1 by OpenAI  
    'om': 'o1-mini',
    'o': 'o1',

    # Claude by Anthropic
    'cm': 'claude-3-5-haiku-20241022',
    'C': 'claude-3-5-sonnet-latest', 
    #'C': 'claude-3-5-sonnet-20241022', 
    'c': 'claude-3-5-sonnet-20240620',

    'd': 'deepseek-chat',

    # Llama by Meta
    'lm': 'meta-llama/llama-3.2-8b-instruct',
    'l': 'meta-llama/llama-3.3-70b-instruct', 
    'L': 'meta-llama/llama-3.2-405b-instruct',

    # Gemini by Google
    'i': 'gemini-2.0-flash-exp',
    'I': 'gemini-exp-1206'
}

# def openai_chat(client_class, use_model):
    # messages = []
    # extend_function = None
    
    # async def ask(user_message, system=None, model=None, temperature=0.0, 
                 # max_tokens=8192, stream=True, shorten=lambda x: x, 
                 # extend=None, predict=None):
        # if user_message is None:
            # return {'messages': messages}
            
        # reasoning_effort = None
        # model = MODELS.get(model, model or use_model)
        # client = client_class(api_key=get_token(client_class.__name__.lower()))
        
        # is_o1 = model.startswith("o1")
        
        # max_completion_tokens = None
        # if is_o1:
            # stream = False
            # temperature = 1
            # max_completion_tokens = max_tokens
            # max_tokens = None
            # reasoning_effort = "high"
            
        # if len(messages) == 0 and system:
            # if is_o1:
                # messages.append({"role": "user", "content": system})
            # else:
                # messages.append({"role": "system", "content": system})
                
        # extended_message = extend_function(user_message) if extend_function else user_message
        # nonlocal extend_function
        # extend_function = extend
        
        # messages_copy = messages + [{"role": "user", "content": extended_message}]
        # messages.append({"role": "user", "content": user_message})
        
        # prediction = {"type": "content", "content": predict} if predict and "o1" not in model else None
        
        # params = {
            # "messages": messages_copy,
            # "model": model,
            # "temperature": temperature,
            # "max_tokens": max_tokens,
            # "max_completion_tokens": max_completion_tokens,
            # "reasoning_effort": reasoning_effort,
            # "stream": stream,
            # "prediction": prediction
        # }
        
        # result = ""
        # response = await client.chat.completions.create(**params)
        
        # if stream:
            # async for chunk in response:
                # text = chunk.choices[0].delta.content or ""
                # print(text, end="", flush=True)
                # result += text
        # else:
            # text = response.choices[0].message.content or ""
            # print(text, end="", flush=True)
            # result = text
            
        # messages.append({"role": "assistant", "content": await shorten(result)})
        # return result
        
    # return ask


def anthropic_chat(client_class, MODEL):
    messages = []
    
    async def ask(user_message, system=None, model=None, temperature=0.0,
                 max_tokens=8192, stream=True, system_cacheable=False,
                 shorten=lambda x: x, extend=None):
        if user_message is None:
            return {'messages': messages}
            
        model = model or MODEL
        model = MODELS.get(model, model)
        client = client_class(
            api_key=get_token(client_class.__name__.lower()),
            default_headers={
                "anthropic-beta": "prompt-caching-2024-07-31"
            }
        )
        
        extended_message = extend(user_message) if extend else user_message
        messages_copy = messages + [{"role": "user", "content": extended_message}]
        messages.append({"role": "user", "content": user_message})
        
        cached_system = [{"type": "text", "text": system}] #, "cache_control": {"type": "ephemeral"}}]
        prompt_system = cached_system if system_cacheable else system
        
        params = {
            "system": prompt_system,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            #"stream": stream
        }
        
        result = ""
        response = client.messages.create(**params, messages=messages_copy)
        for message in response.content:
            if stream and hasattr(message, 'text'):
                print(message.text, end="", flush=True)
                result += message.text
            else:
                print("Skipped2 ", repr(message))
            
        messages.append({"role": "assistant", "content": shorten(result)})
        return result
        
    return ask

# def gemini_chat(client_class):
    # messages = []
    # extend_function = None
    
    # async def ask(user_message, system=None, model=None, temperature=0.0,
                 # max_tokens=8192, stream=True, shorten=lambda x: x, extend=None):
        # if user_message is None:
            # return {'messages': messages}
            
        # model = MODELS.get(model, model)
        # client = client_class(get_token(client_class.__name__.lower()))
        
        # generation_config = {
            # "maxOutputTokens": max_tokens,
            # "temperature": temperature
        # }
        
        # safety_settings = [
            # {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            # {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            # {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            # {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        # ]
        
        # extended_message = extend_function(user_message) if extend_function else user_message
        # nonlocal extend_function
        # extend_function = extend
        
        # messages_copy = messages + [{"role": "user", "parts": [{"text": extended_message}]}]
        # messages.append({"role": "user", "parts": [{"text": user_message}]})
        
        # chat = client.get_generative_model(
            # model=model,
            # generation_config=generation_config
        # ).start_chat(
            # history=messages_copy,
            # safety_settings=safety_settings
        # )
        
        # result = ""
        # if stream:
            # response = await chat.send_message_stream(extended_message)
            # async for chunk in response.stream:
                # text = chunk.text()
                # print(text, end="", flush=True)
                # result += text
        # else:
            # response = await chat.send_message(extended_message)
            # result = (await response.response).text()
            
        # messages.append({"role": "model", "parts": [{"text": await shorten(result)}]})
        # return result
        
    # return ask

def get_token(vendor):
    token_path = Path.home() / '.config' / f'{vendor}.token'
    try:
        return token_path.read_text().strip()
    except Exception as e:
        print(f"Error reading {vendor}.token file:", str(e))
        exit(1)

def token_count(input_text):
    # Note: This is a simplified version since Python doesn't have the exact same tokenizer
    return len(input_text.split())

def chat(model):
    model = MODELS.get(model, model)
    if model.startswith('gpt'):
        return openai_chat(openai.OpenAI, model)
    elif model.startswith('o1'):
        return openai_chat(openai.OpenAI, model)
    elif model.startswith('chatgpt'):
        return openai_chat(openai.OpenAI, model)
    elif model.startswith('deepseek'):
        return openai_chat(openai.OpenAI, model)
    elif model.startswith('claude'):
        return anthropic_chat(Anthropic, model)
    elif model.startswith('meta'):
        return openai_chat(OpenRouter, model)
    elif model.startswith('gemini'):
        return gemini_chat(genai, model)
    else:
        raise ValueError(f"Unsupported model: {model}")
