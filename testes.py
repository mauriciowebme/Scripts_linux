import random

def generate_password(length=16):
    ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
    digits = '0123456789'
    caracteres_especiais = "!@#$%_"  # Caracteres especiais permitidos
    
    # Define os caracteres permitidos: letras, dígitos e símbolos
    characters = ascii_uppercase + ascii_lowercase + digits + caracteres_especiais
    
    # Garante pelo menos um caractere de cada tipo (opcional)
    password = (
        random.choice(ascii_uppercase) +  # Pelo menos uma letra maiúscula
        random.choice(ascii_lowercase) +  # Pelo menos uma letra minúscula
        random.choice(digits) +           # Pelo menos um número
        random.choice(caracteres_especiais)      # Pelo menos um símbolo
    )
    
    # Completa a senha até o comprimento desejado
    password += ''.join(random.choice(characters) for _ in range(length - 4))
    
    # Embaralha os caracteres da senha para evitar padrões previsíveis
    password = ''.join(random.sample(password, len(password)))
    return password

# Gera e imprime a senha
replication_password = generate_password()
print(replication_password)
