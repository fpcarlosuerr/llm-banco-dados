import openai 
from django.conf import settings 
from django.db.models import Q 
from .models import Pessoa # Importante para o escopo do eval 
from google import genai
 
def get_pessoa_model_fields_info(): 
    """Retorna um dicionário com nomes de campos e tipos simplificados para o modelo Pessoa.""" 
    fields_info = {} 
    # Campos relevantes para consulta em linguagem natural 
    relevant_field_names = ['nome', 'telefone', 'idade', 'cidade', 'email', 'data_cadastro'] 
    for field in Pessoa._meta.get_fields(): 
        if field.concrete and field.name in relevant_field_names: 
            field_type_name = field.get_internal_type() 
            if 'CharField' in field_type_name or 'TextField' in field_type_name: 
                simplified_type = 'String' 
            elif 'IntegerField' in field_type_name: 
                simplified_type = 'Integer' 
            elif 'EmailField' in field_type_name: 
                simplified_type = 'Email (String)' 
            elif 'DateField' in field_type_name: 
                simplified_type = 'Date (YYYY-MM-DD)' 
            elif 'BooleanField' in field_type_name: 
                simplified_type = 'Boolean' 
            elif 'FloatField' in field_type_name or 'DecimalField' in field_type_name: 
                simplified_type = 'Number' 
            else: 
                simplified_type = field_type_name 
            fields_info[field.name] = simplified_type 
    return fields_info 
 
def get_llm_prompt(user_query): 
    model_fields = get_pessoa_model_fields_info() 
    fields_description = "\n".join([f"- {name} ({field_type})" for name, field_type in 
    model_fields.items()]) 
    return f""" 
    Você é um assistente de IA que traduz consultas em linguagem natural para queries 
    Django ORM para um modelo chamado 'Pessoa'. 
    
    O modelo 'Pessoa' possui os seguintes campos: 
    {fields_description} 
    Traduza a seguinte consulta em linguagem natural para uma única linha de código Python 
    representando uma query Django ORM. 
    
    A query DEVE começar com "Pessoa.objects.". 
    Você pode usar filtros (filter, exclude), lookups de campo (ex: __exact, __iexact, 
    __contains, __icontains, __gt, __gte, __lt, __lte, __in, __startswith, __istartswith, 
    __endswith, __iendswith, __isnull), objetos Q para lookups complexos, ordenação 
    (order_by) e fatiamento (slicing). 
    
    Você também pode usar .count() para contagem, .exists() para verificar existência, e 
    .values() ou .values_list() para selecionar campos específicos. 
    
    NÃO use .delete(), .update(), .create(), .save(), .raw(), .extra(), .annotate() (exceto para 
    agregações simples como Count), ou .aggregate() (exceto para Count). 
    Retorne APENAS o código Python para a query ORM. Não inclua explicações, markdown, 
    ou qualquer outro texto. 
    
    Exemplo 1: 
    Linguagem Natural: "Quais são todas as pessoas?" 
    Query ORM: Pessoa.objects.all() 
    
    Exemplo 2: 
    Linguagem Natural: "Encontre pessoas com mais de 30 anos." 
    Query ORM: Pessoa.objects.filter(idade__gt=30) 
    
    Exemplo 3: 
    Linguagem Natural: "Mostre as pessoas de São Paulo." 
    Query ORM: Pessoa.objects.filter(cidade='São Paulo') 
    
    Exemplo 4: 
    Linguagem Natural: "Quantas pessoas se chamam Maria?" 
    Query ORM: Pessoa.objects.filter(nome='Maria').count() 
    
    Exemplo 5: 
    Linguagem Natural: "Liste os nomes e emails das pessoas de Curitiba com menos de 25 
    anos, ordenados por nome." 
    Query ORM: Pessoa.objects.filter(cidade='Curitiba',idade__lt=25).order_by('nome').values('nome', 'email') 
    
    Exemplo 6: 
    Linguagem Natural: "Existem pessoas chamadas João ou Pedro?" 
    Query ORM: Pessoa.objects.filter(Q(nome='João') | Q(nome='Pedro')).exists() 
    
    Consulta em Linguagem Natural para traduzir: 
    
    "{user_query}" 
    
    Query ORM: 
    """ 
 
