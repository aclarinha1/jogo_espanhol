from django.db import models

class Pergunta(models.Model):
    
    ALTERNATIVAS = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    
    NIVEIS = [
        ('F', 'Fácil'),
        ('M', 'Médio'),
        ('D', 'Difícil'),
    ]

    texto = models.CharField(max_length=200)
    
    resposta_correta = models.CharField(
        max_length=1, 
        choices=ALTERNATIVAS )
    
    imagem = models.ImageField(upload_to='perguntas/', blank=True, null=True)

    opcao_a = models.CharField(max_length=100)
    opcao_b = models.CharField(max_length=100)
    opcao_c = models.CharField(max_length=100)
    opcao_d = models.CharField(max_length=100, blank=True)

    nivel = models.CharField(
        max_length=1,
        choices=NIVEIS,
        default='F'
    )

    def __str__(self):
        return self.texto
