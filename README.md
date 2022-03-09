# Card Game Server

## Como usar

### Requisitos

- Python 3.8+ (tô desenvolvendo só com 3.9 mas tô assumindo que funcione da 3.8 pra cima)
- Python Poetry (https://python-poetry.org/)

### Instalação

- Clonar o repositório:

```
git clone https://github.com/gabriel-milan/card-game-server
```

- Instalar dependências:

```
poetry install
```

### Uso

- Ative o ambiente virtual com as dependências instaladas

```
poetry shell
```

- Primeiramente, hospede o servidor fazendo

```
python run_server.py
```

- Depois, em outro(s) terminal(is), abra quantos clientes quiser com

```
python client.py
```

- O que é possível fazer:
  - Criar (caso nenhuma exista) ou entrar em uma sala
  - Mandar uma mensagem
  - Sair da sala (opcional)

**Obs:** existem bugs 😅
