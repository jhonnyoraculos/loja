# ORÁCULOS 3D Print - Loja Streamlit

App em Streamlit para vender impressões 3D com catálogo, carrinho, desconto progressivo, registro de pedidos no Neon e finalização pelo WhatsApp.

## Rodar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Configurar Neon

1. Crie um projeto no Neon e copie a connection string PostgreSQL.
2. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`.
3. Preencha `DATABASE_URL` com a connection string do Neon.
4. Ajuste `WHATSAPP_PHONE` se quiser trocar o número de destino.

O app cria automaticamente as tabelas `products`, `orders` e `order_items` no primeiro acesso. O catálogo atual é sincronizado na tabela `products`, e cada pedido finalizado fica salvo em `orders` e `order_items`.

## WhatsApp

O número pode ser salvo como `37998726994` ou já completo com DDI. Se ele tiver 11 dígitos, o app adiciona `55` automaticamente antes de gerar o link do WhatsApp.
