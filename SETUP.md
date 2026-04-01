# NanaSmart — Setup do Login de Teste

## Problema: por que não conseguia criar conta ou fazer login

O repositório tem o backend Django, mas os endpoints `/api/accounts/login/` e `/api/accounts/register/`
estão listados como **"Pendente"** no README — o módulo de autenticação ainda não tem as views completas.

---

## Solução rápida: criar o superusuário manualmente

Com o backend rodando, execute no terminal (dentro do virtualenv ativado):

```bash
python manage.py createsuperuser
```

Quando pedir os dados, use:
- **Username:** `admin`
- **Email:** *(pode deixar vazio, basta pressionar Enter)*
- **Password:** `admin123`

---

## Se o endpoint /api/accounts/login/ não existir ainda

O DRF Token Auth expõe um endpoint padrão que pode ser adicionado em `app/urls.py`:

```python
# app/urls.py — adicione estas linhas
from rest_framework.authtoken import views as auth_views

urlpatterns = [
    # ... suas rotas existentes ...
    path('api/accounts/login/',  auth_views.obtain_auth_token, name='login'),
]
```

Isso faz o endpoint `/api/accounts/login/` aceitar `POST { username, password }` e retornar `{ "token": "..." }`,
que é exatamente o que o frontend NanaSmart espera.

---

## Estrutura de arquivos após a separação

```
NanaSmart/
├── index.html    ← HTML puro, sem CSS nem JS embutido
├── style.css     ← Todo o CSS do projeto
└── app.js        ← Todo o JavaScript / lógica de API
```

## O que foi melhorado no front-end

- **Login:** mensagens de erro mais claras (mostra o campo específico com problema)
- **Registro:** valida tamanho mínimo de senha (6 chars) e exibe erros da API por campo
- **Login de teste:** botão "Preencher automaticamente" com admin/admin123
- **URL da API persistida:** o endereço do backend é salvo no localStorage
- **Enter no registro:** tecla Enter agora também dispara o registro (além do login)
- **Feedback visual:** mensagens de erro ficam em vermelho, sucesso em verde

---

## Credenciais de teste

| Campo    | Valor      |
|----------|------------|
| Usuário  | `admin`    |
| Senha    | `admin123` |

> Após criar o superusuário com `createsuperuser`, essas credenciais funcionarão diretamente no front-end.
