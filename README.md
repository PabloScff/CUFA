# Creamshaper – CUFA (MVP) — Projeto de Software, Experiência Prática 2

Monólito em camadas (Python 3.12 · FastAPI · SQLAlchemy · Pydantic · Pytest · PostgreSQL).

```
app/apresentacao  → telas (Jinja2), rotas, autenticação por perfil
app/dominio       → regra de duplicidade por ciclo (sem banco, sem FastAPI)
app/persistencia  → SQLAlchemy ORM + repositório
```

## Telas (slides 19–20)
| Tela | Rota | Requisitos |
|---|---|---|
| 1 Login | `/login` | RNF01 (JWT + bcrypt), RNF02, RTAC01 |
| 2 Atendimento (cadastro + entrega) | `/operacao/atendimento` | RF01, RF02, RF03, RTAC01 |
| 3 Resultado (sucesso / bloqueio) | resposta do POST da Tela 2 | RF02, RTAC01 (cor + ícone + texto + vibração) |

RF04 (relatórios) está fora do protótipo, como definido no slide 19.

## Rodar
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # edite JWT_SECRET
SEED_SENHA='uma-senha-forte' python seed.py            # cria voluntario.cufa01 e coordenador.cufa01
uvicorn app.main:app --reload                          # http://127.0.0.1:8000
pytest                                                 # domínio + telas + segurança
python scripts/gerar_capturas.py                       # regenera os prints em capturas/
```
Para PostgreSQL (Supabase/Neon ou Docker), troque `DATABASE_URL` no `.env`.

## Decisões a conhecer
- **CPF:** validação de *formato* (RF01), não do dígito verificador — o CPF do roteiro (123.456.789-00) é fictício e inválido pelo dígito.
- **CPF já cadastrado:** não cria cópia. Se não há entrega no ciclo, registra a entrega; se há, **bloqueia** (Tela 3).
- **Logo:** `static/logo-cufa.svg` é um marcador; troque pelo arquivo oficial da CUFA.
- **Logout:** a lista de tokens revogados fica em memória (1 instância). Com várias instâncias, use Redis ou tabela.
