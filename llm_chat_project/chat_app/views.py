from django.shortcuts import render 
from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt # Para simplificar, desabilitar CSRF para esta view AJAX 
import json 
# Certifique-se de que o import está correto (utils.py ou api.py) 
from .utils import get_gemini_response, get_llm_prompt, get_openai_response, execute_orm_query 
# Se você nomeou o arquivo como api.py, use: 
# from .api import get_llm_prompt, get_openai_response, execute_orm_query 
 
def chat_page(request): 
    return render(request, 'chat_app/chat.html') 
 
@csrf_exempt # Apenas para desenvolvimento/protótipo. Use CSRF tokens em produção. 
def process_query(request): 
    if request.method == 'POST': 
        try: 
            data = json.loads(request.body) 
            user_message = data.get('message') 
 
            if not user_message: 
                return JsonResponse({'error': 'Mensagem vazia.'}, status=400) 
 
            # 1. Gerar prompt para o LLM 
            prompt = get_llm_prompt(user_message) 
             
            # 2. Obter query ORM do LLM 
            #orm_query_string = get_openai_response(prompt) 
            orm_query_string = get_gemini_response(prompt) 
            if not orm_query_string or "Erro:" in str(orm_query_string): # Adicionado str() para segurança 
                error_message = orm_query_string if isinstance(orm_query_string, str) else 'Falha ao gerar query ORM.' 
                return JsonResponse({'error': error_message, 'orm_query': orm_query_string if isinstance(orm_query_string, str) else "N/A"}) 
 
            # 3. Executar a query ORM (com os devidos cuidados) 
            query_result = execute_orm_query(orm_query_string) 
             
            # Verificar se o resultado da query é um erro 
            if isinstance(query_result, str) and query_result.startswith("Erro:"): 
                 return JsonResponse({'user_message': user_message, 'orm_query': orm_query_string, 'error': query_result}) 
 
            return JsonResponse({'user_message': user_message, 'orm_query': orm_query_string, 'result': query_result}) 
        except json.JSONDecodeError: 
            return JsonResponse({'error': 'JSON inválido.'}, status=400) 
        except Exception as e: 
            # Para depuração, pode ser útil logar o erro completo 
            # import traceback 
            # print(traceback.format_exc()) 
            return JsonResponse({'error': f'Erro interno do servidor: {str(e)}'}, status=500) 
    return JsonResponse({'error': 'Método não permitido.'}, status=405) 