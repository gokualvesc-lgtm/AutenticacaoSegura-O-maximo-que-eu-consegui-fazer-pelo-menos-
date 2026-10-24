from abc import ABC, abstractmethod
class Validador(ABC):
    def __init__(self):
        self.valor = None

    @abstractmethod
    def validar(self):
        pass

class Usuario(Validador):
    def validar(self):
        valor = self.valor
        quantidade = len(valor)
        if 5 > quantidade or quantidade > 20:
            print(1)
            return False
        
        if any(letra.isupper() for letra in valor):
            print(2)
            return False

        if all(valor.isalnum() or letra == "_" for letra in valor):
            pass
        else:
            print(3)
            return False

        return True


class SenhaValidador(Validador):
    def validar(self):
        valor = self.valor

        if len(valor) < 8:
            return False

        if not any(letra.isupper() for letra in valor):
            return False

        if not any(not letra.isalnum() for letra in valor):
            return False  

        if not any(letra.isdigit() for letra in valor):
            return False
        
        return True

class EmailValidador(Validador):
    def validar(self):
        valor = self.valor

        if not "@" in valor:
            print(1)
            return False

        if any(valor.isalnum() or letra == "_" or letra == "+" or letra == "." for letra in valor):
            pass
        else:
            print(2)
            return False

        if any(letra.isspace() for letra in valor):
            return False


        final = valor.split("@")

        if valor[0] == "@" or valor[0] == ".":
            return False

        if not "." in final[1]:
            print(3)
            return False

        if "@" in final[1]:
            return False

        dominio, tld = final[1].split(".")

        if len(tld) < 3:
            print(4)
            return False
        return True


def validar_dado(tipo, valor):
    tipo.valor = valor
    resposta = tipo.validar()
    if resposta:
        return True
    return False