def get_gemini_response(prompt_text):
    try:         
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        ) # Para GEMINI >= 1.0.0 
        # response = openai.ChatCompletion.create( 
        response = client.models.generate_content( # Certifique-se de que esta é a chamada correta para sua versão da lib GEMINI 
            model="gemini-2.0-flash",
            contents=prompt_text
            #temperature=0.2, # Baixa temperatura para respostas mais determinísticas 
            #max_tokens=150 
        ) 
        orm_query_string = response.text
        # Adicionar uma verificação simples para garantir que é uma linha de código 
        if '\n' in orm_query_string or not orm_query_string.startswith("Pessoa.objects."): 
            # Tenta pegar a primeira linha que parece ser a query 
            lines = [line for line in orm_query_string.split('\n') if line.strip().startswith("Pessoa.objects.")] 
            if lines: 
                orm_query_string = lines[0].strip() 
            else: 
                raise ValueError("LLM não retornou uma query ORM válida no formato esperado.") 
        return orm_query_string 
    except Exception as e: 
        print(f"Erro na API GeminiAI: {e}") 
        return None # Ou uma string de erro específica
 
def get_openai_response(prompt_text): 
    try:         
        client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY,
        ) # Para openai >= 1.0.0 
        # Para versões mais antigas de openai (ex: 0.28), seria: 
        # response = openai.ChatCompletion.create( 
        response = client.chat.completions.create( # Certifique-se de que esta é a chamada correta para sua versão da lib openai 
            model="gpt-4", # Ou "gpt-3.5-turbo" ou outro modelo disponível 
            messages=[ 
                {"role": "system", "content": "Você é um tradutor de linguagem natural para Django ORM."}, 
                {"role": "user", "content": prompt_text} 
            ], 
            temperature=0.2, # Baixa temperatura para respostas mais determinísticas 
            max_tokens=150 
        ) 
        orm_query_string = response.choices[0].message.content.strip() 
        # Adicionar uma verificação simples para garantir que é uma linha de código 
        if '\n' in orm_query_string or not orm_query_string.startswith("Pessoa.objects."): 
            # Tenta pegar a primeira linha que parece ser a query 
            lines = [line for line in orm_query_string.split('\n') if line.strip().startswith("Pessoa.objects.")] 
            if lines: 
                orm_query_string = lines[0].strip() 
            else: 
                raise ValueError("LLM não retornou uma query ORM válida no formato esperado.") 
        return orm_query_string 
    except Exception as e: 
        print(f"Erro na API OpenAI: {e}") 
        return None # Ou uma string de erro específica 
 
def execute_orm_query(query_str): 
    """ 
    Executa uma string de query ORM. 
    ATENÇÃO: Usar eval() é arriscado. Esta função é um protótipo e deve ser usada 
    com extrema cautela. A engenharia de prompt é crucial para mitigar riscos. 
    """ 
    if not query_str.strip().startswith("Pessoa.objects."): 
        return "Erro: Query inválida. Deve começar com 'Pessoa.objects.'." 
 
    try: 
        # Escopo limitado para eval. Apenas Pessoa e Q são permitidos do nosso código. 
        # Builtins são limitados implicitamente pelo que o ORM do Django usa. 
        allowed_globals = {"__builtins__": globals()['__builtins__'], "Pessoa": Pessoa, "Q": Q} 
         
        raw_result = eval(query_str, allowed_globals, {"Pessoa": Pessoa, "Q": Q}) # O terceiro argumento (locals) pode ser combinado com globals ou ser um dict separado 
 
        if isinstance(raw_result, (int, float, bool)) or raw_result is None: 
            return raw_result 
        elif hasattr(raw_result, 'all'): # É um QuerySet 
            # Se for um QuerySet de instâncias de modelo, precisamos serializá-las. 
            # Se for .values() ou .values_list(), já será uma lista de dicts/tuples. 
            if raw_result.exists() and isinstance(raw_result.first(), Pessoa): 
                 return [f"{p.nome} (Idade: {p.idade}, Cidade: {p.cidade}, Email: {p.email})" for p in raw_result] 
            return list(raw_result)  
        elif isinstance(raw_result, list): 
            return raw_result 
        # Se for uma única instância do modelo 
        elif isinstance(raw_result, Pessoa): 
            return f"{raw_result.nome} (Idade: {raw_result.idade}, Cidade: {raw_result.cidade}, Email: {raw_result.email})" 
        return str(raw_result) # Fallback 
    except Exception as e: 
        return f"Erro ao executar query: {str(e)}" 