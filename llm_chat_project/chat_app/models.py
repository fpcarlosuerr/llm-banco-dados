from django.db import models

class Pessoa(models.Model): 
    nome = models.CharField(max_length=100) 
    telefone = models.CharField(max_length=20, null=True, blank=True) 
    idade = models.IntegerField(null=True, blank=True)     
    cidade = models.CharField(max_length=100, null=True, blank=True) 
    email = models.EmailField(null=True, blank=True, unique=True) 
    data_cadastro = models.DateField(auto_now_add=True) 
 
    def __str__(self): 
        return f"{self.nome} ({self.id})"
    
class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    
    def __str__(self): 
        return f"{self.nome} ({self.id})"