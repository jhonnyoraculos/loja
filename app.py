from __future__ import annotations

import copy
import base64
import hashlib
import hmac
import mimetypes
import os
import random
import re
import secrets as py_secrets
import urllib.parse
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import streamlit as st

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Json
except ModuleNotFoundError:
    psycopg = None
    dict_row = None
    Json = None

try:
    from zoneinfo import ZoneInfo
except ModuleNotFoundError:
    ZoneInfo = None


BASE_DIR = Path(__file__).parent
BRAND_NAME = "ORÁCULOS 3D Print"
DEFAULT_WHATSAPP_PHONE = "37998726994"
DELIVERY_NOTE = "Entrega grátis em: São Gonçalo do Pará - MG"
PROMO_NOTE = "Desconto progressivo: 2 itens = 2%, 3 itens = 5%, 6 itens = 7%"
DISCOUNT_TIERS = [
    (2, Decimal("0.02")),
    (3, Decimal("0.05")),
    (6, Decimal("0.07")),
]


def svg_data_uri(svg: str) -> str:
    return f"data:image/svg+xml;utf8,{urllib.parse.quote(svg)}"


PERSONALIZED_PLACEHOLDER = svg_data_uri(
    """
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="640" viewBox="0 0 900 640">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#fff159"/>
          <stop offset="100%" stop-color="#ffd53f"/>
        </linearGradient>
        <linearGradient id="plate" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.95"/>
          <stop offset="100%" stop-color="#fff9d8" stop-opacity="0.90"/>
        </linearGradient>
      </defs>
      <rect width="900" height="640" rx="42" fill="url(#bg)"/>
      <circle cx="130" cy="110" r="70" fill="#ffffff" opacity="0.30"/>
      <circle cx="760" cy="530" r="145" fill="#ffffff" opacity="0.25"/>
      <path d="M260 390h380l42 52H218l42-52Z" fill="#1d2433" opacity="0.18"/>
      <rect x="285" y="172" width="330" height="225" rx="28" fill="url(#plate)"/>
      <rect x="322" y="210" width="256" height="150" rx="18" fill="#1d2433" opacity="0.10"/>
      <path d="M382 332h136l34 44H348l34-44Z" fill="#0b1021" opacity="0.72"/>
      <circle cx="450" cy="286" r="58" fill="#3483fa" opacity="0.95"/>
      <path d="M418 286h64M450 254v64" stroke="#fff" stroke-width="18" stroke-linecap="round"/>
      <text x="450" y="470" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="48" font-weight="800" fill="#333333">Personalizados</text>
      <text x="450" y="512" text-anchor="middle" font-family="Trebuchet MS, Verdana, sans-serif" font-size="24" font-weight="700" fill="#555555">sob medida</text>
    </svg>
    """
)

DEFAULT_PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "personalizados",
        "name": "Objetos Personalizados",
        "price": None,
        "compare_at_price": None,
        "price_text": "A combinar",
        "description": "Você escolhe o modelo em outro lugar e me envia para eu produzir.",
        "description_long": (
            "Produção sob medida: você escolhe o objeto, me envia a referência "
            "e combinamos o formato final e o valor."
        ),
        "category": "Personalizados",
        "customizable": True,
        "pinned": True,
        "featured": True,
        "featured_rank": 0,
        "specs": {"dimensoes": "A combinar", "tempo": "A combinar"},
        "colors": [],
        "images": [PERSONALIZED_PLACEHOLDER],
        "image": PERSONALIZED_PLACEHOLDER,
    },
    {
        "id": "sup-xbox",
        "name": "Suporte de Controle de Xbox",
        "price": Decimal("29.90"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Suporte firme para controle de Xbox com acabamento clean.",
        "description_long": (
            "Suporte 3D para controle de Xbox, com encaixe seguro e base estável "
            "para deixar o setup organizado."
        ),
        "category": "Suportes",
        "customizable": False,
        "pinned": False,
        "featured": True,
        "featured_rank": 1,
        "specs": {"dimensoes": "A confirmar", "tempo": "2h 30m"},
        "colors": [],
        "images": [
            "SUPORTE XBOX/1.jpeg",
            "SUPORTE XBOX/2.jpeg",
            "SUPORTE XBOX/3.jpeg",
            "SUPORTE XBOX/4.jpeg",
        ],
        "image": "SUPORTE XBOX/1.jpeg",
    },
    {
        "id": "placa-f1",
        "name": "Placa Decorativa F1",
        "price": Decimal("23.90"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Placa decorativa inspirada na Fórmula 1.",
        "description_long": (
            "Placa decorativa da Fórmula 1 com base de apoio. Ideal para mesas, "
            "prateleiras e setups."
        ),
        "category": "Decoração",
        "customizable": False,
        "pinned": False,
        "featured": True,
        "featured_rank": 4,
        "specs": {"dimensoes": "16 x 5 x 8 cm (aprox.)", "tempo": "A confirmar"},
        "colors": [],
        "images": ["PLACA DECORATIVA F1/1.jpeg"],
        "image": "PLACA DECORATIVA F1/1.jpeg",
    },
    {
        "id": "sup-controle",
        "name": "Suporte para Controles Remotos",
        "price": Decimal("14.90"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Suporte com 3 compartimentos para controles.",
        "description_long": (
            "Suporte para controles remotos com 3 compartimentos. Disponível nas "
            "cores branca e preta."
        ),
        "category": "Suportes",
        "customizable": False,
        "pinned": False,
        "featured": True,
        "featured_rank": 5,
        "specs": {"dimensoes": "16 x 5 x 8 cm (aprox.)", "tempo": "A confirmar"},
        "colors": ["Preto", "Branco"],
        "images": [
            "SUPORTE CONTROLE/0.webp",
            "SUPORTE CONTROLE/1.jpg",
            "SUPORTE CONTROLE/2.jpg",
            "SUPORTE CONTROLE/3.jpg",
        ],
        "image": "SUPORTE CONTROLE/0.webp",
    },
    {
        "id": "sup-gatinho",
        "name": "Suporte de Celular Gatinho",
        "price": Decimal("7.50"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Suporte de celular com base em formato de gatinho.",
        "description_long": (
            "Suporte decorativo para celular em formato de gatinho. Ideal para "
            "mesas e criados-mudos."
        ),
        "category": "Suportes",
        "customizable": False,
        "pinned": False,
        "featured": True,
        "featured_rank": 3,
        "specs": {"dimensoes": "A confirmar", "tempo": "2h"},
        "colors": [],
        "images": [
            "SUPORTE CELULAR GATINHO/1.webp",
            "SUPORTE CELULAR GATINHO/2.webp",
            "SUPORTE CELULAR GATINHO/3.webp",
            "SUPORTE CELULAR GATINHO/4.webp",
        ],
        "image": "SUPORTE CELULAR GATINHO/1.webp",
    },
    {
        "id": "sup-moderno",
        "name": "Suporte Moderno para Celular",
        "price": Decimal("13.90"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Suporte moderno com design ondulado.",
        "description_long": (
            "Suporte moderno para celular com design ondulado, pensado para "
            "destaque na decoração."
        ),
        "category": "Suportes",
        "customizable": False,
        "pinned": False,
        "featured": True,
        "featured_rank": 6,
        "specs": {"dimensoes": "A confirmar", "tempo": "3h 30m"},
        "colors": [],
        "images": [
            "SUPORTE MODERNO CELULAR/1.webp",
            "SUPORTE MODERNO CELULAR/2.webp",
            "SUPORTE MODERNO CELULAR/3.webp",
            "SUPORTE MODERNO CELULAR/4.webp",
        ],
        "image": "SUPORTE MODERNO CELULAR/1.webp",
    },
    {
        "id": "sup-elegante",
        "name": "Suporte Elegante para Celular",
        "price": Decimal("10.50"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Suporte elegante com base ventilada.",
        "description_long": (
            "Suporte elegante para celular com base ventilada e apoio firme. "
            "Ideal para uso horizontal."
        ),
        "category": "Suportes",
        "customizable": False,
        "pinned": False,
        "featured": False,
        "featured_rank": None,
        "specs": {"dimensoes": "A confirmar", "tempo": "3h 30m"},
        "colors": [],
        "images": [
            "SUPORTE PARA CELULAR ELEGANTE/1.webp",
            "SUPORTE PARA CELULAR ELEGANTE/2.webp",
            "SUPORTE PARA CELULAR ELEGANTE/3.webp",
            "SUPORTE PARA CELULAR ELEGANTE/4.webp",
            "SUPORTE PARA CELULAR ELEGANTE/5.webp",
            "SUPORTE PARA CELULAR ELEGANTE/6.webp",
        ],
        "image": "SUPORTE PARA CELULAR ELEGANTE/1.webp",
    },
    {
        "id": "sup-ps5",
        "name": "Suporte de Controle de PS5",
        "price": Decimal("29.90"),
        "compare_at_price": None,
        "price_text": None,
        "description": "Suporte firme para controle de PS5 com acabamento clean.",
        "description_long": (
            "Suporte 3D para controle de PS5, com encaixe seguro e base estável "
            "para deixar o setup organizado."
        ),
        "category": "Suportes",
        "customizable": False,
        "pinned": False,
        "featured": True,
        "featured_rank": 2,
        "specs": {"dimensoes": "A confirmar", "tempo": "2h 30m"},
        "colors": [],
        "images": [
            "SUPORTE PS5/1.jpeg",
            "SUPORTE PS5/2.jpeg",
            "SUPORTE PS5/3.jpeg",
            "SUPORTE PS5/4.jpeg",
            "SUPORTE PS5/5.jpeg",
        ],
        "image": "SUPORTE PS5/1.jpeg",
    },
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(12, 2),
    compare_at_price NUMERIC(12, 2),
    price_text TEXT,
    description TEXT NOT NULL,
    description_long TEXT NOT NULL,
    category TEXT NOT NULL,
    customizable BOOLEAN NOT NULL DEFAULT FALSE,
    pinned BOOLEAN NOT NULL DEFAULT FALSE,
    featured BOOLEAN NOT NULL DEFAULT FALSE,
    featured_rank INTEGER,
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    colors JSONB NOT NULL DEFAULT '[]'::jsonb,
    images JSONB NOT NULL DEFAULT '[]'::jsonb,
    image TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    notes TEXT,
    item_count INTEGER NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    discount_rate NUMERIC(5, 4) NOT NULL,
    discount_amount NUMERIC(12, 2) NOT NULL,
    total NUMERIC(12, 2) NOT NULL,
    has_flexible_price BOOLEAN NOT NULL DEFAULT FALSE,
    whatsapp_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    unit_price NUMERIC(12, 2),
    price_text TEXT,
    color TEXT,
    qty INTEGER NOT NULL,
    subtotal NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS admin_users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def get_setting(name: str, default: str | None = None) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.environ.get(name) or default


def normalize_database_url(database_url: str) -> str:
    parsed = urllib.parse.urlparse(database_url)
    if not parsed.query:
        return urllib.parse.urlunparse(parsed._replace(query="sslmode=require"))
    query = urllib.parse.parse_qs(parsed.query)
    if "sslmode" in query:
        return database_url
    return urllib.parse.urlunparse(parsed._replace(query=f"{parsed.query}&sslmode=require"))


def normalize_whatsapp_phone(phone: str) -> str:
    digits = "".join(char for char in str(phone) if char.isdigit())
    if len(digits) == 11 and not digits.startswith("55"):
        return f"55{digits}"
    return digits


def to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_money(value: Decimal | int | float | str | None) -> str:
    decimal_value = to_decimal(value)
    if decimal_value is None:
        return "A combinar"
    text = f"{decimal_value:,.2f}"
    text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {text}"


def format_product_price(product: dict[str, Any]) -> str:
    return product.get("price_text") or format_money(product.get("price"))


def get_promotion_percent(product: dict[str, Any]) -> int | None:
    price = to_decimal(product.get("price"))
    compare_at_price = to_decimal(product.get("compare_at_price"))
    if price is None or compare_at_price is None or compare_at_price <= price:
        return None
    percent = ((compare_at_price - price) / compare_at_price * Decimal("100")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(percent)


def is_promotional_product(product: dict[str, Any]) -> bool:
    return get_promotion_percent(product) is not None


def render_price_html(product: dict[str, Any]) -> str:
    percent = get_promotion_percent(product)
    if percent is None:
        return f'<div class="price-line">{format_product_price(product)}</div>'
    return (
        '<div class="price-stack">'
        f'<span class="old-price">{format_money(product.get("compare_at_price"))}</span>'
        '<div class="promo-price-row">'
        f'<span class="price-line promo">{format_money(product.get("price"))}</span>'
        f'<span class="discount-tag">-{percent}%</span>'
        '</div>'
        '</div>'
    )


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or f"produto-{random.randint(1000, 9999)}"


def parse_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or py_secrets.token_urlsafe(18)
    iterations = 260_000
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${base64.b64encode(digest).decode('ascii')}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, digest = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return hmac.compare_digest(base64.b64encode(candidate).decode("ascii"), digest)
    except Exception:
        return False


def get_now() -> datetime:
    if ZoneInfo is None:
        return datetime.now()
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def generate_order_id(now: datetime) -> str:
    rand = random.randint(100, 999)
    return f"ORAK-{now:%Y%m%d}-{now:%H%M}-{rand}"


def image_source(image_path: str | None) -> str | None:
    if not image_path:
        return None
    if image_path.startswith(("http://", "https://", "data:")):
        return image_path
    path = BASE_DIR / image_path
    if path.exists():
        return str(path)
    logo = BASE_DIR / "IMAGEM.jpeg"
    return str(logo) if logo.exists() else None


def uploaded_image_to_data_uri(uploaded_file: Any) -> str | None:
    if uploaded_file is None:
        return None
    mime_type = uploaded_file.type or "image/jpeg"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


@st.cache_data(show_spinner=False)
def image_data_uri(image_path: str) -> str | None:
    source = image_source(image_path)
    if not source or source.startswith(("http://", "https://", "data:")):
        return source
    path = Path(source)
    if not path.exists():
        return None
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


@st.cache_resource(show_spinner=False)
def initialize_database(database_url: str) -> bool:
    if psycopg is None or Json is None:
        raise RuntimeError("Instale as dependências com: pip install -r requirements.txt")

    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS compare_at_price NUMERIC(12, 2)")
            cur.execute("SELECT COUNT(*) AS total FROM products")
            product_count = cur.fetchone()["total"]
            if product_count == 0:
                for product in DEFAULT_PRODUCTS:
                    cur.execute(
                        """
                        INSERT INTO products (
                            id, name, price, compare_at_price, price_text, description, description_long,
                            category, customizable, pinned, featured, featured_rank,
                            specs, colors, images, image, active, updated_at
                        )
                        VALUES (
                            %(id)s, %(name)s, %(price)s, %(compare_at_price)s, %(price_text)s,
                            %(description)s, %(description_long)s, %(category)s,
                            %(customizable)s, %(pinned)s, %(featured)s,
                            %(featured_rank)s, %(specs)s, %(colors)s,
                            %(images)s, %(image)s, TRUE, now()
                        )
                        ON CONFLICT (id) DO NOTHING
                        """,
                        {
                            **product,
                            "specs": Json(product["specs"]),
                            "colors": Json(product.get("colors", [])),
                            "images": Json(product.get("images", [])),
                        },
                    )
        conn.commit()
    return True


def fetch_products_from_database(database_url: str) -> list[dict[str, Any]]:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, name, price, compare_at_price, price_text, description, description_long,
                    category, customizable, pinned, featured, featured_rank,
                    specs, colors, images, image
                FROM products
                WHERE active = TRUE
                ORDER BY
                    CASE WHEN pinned THEN 0 ELSE 1 END,
                    COALESCE(featured_rank, 999),
                    name
                """
            )
            rows = cur.fetchall()
    return [dict(row) for row in rows]


def fetch_all_products_from_database(database_url: str) -> list[dict[str, Any]]:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, name, price, compare_at_price, price_text, description, description_long,
                    category, customizable, pinned, featured, featured_rank,
                    specs, colors, images, image, active
                FROM products
                ORDER BY
                    CASE WHEN active THEN 0 ELSE 1 END,
                    CASE WHEN pinned THEN 0 ELSE 1 END,
                    COALESCE(featured_rank, 999),
                    name
                """
            )
            rows = cur.fetchall()
    return [dict(row) for row in rows]


def upsert_product(database_url: str, product: dict[str, Any]) -> None:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (
                    id, name, price, compare_at_price, price_text, description, description_long,
                    category, customizable, pinned, featured, featured_rank,
                    specs, colors, images, image, active, updated_at
                )
                VALUES (
                    %(id)s, %(name)s, %(price)s, %(compare_at_price)s, %(price_text)s,
                    %(description)s, %(description_long)s, %(category)s,
                    %(customizable)s, %(pinned)s, %(featured)s, %(featured_rank)s,
                    %(specs)s, %(colors)s, %(images)s, %(image)s, %(active)s, now()
                )
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    price = EXCLUDED.price,
                    compare_at_price = EXCLUDED.compare_at_price,
                    price_text = EXCLUDED.price_text,
                    description = EXCLUDED.description,
                    description_long = EXCLUDED.description_long,
                    category = EXCLUDED.category,
                    customizable = EXCLUDED.customizable,
                    pinned = EXCLUDED.pinned,
                    featured = EXCLUDED.featured,
                    featured_rank = EXCLUDED.featured_rank,
                    specs = EXCLUDED.specs,
                    colors = EXCLUDED.colors,
                    images = EXCLUDED.images,
                    image = EXCLUDED.image,
                    active = EXCLUDED.active,
                    updated_at = now()
                """,
                {
                    **product,
                    "specs": Json(product.get("specs") or {}),
                    "colors": Json(product.get("colors") or []),
                    "images": Json(product.get("images") or []),
                },
            )
        conn.commit()


def set_product_active(database_url: str, product_id: str, active: bool) -> None:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET active = %s, updated_at = now() WHERE id = %s",
                (active, product_id),
            )
        conn.commit()


def authenticate_admin(database_url: str, username: str, password: str) -> bool:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT password_hash
                FROM admin_users
                WHERE username = %s AND active = TRUE
                """,
                (username.strip().lower(),),
            )
            row = cur.fetchone()
    return bool(row and verify_password(password, row["password_hash"]))


def create_or_update_admin_user(
    database_url: str,
    username: str,
    password: str,
    display_name: str | None = None,
) -> None:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO admin_users (
                    username, password_hash, display_name, active, updated_at
                )
                VALUES (%s, %s, %s, TRUE, now())
                ON CONFLICT (username) DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    display_name = EXCLUDED.display_name,
                    active = TRUE,
                    updated_at = now()
                """,
                (username.strip().lower(), hash_password(password), display_name),
            )
        conn.commit()


def update_admin_password(database_url: str, username: str, password: str) -> None:
    connection_url = normalize_database_url(database_url)
    with psycopg.connect(connection_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE admin_users
                SET password_hash = %s, updated_at = now()
                WHERE username = %s AND active = TRUE
                """,
                (hash_password(password), username.strip().lower()),
            )
        conn.commit()


def load_products(database_url: str | None) -> tuple[list[dict[str, Any]], str, str | None]:
    if not database_url:
        return copy.deepcopy(DEFAULT_PRODUCTS), "demo", None
    try:
        initialize_database(database_url)
        products = fetch_products_from_database(database_url)
        return products or copy.deepcopy(DEFAULT_PRODUCTS), "neon", None
    except Exception as exc:
        return copy.deepcopy(DEFAULT_PRODUCTS), "fallback", str(exc)


def save_order(database_url: str | None, order: dict[str, Any]) -> tuple[bool, str | None]:
    if not database_url:
        return False, "DATABASE_URL não configurada; pedido não foi salvo no Neon."
    if psycopg is None:
        return False, "Dependência psycopg não instalada; pedido não foi salvo no Neon."

    try:
        connection_url = normalize_database_url(database_url)
        with psycopg.connect(connection_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO orders (
                        id, customer_name, notes, item_count, subtotal,
                        discount_rate, discount_amount, total,
                        has_flexible_price, whatsapp_message
                    )
                    VALUES (
                        %(id)s, %(customer_name)s, %(notes)s, %(item_count)s,
                        %(subtotal)s, %(discount_rate)s, %(discount_amount)s,
                        %(total)s, %(has_flexible_price)s, %(whatsapp_message)s
                    )
                    """,
                    {
                        "id": order["id"],
                        "customer_name": order["customer_name"],
                        "notes": order["notes"],
                        "item_count": order["item_count"],
                        "subtotal": order["subtotal"],
                        "discount_rate": order["discount_rate"],
                        "discount_amount": order["discount_amount"],
                        "total": order["total"],
                        "has_flexible_price": order["has_flexible_price"],
                        "whatsapp_message": order["whatsapp_message"],
                    },
                )
                for item in order["items"]:
                    cur.execute(
                        """
                        INSERT INTO order_items (
                            order_id, product_id, product_name, unit_price,
                            price_text, color, qty, subtotal
                        )
                        VALUES (
                            %(order_id)s, %(product_id)s, %(product_name)s,
                            %(unit_price)s, %(price_text)s, %(color)s,
                            %(qty)s, %(subtotal)s
                        )
                        """,
                        {
                            "order_id": order["id"],
                            "product_id": item["product"]["id"],
                            "product_name": item["product"]["name"],
                            "unit_price": item["unit_price"],
                            "price_text": item["product"].get("price_text"),
                            "color": item.get("color"),
                            "qty": item["qty"],
                            "subtotal": item["subtotal"],
                        },
                    )
            conn.commit()
        return True, None
    except Exception as exc:
        return False, str(exc)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer, header, [data-testid="stToolbar"],
        [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
          display: none !important;
        }
        .stApp {
          background: #f5f5f5;
          color: #0b1021;
        }
        .block-container {
          max-width: 1280px;
          padding: 0 1.25rem 4rem;
        }
        .hero-band {
          background: #ffffff;
          border-radius: 0;
          padding: 0.65rem 1rem;
          box-shadow: none;
          margin: 0 -1.25rem 0;
        }
        .brand-row {
          display: flex;
          align-items: center;
          gap: 0.8rem;
          margin-bottom: 0;
        }
        .brand-logo {
          width: 54px;
          height: 54px;
          object-fit: contain;
          border-radius: 14px;
          background: #ffffff;
          border: 1px solid rgba(0, 0, 0, 0.08);
          flex: 0 0 auto;
        }
        .note-row {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 0.6rem;
        }
        .brand-title {
          margin: 0;
          font-size: clamp(1.35rem, 2.6vw, 2.15rem);
          line-height: 1.12;
          letter-spacing: 0;
          font-weight: 900;
        }
        .brand-subtitle {
          color: #565656;
          margin-top: 0.15rem;
          font-weight: 600;
          font-size: 0.88rem;
        }
        .pill-note {
          border-radius: 999px;
          padding: 0.62rem 0.85rem;
          text-align: center;
          font-weight: 800;
          border: 1px solid rgba(245, 196, 0, 0.55);
          background: linear-gradient(90deg, #fff8bf, #fff3a0);
          margin: 0.75rem 0 0;
          font-size: 0.94rem;
        }
        .pill-note.blue {
          border-color: rgba(245, 196, 0, 0.55);
          background: linear-gradient(90deg, #fff9d7, #ffef77);
        }
        .market-tiles {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 1rem;
          margin: 1rem 0 1.25rem;
        }
        .market-tile {
          min-height: 122px;
          background: #ffffff;
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.13);
          border: 1px solid rgba(0, 0, 0, 0.05);
          padding: 1rem;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }
        .market-tile strong {
          display: block;
          font-size: 1rem;
          color: #333333;
          margin-bottom: 0.35rem;
        }
        .market-tile span {
          display: block;
          color: #555555;
          font-size: 0.9rem;
          line-height: 1.35;
        }
        .market-tile em {
          color: #00a650;
          font-style: normal;
          font-weight: 800;
        }
        .market-tile small {
          display: inline-block;
          color: #3483fa;
          background: #e8f1ff;
          border-radius: 6px;
          padding: 0.28rem 0.55rem;
          font-weight: 800;
          margin-top: 0.6rem;
          width: fit-content;
        }
        [class*="st-key-market-tile"] div[data-testid="stVerticalBlockBorderWrapper"] {
          min-height: 126px;
          border-radius: 8px;
          background: #ffffff;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.13);
          border-color: rgba(0, 0, 0, 0.05);
        }
        .market-tile-copy strong {
          display: block;
          color: #333333;
          font-size: 1rem;
          margin-bottom: 0.35rem;
        }
        .market-tile-copy span {
          display: block;
          color: #555555;
          line-height: 1.35;
          min-height: 2.7rem;
        }
        [class*="st-key-market-tile"] .stButton > button {
          background: #e8f1ff;
          border: 0;
          color: #3483fa;
          min-height: 2rem;
          border-radius: 6px;
          font-weight: 900;
        }
        [class*="st-key-market-tile"] .stButton > button:hover {
          background: #dbeaff;
          color: #2968c8;
        }
        .st-key-market-search-shell {
          background: #ffffff;
          margin: 0 -1.25rem;
          padding: 0.75rem 1rem 0.85rem;
          box-shadow: 0 1px 5px rgba(0, 0, 0, 0.10);
          position: sticky;
          top: 0;
          z-index: 50;
        }
        .st-key-search-cart-row div[data-testid="stHorizontalBlock"] {
          align-items: center;
          flex-wrap: nowrap;
          gap: 0.7rem;
        }
        .st-key-search-cart-row div[data-testid="stTextInput"] {
          flex: 1 1 auto;
          min-width: 0;
        }
        .st-key-search-cart-row div[data-testid="stElementContainer"]:has(.st-key-cart-fab-shell) {
          flex: 0 0 48px;
          width: 48px !important;
        }
        .st-key-market-search-shell div[data-testid="stTextInput"] input,
        .st-key-market-search-shell div[data-testid="stSelectbox"] div[data-baseweb="select"] {
          background: #f0f0f0;
          border: 0;
          box-shadow: none;
          min-height: 2.65rem;
          border-radius: 3px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
          border-color: rgba(0, 0, 0, 0.08);
          border-radius: 8px;
          background: #ffffff;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.13);
        }
        div[data-testid="stImage"] img {
          height: 220px !important;
          object-fit: contain !important;
          background: #ffffff;
          border-radius: 6px;
        }
        .cart-panel div[data-testid="stVerticalBlockBorderWrapper"] {
          box-shadow: none;
        }
        .product-title {
          font-size: 1rem;
          font-weight: 800;
          line-height: 1.2;
          margin: 0.3rem 0 0.15rem;
        }
        .product-description {
          color: #444444;
          font-size: 0.82rem;
          line-height: 1.35;
          min-height: 2.25rem;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .price-line {
          font-size: 1.32rem;
          font-weight: 800;
          color: #ee4d2d;
          margin: 0.15rem 0 0.2rem;
        }
        .price-stack {
          margin: 0.12rem 0 0.2rem;
        }
        .old-price {
          display: block;
          color: #8a8a8a;
          font-size: 0.78rem;
          text-decoration: line-through;
          line-height: 1.05;
        }
        .promo-price-row {
          display: flex;
          align-items: center;
          gap: 0.35rem;
          flex-wrap: wrap;
        }
        .price-line.promo {
          margin: 0;
        }
        .discount-tag {
          display: inline-flex;
          align-items: center;
          border-radius: 3px;
          padding: 0.12rem 0.28rem;
          color: #ee4d2d;
          background: #fff0eb;
          border: 1px solid #ffd1c4;
          font-size: 0.72rem;
          font-weight: 900;
        }
        .badge-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.35rem;
          margin: 0.15rem 0 0.2rem;
        }
        .badge {
          display: inline-flex;
          align-items: center;
          border-radius: 999px;
          padding: 0.18rem 0.5rem;
          background: #e8f1ff;
          color: #0b1021;
          font-size: 0.68rem;
          font-weight: 800;
          text-transform: uppercase;
        }
        .badge.hot {
          background: #fff0eb;
          color: #ee4d2d;
          border: 1px solid #ffd1c4;
        }
        .badge.sale {
          background: #ee4d2d;
          color: #ffffff;
          border: 1px solid #ee4d2d;
        }
        .section-heading {
          font-size: 1.35rem;
          font-weight: 500;
          margin: 0.4rem 0 0.75rem;
          color: #333333;
        }
        .status-line {
          color: #666666;
          font-size: 0.86rem;
          margin: 0.45rem 0 0.2rem;
        }
        .cart-title {
          font-size: 1.18rem;
          font-weight: 800;
          margin: 0 0 0.35rem;
        }
        .cart-empty {
          border-radius: 8px;
          padding: 0.8rem;
          background: #e8f1ff;
          color: #245179;
          font-weight: 650;
        }
        .cart-total {
          border: 1px solid #d6e0ef;
          border-radius: 8px;
          background: #f5fbff;
          padding: 0.8rem;
          margin: 0.55rem 0;
        }
        .cart-total span {
          display: block;
          color: #4e5b6a;
          font-size: 0.8rem;
        }
        .cart-total strong {
          display: block;
          font-size: 1.65rem;
          line-height: 1.15;
          font-weight: 500;
          margin-top: 0.2rem;
        }
        div[data-testid="stMetric"] {
          background: #edf3ff;
          border: 1px solid #d6e0ef;
          border-radius: 14px;
          padding: 0.7rem;
        }
        .stButton > button {
          border-radius: 999px;
          font-weight: 800;
          border-color: #cbd9ee;
          min-height: 2.45rem;
        }
        .stButton > button[kind="primary"] {
          background: #ee4d2d;
          border-color: #ee4d2d;
          color: #ffffff;
        }
        .stButton > button[kind="primary"]:hover {
          background: #d73211;
          border-color: #d73211;
          color: #ffffff;
        }
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
          border-radius: 12px;
        }
        .st-key-cart-fab-shell .stButton {
          position: relative;
          z-index: 2;
          width: 48px !important;
          height: 48px !important;
        }
        .st-key-cart-fab-shell .stButton > button {
          width: 48px !important;
          height: 48px !important;
          min-height: 48px;
          padding: 0 !important;
          border-radius: 50%;
          background: #ffffff;
          border: 0;
          color: #ee4d2d;
          box-shadow: none;
          font-weight: 900;
          font-size: 0 !important;
          overflow: visible;
        }
        .st-key-cart-fab-shell .stButton > button p {
          display: none !important;
          font-size: 0 !important;
          line-height: 0 !important;
        }
        .st-key-cart-fab-shell .stButton > button [data-testid="stIconMaterial"] {
          font-size: 1.85rem !important;
          margin: 0 !important;
          line-height: 1 !important;
        }
        .st-key-cart-fab-shell .stButton::after {
          position: absolute;
          top: -6px;
          right: -4px;
          min-width: 22px;
          height: 22px;
          border-radius: 999px;
          background: #ee4d2d;
          color: #ffffff;
          display: grid;
          place-items: center;
          font-size: 0.72rem;
          font-weight: 900;
          border: 2px solid #ffffff;
          box-shadow: 0 2px 8px rgba(0,0,0,0.18);
        }
        .cart-dialog-head {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          gap: 0.75rem;
          margin: 0.15rem 0 0.4rem;
        }
        .cart-dialog-title {
          font-size: 1rem;
          font-weight: 900;
          color: #111827;
        }
        .cart-dialog-count {
          color: #6b7280;
          font-size: 0.82rem;
          font-weight: 700;
        }
        .cart-dialog-total {
          background: #fff0eb;
          border: 1px solid rgba(0, 0, 0, 0.08);
          border-radius: 12px;
          padding: 0.75rem 0.85rem;
          margin: 0.35rem 0 0.75rem;
        }
        .cart-dialog-total span {
          display: block;
          color: #555555;
          font-size: 0.78rem;
          font-weight: 800;
          text-transform: uppercase;
        }
        .cart-dialog-total strong {
          display: block;
          color: #333333;
          font-size: 1.4rem;
          line-height: 1.1;
          margin-top: 0.15rem;
          font-weight: 900;
        }
        .cart-qty-display {
          height: 2rem;
          min-width: 2rem;
          display: grid;
          place-items: center;
          font-weight: 900;
          color: #333333;
        }
        .cart-item-line {
          display: flex;
          flex-direction: column;
          gap: 0.1rem;
        }
        .cart-item-name {
          font-weight: 900;
          line-height: 1.15;
          color: #111827;
        }
        .cart-item-meta {
          color: #6b7280;
          font-size: 0.82rem;
          line-height: 1.25;
        }
        .cart-item-subtotal {
          color: #333333;
          font-weight: 700;
          font-size: 0.92rem;
        }
        [class*="st-key-dialog-cart-item"] div[data-testid="stVerticalBlockBorderWrapper"] {
          border-radius: 12px;
          background: #ffffff;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.10);
          border-color: rgba(0, 0, 0, 0.08);
        }
        [class*="st-key-dialog-cart-controls"] {
          align-items: center;
        }
        [class*="st-key-dialog-cart-controls"] .stButton > button {
          width: 2.1rem;
          min-width: 2.1rem;
          height: 2.1rem;
          min-height: 2.1rem;
          padding: 0;
          border-radius: 999px;
        }
        [class*="st-key-dialog-cart-controls"] .stButton:last-child > button {
          width: auto;
          min-width: 5.6rem;
          padding: 0 0.8rem;
        }
        [class*="st-key-product-card"] div[data-testid="stVerticalBlockBorderWrapper"] {
          border-radius: 12px;
          background: #ffffff;
          box-shadow: 0 1px 8px rgba(15, 23, 42, 0.08);
          border-color: rgba(15, 23, 42, 0.06);
        }
        [class*="st-key-product-card"] div[data-testid="stImage"] img {
          height: 230px !important;
          width: 100% !important;
          object-fit: cover !important;
          background: #ffffff;
          border-radius: 10px;
        }
        [class*="st-key-product-card"] div[data-testid="stImage"] {
          margin-bottom: 0.35rem;
        }
        [class*="st-key-product-card"] .stButton > button {
          min-height: 2.35rem;
          border-radius: 999px;
          padding-left: 0.75rem;
          padding-right: 0.75rem;
        }
        [class*="st-key-product-card"] .stButton > button p {
          white-space: nowrap;
        }
        [class*="st-key-product-card"] div[data-testid="stSelectbox"] {
          margin-top: 0.15rem;
          margin-bottom: 0.45rem;
        }
        .st-key-cart-dialog div[data-testid="stVerticalBlockBorderWrapper"] {
          border-radius: 10px;
        }
        .st-key-cart-dialog .stButton > button {
          min-height: 2.1rem;
        }
        .st-key-cart-dialog div[data-testid="stImage"] img {
          width: 56px !important;
          height: 56px !important;
          object-fit: cover !important;
          border-radius: 8px;
        }
        div[data-testid="stDialog"] div[role="dialog"] {
          border-radius: 18px;
          max-height: min(86vh, 720px);
          overflow: auto;
        }
        @media (max-width: 900px) {
          .block-container {
            padding: 0 0.65rem 4rem;
          }
          .hero-band {
            padding: 0.55rem 0.65rem 0.45rem;
            border-radius: 0;
            margin: 0 -0.65rem 0;
          }
          .brand-row {
            gap: 0.7rem;
            margin-bottom: 0;
          }
          .brand-logo {
            width: 44px;
            height: 44px;
            border-radius: 11px;
          }
          .brand-title {
            font-size: 1.08rem;
          }
          .brand-subtitle {
            display: none;
          }
          .pill-note {
            border-radius: 14px;
            font-size: 0.78rem;
            padding: 0.52rem 0.6rem;
          }
          .st-key-market-search-shell {
            margin: 0 -0.65rem;
            padding: 0.55rem 0.65rem 0.65rem;
          }
          .st-key-search-cart-row div[data-testid="stHorizontalBlock"] {
            gap: 0.45rem;
          }
          .st-key-search-cart-row div[data-testid="stElementContainer"]:has(.st-key-cart-fab-shell) {
            flex-basis: 44px;
            width: 44px !important;
          }
          [class*="st-key-market-tile"] div[data-testid="stVerticalBlockBorderWrapper"] {
            min-height: 118px;
          }
          .market-tile-copy span {
            min-height: 2.3rem;
            font-size: 0.9rem;
          }
          div[data-testid="stImage"] img {
            height: 188px !important;
          }
          .note-row {
            grid-template-columns: 1fr;
          }
          .st-key-cart-fab-shell .stButton {
            width: 44px !important;
            height: 44px !important;
          }
          .st-key-cart-fab-shell .stButton > button {
            width: 44px !important;
            height: 44px !important;
            min-height: 44px;
          }
          .st-key-cart-fab-shell .stButton > button [data-testid="stIconMaterial"] {
            font-size: 1.65rem !important;
          }
          .section-heading {
            font-size: 1.25rem;
            margin-top: 0.65rem;
          }
          [class*="st-key-product-card"] div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
            box-shadow: 0 1px 8px rgba(15, 23, 42, 0.08);
          }
          [class*="st-key-product-card"] div[data-testid="stImage"] img {
            height: 168px !important;
          }
          .product-title {
            font-size: 0.96rem;
          }
          .product-description {
            display: none;
            min-height: 0;
          }
          [class*="st-key-product-card"] .stButton > button {
            min-height: 2.25rem;
            padding-left: 0.55rem;
            padding-right: 0.55rem;
          }
          [class*="st-key-product-card"] .stButton > button p {
            font-size: 0.86rem;
          }
          .price-line {
            font-size: 1.18rem;
          }
          .badge {
            font-size: 0.58rem;
            padding: 0.14rem 0.38rem;
          }
          div[data-testid="stDialog"] div[role="dialog"] {
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            top: auto !important;
            transform: none !important;
            width: 100vw !important;
            max-width: 100vw !important;
            max-height: 78vh !important;
            margin: 0 !important;
            padding: 0.9rem !important;
            border-radius: 22px 22px 0 0 !important;
          }
          .cart-dialog-total {
            margin-bottom: 0.55rem;
          }
          [class*="st-key-dialog-cart-item"] div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "cart": {},
        "customer_name": "",
        "customer_notes": "",
        "checkout_url": None,
        "checkout_message": None,
        "last_order_id": None,
        "order_saved": None,
        "order_save_error": None,
        "admin_authenticated": False,
        "admin_username": "",
        "cart_dialog_open": False,
        "show_discount_conditions": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_checkout_state() -> None:
    for key in ["checkout_url", "checkout_message", "last_order_id", "order_saved", "order_save_error"]:
        st.session_state[key] = None


def make_cart_key(product_id: str, color: str | None) -> str:
    return f"{product_id}::{color}" if color else product_id


def add_to_cart(product: dict[str, Any], qty: int, color: str | None) -> None:
    cart_key = make_cart_key(product["id"], color)
    entry = st.session_state.cart.get(
        cart_key, {"id": product["id"], "qty": 0, "color": color}
    )
    entry["qty"] = int(entry.get("qty", 0)) + int(qty)
    entry["color"] = color
    st.session_state.cart[cart_key] = entry
    clear_checkout_state()
    st.toast("Produto adicionado ao carrinho.")


def remove_from_cart(cart_key: str) -> None:
    st.session_state.cart.pop(cart_key, None)
    clear_checkout_state()


def set_cart_qty(cart_key: str, qty: int) -> None:
    if qty <= 0:
        remove_from_cart(cart_key)
        return
    if cart_key in st.session_state.cart:
        st.session_state.cart[cart_key]["qty"] = int(qty)
        clear_checkout_state()


def sort_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        products,
        key=lambda product: (
            0 if is_promotional_product(product) else 1,
            0 if product.get("pinned") else 1,
            product.get("featured_rank") if product.get("featured_rank") is not None else 999,
            product.get("name", ""),
        ),
    )


def filter_products(
    products: list[dict[str, Any]], search: str, category: str
) -> list[dict[str, Any]]:
    term = search.strip().lower()
    filtered = []
    for product in products:
        matches_text = (
            not term
            or term in product["name"].lower()
            or term in product["description"].lower()
            or term in product["category"].lower()
        )
        matches_category = category == "Todas as categorias" or product["category"] == category
        if matches_text and matches_category:
            filtered.append(product)
    return sort_products(filtered)


def get_discount_rate(item_count: int) -> Decimal:
    rate = Decimal("0")
    for min_items, tier_rate in DISCOUNT_TIERS:
        if item_count >= min_items:
            rate = tier_rate
    return rate


def cart_items(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    product_index = {product["id"]: product for product in products}
    items = []
    stale_keys = []

    for cart_key, entry in st.session_state.cart.items():
        product = product_index.get(entry.get("id"))
        if not product:
            stale_keys.append(cart_key)
            continue
        qty = max(1, int(entry.get("qty", 1)))
        unit_price = to_decimal(product.get("price"))
        subtotal = None if unit_price is None else unit_price * qty
        items.append(
            {
                "cart_key": cart_key,
                "product": product,
                "qty": qty,
                "color": entry.get("color"),
                "unit_price": unit_price,
                "subtotal": subtotal,
                "flexible": unit_price is None,
            }
        )

    for cart_key in stale_keys:
        st.session_state.cart.pop(cart_key, None)
    return items


def calculate_totals(items: list[dict[str, Any]]) -> dict[str, Any]:
    item_count = sum(item["qty"] for item in items)
    subtotal = sum((item["subtotal"] or Decimal("0")) for item in items)
    discount_rate = get_discount_rate(item_count)
    discount_amount = (subtotal * discount_rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total = subtotal - discount_amount
    return {
        "item_count": item_count,
        "subtotal": subtotal,
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "total": total,
        "has_flexible_price": any(item["flexible"] for item in items),
    }


def total_label(totals: dict[str, Any]) -> str:
    total_text = format_money(totals["total"])
    if totals["has_flexible_price"]:
        return f"{total_text} + a combinar" if totals["total"] > 0 else "A combinar"
    return total_text


def build_whatsapp_message(
    order_id: str,
    items: list[dict[str, Any]],
    totals: dict[str, Any],
    customer_name: str,
    notes: str,
    now: datetime,
) -> str:
    lines = []
    if customer_name:
        lines.append(
            f"Olá, meu nome é {customer_name} e gostaria de fazer um pedido na {BRAND_NAME}."
        )
    else:
        lines.append(f"Olá, gostaria de fazer um pedido na {BRAND_NAME}.")
    lines.append("")
    lines.append("Itens:")

    for item in items:
        product = item["product"]
        color_label = f" (Cor: {item['color']})" if item.get("color") else ""
        if item["flexible"]:
            lines.append(f"- {item['qty']}x {product['name']}{color_label} (A combinar)")
            continue
        lines.append(
            f"- {item['qty']}x {product['name']}{color_label} "
            f"({format_money(item['unit_price'])}) = {format_money(item['subtotal'])}"
        )

    lines.append("")
    if totals["discount_amount"] > 0:
        discount_percent = int(totals["discount_rate"] * 100)
        lines.append(
            f"Desconto ({discount_percent}%): -{format_money(totals['discount_amount'])}"
        )
    lines.append(f"Total: {total_label(totals)}")

    if notes:
        lines.append(f"Observações: {notes}")
    lines.append(f"Data/Hora: {now:%d/%m/%Y %H:%M}")
    lines.append(f"ID do pedido: {order_id}")
    return "\n".join(lines)


def build_order(
    items: list[dict[str, Any]],
    totals: dict[str, Any],
    customer_name: str,
    notes: str,
) -> dict[str, Any]:
    now = get_now()
    order_id = generate_order_id(now)
    message = build_whatsapp_message(order_id, items, totals, customer_name, notes, now)
    return {
        "id": order_id,
        "customer_name": customer_name,
        "notes": notes,
        "item_count": totals["item_count"],
        "subtotal": totals["subtotal"],
        "discount_rate": totals["discount_rate"],
        "discount_amount": totals["discount_amount"],
        "total": totals["total"],
        "has_flexible_price": totals["has_flexible_price"],
        "whatsapp_message": message,
        "items": items,
    }


def whatsapp_url(phone: str, message: str) -> str:
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{normalize_whatsapp_phone(phone)}?text={encoded}"


def append_quick_note(note: str) -> None:
    current = st.session_state.customer_notes.strip()
    parts = [part.strip() for part in current.split(",") if part.strip()]
    if note not in parts:
        parts.append(note)
    st.session_state.customer_notes = ", ".join(parts)
    clear_checkout_state()


def render_header(db_status: str, db_error: str | None) -> None:
    logo = image_data_uri("IMAGEM.jpeg")
    logo_html = f'<img class="brand-logo" src="{logo}" alt="Logo {BRAND_NAME}" />' if logo else ""
    st.markdown(
        f"""
        <section class="hero-band">
          <div class="brand-row">
            {logo_html}
            <div>
              <h1 class="brand-title">{BRAND_NAME}</h1>
              <div class="brand-subtitle">Catálogo estilo cardápio para impressão 3D</div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if db_status == "neon":
        return
    elif db_status == "demo":
        st.info(
            "Configure DATABASE_URL em `.streamlit/secrets.toml` para salvar pedidos no Neon."
        )
    else:
        st.warning(
            "Não consegui conectar ao Neon agora. O catálogo abriu em modo local e o pedido "
            "ainda pode ser enviado pelo WhatsApp."
        )
        if db_error:
            with st.expander("Detalhe técnico da conexão"):
                st.code(db_error)


def render_product(product: dict[str, Any], suffix: str) -> None:
    with st.container(border=True, key=f"product-card-{suffix}-{product['id']}"):
        image = image_source(product.get("image"))
        if image:
            st.image(image, width="stretch")

        badges = [f'<span class="badge">{product["category"]}</span>']
        promo_percent = get_promotion_percent(product)
        if promo_percent is not None:
            badges.append(f'<span class="badge sale">-{promo_percent}%</span>')
        if product.get("featured"):
            badges.append('<span class="badge hot">Destaque</span>')
        if product.get("customizable"):
            badges.append('<span class="badge hot">Personalizável</span>')
        st.markdown(
            f'<div class="badge-row">{"".join(badges)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="product-title">{product["name"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="product-description">{product["description"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(render_price_html(product), unsafe_allow_html=True)

        color = None
        colors = product.get("colors") or []
        if colors:
            color = st.selectbox(
                "Cor",
                colors,
                key=f"color-{suffix}-{product['id']}",
            )

        details = st.popover("Ver detalhes", width="stretch")
        add_pressed = st.button(
            "Adicionar",
            key=f"add-{suffix}-{product['id']}",
            type="primary",
            width="stretch",
        )

        with details:
            st.write(product.get("description_long") or product.get("description"))
            specs = product.get("specs") or {}
            if specs:
                st.write(f"Dimensões: {specs.get('dimensoes', 'A confirmar')}")
                st.write(f"Tempo de impressão: {specs.get('tempo', 'A confirmar')}")

            gallery = product.get("images") or [product.get("image")]
            gallery = [image for image in gallery if image]
            if gallery:
                cols = st.columns(min(3, len(gallery)))
                for index, gallery_image in enumerate(gallery):
                    with cols[index % len(cols)]:
                        source = image_source(gallery_image)
                        if source:
                            st.image(source, width="stretch")

        if add_pressed:
            add_to_cart(product, 1, color)
            st.rerun()


def render_product_grid(products: list[dict[str, Any]], suffix: str) -> None:
    for start in range(0, len(products), 4):
        row = products[start : start + 4]
        with st.container(key=f"product-row-{suffix}-{start}"):
            cols = st.columns(4)
            for col, product in zip(cols, row):
                with col:
                    render_product(product, suffix)


def render_search_controls(
    products: list[dict[str, Any]],
    database_url: str | None,
    phone: str,
) -> tuple[str, str]:
    categories = ["Todas as categorias"] + sorted({product["category"] for product in products})
    if "catalog_search" not in st.session_state:
        st.session_state.catalog_search = ""
    if "catalog_category" not in st.session_state:
        st.session_state.catalog_category = "Todas as categorias"
    if st.session_state.catalog_category not in categories:
        st.session_state.catalog_category = "Todas as categorias"
    with st.container(key="market-search-shell"):
        with st.container(
            horizontal=True,
            vertical_alignment="center",
            gap="small",
            key="search-cart-row",
        ):
            search = st.text_input(
                "Buscar",
                placeholder="Buscar produtos, peças ou ideias",
                label_visibility="collapsed",
                key="catalog_search",
                width="stretch",
            )
            render_cart_fab(products, database_url, phone)
        category = st.selectbox(
            "Categoria",
            categories,
            label_visibility="collapsed",
            key="catalog_category",
            width="stretch",
        )
    return search, category


def render_store_banners() -> None:
    st.markdown(
        f"""
        <div class="note-row">
          <div class="pill-note">{DELIVERY_NOTE}</div>
          <div class="pill-note blue">{PROMO_NOTE}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def set_catalog_filter(category: str = "Todas as categorias", search: str = "") -> None:
    st.session_state.catalog_category = category
    st.session_state.catalog_search = search


def toggle_discount_conditions() -> None:
    st.session_state.show_discount_conditions = not st.session_state.get(
        "show_discount_conditions", False
    )


def render_market_tile(
    title: str,
    body: str,
    button_label: str,
    key: str,
    *,
    category: str = "Todas as categorias",
    search: str = "",
    discount_toggle: bool = False,
) -> None:
    with st.container(border=True, key=f"market-tile-{key}"):
        st.markdown(
            f"""
            <div class="market-tile-copy">
              <strong>{title}</strong>
              <span>{body}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if discount_toggle:
            st.button(
                button_label,
                key=f"tile-button-{key}",
                on_click=toggle_discount_conditions,
                width="stretch",
            )
        else:
            st.button(
                button_label,
                key=f"tile-button-{key}",
                on_click=set_catalog_filter,
                args=(category, search),
                width="stretch",
            )


def render_market_tiles() -> None:
    cols = st.columns(4)
    with cols[0]:
        render_market_tile(
            "Frete grátis",
            "Entrega grátis em São Gonçalo do Pará - MG.",
            "Ver produtos",
            "free-shipping",
        )
    with cols[1]:
        render_market_tile(
            "Peças sob medida",
            "Você envia a referência e eu combino o valor final.",
            "Personalizados",
            "custom",
            category="Personalizados",
        )
    with cols[2]:
        render_market_tile(
            "Menos de R$100",
            "Suportes e decoração com preços baixos.",
            "Explorar",
            "under-100",
        )
    with cols[3]:
        render_market_tile(
            "Desconto progressivo",
            "Até 7% OFF comprando mais itens.",
            "Ver condição",
            "discount",
            discount_toggle=True,
        )
    if st.session_state.get("show_discount_conditions", False):
        st.info("Desconto automático no carrinho: 2 itens = 2%, 3 itens = 5%, 6 itens = 7%.")


def render_catalog(products: list[dict[str, Any]], search: str, category: str) -> None:
    filtered = filter_products(products, search, category)
    if not filtered:
        st.warning("Nenhum produto encontrado. Ajuste a busca ou o filtro.")
        return

    promotional_products = [product for product in filtered if is_promotional_product(product)]
    regular_products = [product for product in filtered if not is_promotional_product(product)]

    if promotional_products:
        st.markdown('<div class="section-heading">Produtos em promoção</div>', unsafe_allow_html=True)
        render_product_grid(promotional_products, "promo")

    if regular_products:
        heading = "Todos os produtos" if promotional_products else "Destaques do catálogo"
        st.markdown(f'<div class="section-heading">{heading}</div>', unsafe_allow_html=True)
        render_product_grid(regular_products, "catalog")


def render_sidebar(products: list[dict[str, Any]], database_url: str | None, phone: str) -> None:
    st.sidebar.title("Carrinho")
    items = cart_items(products)
    totals = calculate_totals(items)

    if not items:
        st.sidebar.info("Carrinho vazio. Escolha algo no catálogo para começar.")
    else:
        for item in items:
            product = item["product"]
            with st.sidebar.container(border=True):
                st.write(f"**{product['name']}**")
                if item.get("color"):
                    st.caption(f"Cor: {item['color']}")
                unit_label = format_money(item["unit_price"]) if not item["flexible"] else "A combinar"
                subtotal_label = format_money(item["subtotal"]) if item["subtotal"] else "A combinar"
                st.caption(f"Unitário: {unit_label}")
                st.write(f"Subtotal: **{subtotal_label}**")

                qty = st.number_input(
                    "Qtd.",
                    min_value=1,
                    max_value=99,
                    value=item["qty"],
                    step=1,
                    key=f"cart-qty-{item['cart_key']}",
                )
                if int(qty) != item["qty"]:
                    set_cart_qty(item["cart_key"], int(qty))
                    st.rerun()

                if st.button(
                    "Remover",
                    key=f"remove-{item['cart_key']}",
                    width="stretch",
                ):
                    remove_from_cart(item["cart_key"])
                    st.rerun()

    st.sidebar.metric("Total", total_label(totals))
    if totals["discount_amount"] > 0:
        discount_percent = int(totals["discount_rate"] * 100)
        st.sidebar.success(
            f"Desconto ({discount_percent}%): -{format_money(totals['discount_amount'])}"
        )
    elif totals["item_count"] < 2:
        st.sidebar.caption("Condição: a partir de 2 itens, 2% de desconto.")
    else:
        st.sidebar.caption("Condição: maior desconto aplicado automaticamente.")

    st.sidebar.divider()
    st.sidebar.subheader("Finalização no WhatsApp")
    st.sidebar.text_input("Nome do cliente", key="customer_name")
    st.sidebar.text_area(
        "Observações (prazo, entrega)",
        key="customer_notes",
        placeholder="Ex: entrega semana que vem",
        height=96,
    )

    chip_cols = st.sidebar.columns(3)
    for col, note in zip(chip_cols, ["Personalizado", "Retirada", "Entrega"]):
        with col:
            st.button(note, key=f"quick-{note}", on_click=append_quick_note, args=(note,))

    customer_name = st.session_state.customer_name.strip()
    notes = st.session_state.customer_notes.strip()
    can_finalize = bool(items)

    if st.sidebar.button(
        "Finalizar no WhatsApp",
        type="primary",
        disabled=not can_finalize,
        width="stretch",
    ):
        if not customer_name:
            st.sidebar.error("Informe o nome para continuar.")
        else:
            order = build_order(items, totals, customer_name, notes)
            saved, error = save_order(database_url, order)
            st.session_state.checkout_message = order["whatsapp_message"]
            st.session_state.checkout_url = whatsapp_url(phone, order["whatsapp_message"])
            st.session_state.last_order_id = order["id"]
            st.session_state.order_saved = saved
            st.session_state.order_save_error = error
            st.rerun()

    if st.session_state.checkout_url:
        if st.session_state.order_saved:
            st.sidebar.success(f"Pedido {st.session_state.last_order_id} salvo no Neon.")
        else:
            st.sidebar.warning(st.session_state.order_save_error or "Pedido não salvo no Neon.")
        st.sidebar.link_button(
            "Abrir WhatsApp",
            st.session_state.checkout_url,
            type="primary",
            width="stretch",
        )
        st.sidebar.text_area(
            "Mensagem gerada",
            value=st.session_state.checkout_message,
            height=180,
        )

    if items and st.sidebar.button("Limpar carrinho", width="stretch"):
        st.session_state.cart = {}
        clear_checkout_state()
        st.rerun()


def sync_customer_field(widget_key: str, state_key: str) -> None:
    st.session_state[state_key] = st.session_state.get(widget_key, "")
    clear_checkout_state()


def render_cart_panel(
    products: list[dict[str, Any]],
    database_url: str | None,
    phone: str,
    key_prefix: str = "cart",
) -> None:
    items = cart_items(products)
    totals = calculate_totals(items)

    with st.container(border=True):
        st.markdown('<div class="cart-title">Carrinho</div>', unsafe_allow_html=True)

        if not items:
            st.markdown(
                '<div class="cart-empty">Carrinho vazio. Escolha um produto para começar.</div>',
                unsafe_allow_html=True,
            )
        else:
            for item in items:
                product = item["product"]
                with st.container(border=True):
                    unit_label = format_money(item["unit_price"]) if not item["flexible"] else "A combinar"
                    subtotal_label = format_money(item["subtotal"]) if item["subtotal"] else "A combinar"
                    st.write(f"**{product['name']}**")
                    meta = f"Unitário: {unit_label}"
                    if item.get("color"):
                        meta += f" • Cor: {item['color']}"
                    st.caption(meta)
                    st.write(f"Subtotal: **{subtotal_label}**")

                    dec_col, qty_col, inc_col, remove_col = st.columns(
                        [0.18, 0.18, 0.18, 0.46], vertical_alignment="center"
                    )
                    with dec_col:
                        dec = st.button("-", key=f"{key_prefix}-dec-{item['cart_key']}")
                    with qty_col:
                        st.markdown(
                            f'<div class="cart-qty-display">{item["qty"]}</div>',
                            unsafe_allow_html=True,
                        )
                    with inc_col:
                        inc = st.button("+", key=f"{key_prefix}-inc-{item['cart_key']}")
                    with remove_col:
                        remove = st.button(
                            "Remover",
                            key=f"{key_prefix}-remove-{item['cart_key']}",
                            width="stretch",
                        )
                    if dec:
                        set_cart_qty(item["cart_key"], item["qty"] - 1)
                        st.rerun()
                    if inc:
                        set_cart_qty(item["cart_key"], item["qty"] + 1)
                        st.rerun()
                    if remove:
                        remove_from_cart(item["cart_key"])
                        st.rerun()

        st.markdown(
            f"""
            <div class="cart-total">
              <span>Total</span>
              <strong>{total_label(totals)}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if totals["discount_amount"] > 0:
            discount_percent = int(totals["discount_rate"] * 100)
            st.success(
                f"Desconto ({discount_percent}%): -{format_money(totals['discount_amount'])}"
            )
        elif totals["item_count"] < 2:
            st.caption("Condição: a partir de 2 itens, 2% de desconto.")
        else:
            st.caption("Condição: maior desconto aplicado automaticamente.")

        st.divider()
        st.subheader("Finalização no WhatsApp")
        name_key = f"{key_prefix}-customer-name"
        notes_key = f"{key_prefix}-customer-notes"
        if st.session_state.get(name_key) != st.session_state.customer_name:
            st.session_state[name_key] = st.session_state.customer_name
        if st.session_state.get(notes_key) != st.session_state.customer_notes:
            st.session_state[notes_key] = st.session_state.customer_notes

        st.text_input(
            "Nome do cliente",
            key=name_key,
            on_change=sync_customer_field,
            args=(name_key, "customer_name"),
        )
        st.text_area(
            "Observações",
            key=notes_key,
            placeholder="Ex: entrega semana que vem",
            height=92,
            on_change=sync_customer_field,
            args=(notes_key, "customer_notes"),
        )

        chip_cols = st.columns(3)
        for col, note, label in zip(
            chip_cols,
            ["Personalizado", "Retirada", "Entrega"],
            ["Pers.", "Retirada", "Entrega"],
        ):
            with col:
                st.button(label, key=f"{key_prefix}-quick-{note}", on_click=append_quick_note, args=(note,))

        customer_name = st.session_state.customer_name.strip()
        notes = st.session_state.customer_notes.strip()
        can_finalize = bool(items)

        if st.button(
            "Finalizar no WhatsApp",
            type="primary",
            disabled=not can_finalize,
            width="stretch",
            key=f"{key_prefix}-finalize",
        ):
            if not customer_name:
                st.error("Informe o nome para continuar.")
            else:
                order = build_order(items, totals, customer_name, notes)
                saved, error = save_order(database_url, order)
                st.session_state.checkout_message = order["whatsapp_message"]
                st.session_state.checkout_url = whatsapp_url(phone, order["whatsapp_message"])
                st.session_state.last_order_id = order["id"]
                st.session_state.order_saved = saved
                st.session_state.order_save_error = error
                st.rerun()

        if st.session_state.checkout_url:
            if st.session_state.order_saved:
                st.success(f"Pedido {st.session_state.last_order_id} salvo no Neon.")
            else:
                st.warning(st.session_state.order_save_error or "Pedido não salvo no Neon.")
            st.link_button(
                "Abrir WhatsApp",
                st.session_state.checkout_url,
                type="primary",
                width="stretch",
                key=f"{key_prefix}-open-whatsapp",
            )
            st.text_area(
                "Mensagem gerada",
                value=st.session_state.checkout_message,
                height=160,
                key=f"{key_prefix}-generated-message",
            )

        if items and st.button("Limpar carrinho", width="stretch", key=f"{key_prefix}-clear"):
            st.session_state.cart = {}
            clear_checkout_state()
            st.rerun()


def render_compact_cart_panel(
    products: list[dict[str, Any]],
    database_url: str | None,
    phone: str,
    key_prefix: str = "cart",
) -> None:
    items = cart_items(products)
    totals = calculate_totals(items)

    st.markdown(
        f"""
        <div class="cart-dialog-head">
          <div>
            <div class="cart-dialog-title">Itens escolhidos</div>
            <div class="cart-dialog-count">{totals["item_count"]} item(ns) no carrinho</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not items:
        st.markdown(
            '<div class="cart-empty">Carrinho vazio. Escolha um produto para começar.</div>',
            unsafe_allow_html=True,
        )
        return

    for item in items:
        product = item["product"]
        unit_label = format_money(item["unit_price"]) if not item["flexible"] else "A combinar"
        subtotal_label = format_money(item["subtotal"]) if item["subtotal"] else "A combinar"
        meta = f"Unitário: {unit_label}"
        if item.get("color"):
            meta += f" • Cor: {item['color']}"

        with st.container(border=True, key=f"{key_prefix}-cart-item-{item['cart_key']}"):
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap="small",
                key=f"{key_prefix}-cart-row-{item['cart_key']}",
            ):
                source = image_source(product.get("image"))
                if source:
                    st.image(source, width=56)
                st.markdown(
                    f"""
                    <div class="cart-item-line">
                      <div class="cart-item-name">{product["name"]}</div>
                      <div class="cart-item-meta">{meta}</div>
                      <div class="cart-item-subtotal">Subtotal: {subtotal_label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap="small",
                key=f"{key_prefix}-cart-controls-{item['cart_key']}",
            ):
                dec = st.button("-", key=f"{key_prefix}-dec-{item['cart_key']}")
                st.markdown(
                    f'<div class="cart-qty-display">{item["qty"]}</div>',
                    unsafe_allow_html=True,
                )
                inc = st.button("+", key=f"{key_prefix}-inc-{item['cart_key']}")
                remove = st.button("Remover", key=f"{key_prefix}-remove-{item['cart_key']}")

            if dec:
                set_cart_qty(item["cart_key"], item["qty"] - 1)
                st.rerun()
            if inc:
                set_cart_qty(item["cart_key"], item["qty"] + 1)
                st.rerun()
            if remove:
                remove_from_cart(item["cart_key"])
                st.rerun()

    st.markdown(
        f"""
        <div class="cart-dialog-total">
          <span>Total</span>
          <strong>{total_label(totals)}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if totals["discount_amount"] > 0:
        discount_percent = int(totals["discount_rate"] * 100)
        st.success(f"Desconto ({discount_percent}%): -{format_money(totals['discount_amount'])}")
    elif totals["item_count"] < 2:
        st.caption("A partir de 2 itens, o desconto entra automaticamente.")
    else:
        st.caption("Maior desconto aplicado automaticamente.")

    name_key = f"{key_prefix}-customer-name"
    notes_key = f"{key_prefix}-customer-notes"
    if st.session_state.get(name_key) != st.session_state.customer_name:
        st.session_state[name_key] = st.session_state.customer_name
    if st.session_state.get(notes_key) != st.session_state.customer_notes:
        st.session_state[notes_key] = st.session_state.customer_notes

    st.text_input(
        "Nome do cliente",
        key=name_key,
        on_change=sync_customer_field,
        args=(name_key, "customer_name"),
    )
    st.text_area(
        "Observações",
        key=notes_key,
        placeholder="Ex: entrega semana que vem",
        height=82,
        on_change=sync_customer_field,
        args=(notes_key, "customer_notes"),
    )

    with st.container(horizontal=True, gap="small", key=f"{key_prefix}-quick-notes"):
        for note, label in [
            ("Personalizado", "Personalizado"),
            ("Retirada", "Retirada"),
            ("Entrega", "Entrega"),
        ]:
            st.button(
                label,
                key=f"{key_prefix}-quick-{note}",
                on_click=append_quick_note,
                args=(note,),
            )

    customer_name = st.session_state.customer_name.strip()
    notes = st.session_state.customer_notes.strip()

    if st.button(
        "Finalizar no WhatsApp",
        type="primary",
        width="stretch",
        key=f"{key_prefix}-finalize",
    ):
        if not customer_name:
            st.error("Informe o nome para continuar.")
        else:
            order = build_order(items, totals, customer_name, notes)
            saved, error = save_order(database_url, order)
            st.session_state.checkout_message = order["whatsapp_message"]
            st.session_state.checkout_url = whatsapp_url(phone, order["whatsapp_message"])
            st.session_state.last_order_id = order["id"]
            st.session_state.order_saved = saved
            st.session_state.order_save_error = error
            st.rerun()

    if st.session_state.checkout_url:
        if st.session_state.order_saved:
            st.success(f"Pedido {st.session_state.last_order_id} salvo no Neon.")
        else:
            st.warning(st.session_state.order_save_error or "Pedido não salvo no Neon.")
        st.link_button(
            "Abrir WhatsApp",
            st.session_state.checkout_url,
            type="primary",
            width="stretch",
            key=f"{key_prefix}-open-whatsapp",
        )

    if st.button("Limpar carrinho", width="stretch", key=f"{key_prefix}-clear"):
        st.session_state.cart = {}
        clear_checkout_state()
        st.rerun()


def close_cart_dialog() -> None:
    st.session_state.cart_dialog_open = False


@st.dialog("Carrinho", width="small", on_dismiss=close_cart_dialog)
def render_cart_dialog(products: list[dict[str, Any]], database_url: str | None, phone: str) -> None:
    with st.container(key="cart-dialog"):
        render_compact_cart_panel(products, database_url, phone, key_prefix="dialog")


def render_cart_fab(products: list[dict[str, Any]], database_url: str | None, phone: str) -> None:
    totals = calculate_totals(cart_items(products))
    item_count = totals["item_count"]
    badge_rule = (
        f'.st-key-cart-fab-shell .stButton::after {{ content: "{item_count}"; }}'
        if item_count
        else ".st-key-cart-fab-shell .stButton::after { display: none; }"
    )
    st.markdown(f"<style>{badge_rule}</style>", unsafe_allow_html=True)
    with st.container(key="cart-fab-shell"):
        if st.button(
            "Carrinho",
            key="cart-fab-button",
            icon=":material/shopping_cart:",
            help="Abrir carrinho",
        ):
            st.session_state.cart_dialog_open = True
    if st.session_state.cart_dialog_open:
        render_cart_dialog(products, database_url, phone)


def product_form_payload(
    *,
    product_id: str,
    name: str,
    category: str,
    price_mode: str,
    price_value: float,
    compare_price_value: float,
    clear_promotion: bool,
    price_text: str,
    description: str,
    description_long: str,
    dimensions: str,
    print_time: str,
    colors_text: str,
    image_reference: str,
    gallery_text: str,
    uploaded_file: Any,
    customizable: bool,
    pinned: bool,
    featured: bool,
    featured_rank: int | None,
    active: bool,
    existing_product: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing_product = existing_product or {}
    uploaded_image = uploaded_image_to_data_uri(uploaded_file)
    existing_image = existing_product.get("image") or PERSONALIZED_PLACEHOLDER
    existing_images = existing_product.get("images") or []

    if uploaded_image:
        image = uploaded_image
    elif image_reference.strip():
        image = image_reference.strip()
    else:
        image = existing_image

    gallery = parse_lines(gallery_text)
    if not gallery and existing_images:
        gallery = list(existing_images)
    if image and image not in gallery:
        gallery.insert(0, image)

    if price_mode == "Preço fixo":
        price = to_decimal(price_value)
        final_price_text = None
    else:
        price = None
        final_price_text = price_text.strip() or "A combinar"

    existing_price = to_decimal(existing_product.get("price"))
    existing_compare_price = to_decimal(existing_product.get("compare_at_price"))
    manual_compare_price = to_decimal(compare_price_value) if compare_price_value else None
    compare_at_price = existing_compare_price
    if clear_promotion or price is None:
        compare_at_price = None
    elif manual_compare_price and manual_compare_price > price:
        compare_at_price = manual_compare_price
    elif existing_price is not None and price < existing_price:
        compare_at_price = max(existing_price, existing_compare_price or Decimal("0"))
    elif compare_at_price is not None and compare_at_price <= price:
        compare_at_price = None

    return {
        "id": product_id.strip().lower(),
        "name": name.strip(),
        "price": price,
        "compare_at_price": compare_at_price,
        "price_text": final_price_text,
        "description": description.strip(),
        "description_long": (description_long.strip() or description.strip()),
        "category": category.strip() or "Geral",
        "customizable": customizable,
        "pinned": pinned,
        "featured": featured,
        "featured_rank": featured_rank if featured else None,
        "specs": {
            "dimensoes": dimensions.strip() or "A confirmar",
            "tempo": print_time.strip() or "A confirmar",
        },
        "colors": parse_csv(colors_text),
        "images": gallery,
        "image": image or PERSONALIZED_PLACEHOLDER,
        "active": active,
    }


def render_product_admin_form(
    database_url: str,
    *,
    mode: str,
    product: dict[str, Any] | None = None,
) -> None:
    product = product or {}
    is_edit = mode == "edit"
    form_key = f"admin-{mode}-{product.get('id', 'new')}"

    current_image = product.get("image") or ""
    current_images = product.get("images") or []
    image_reference_value = "" if current_image.startswith("data:") else current_image
    gallery_value = "\n".join(
        image for image in current_images if image and not str(image).startswith("data:")
    )
    price_is_fixed = product.get("price") is not None

    if current_image:
        preview = image_source(current_image)
        if preview:
            st.image(preview, width=220)

    with st.form(form_key):
        if is_edit:
            product_id = st.text_input("ID do produto", value=product["id"], disabled=True)
        else:
            suggested_id = slugify(product.get("name", "novo-produto"))
            product_id = st.text_input("ID do produto", value=suggested_id)

        name = st.text_input("Nome", value=product.get("name", ""))
        category = st.text_input("Categoria", value=product.get("category", "Suportes"))
        price_mode = st.radio(
            "Tipo de preço",
            ["Preço fixo", "A combinar"],
            index=0 if price_is_fixed else 1,
            horizontal=True,
        )
        price_value = st.number_input(
            "Preço",
            min_value=0.0,
            value=float(product.get("price") or 0),
            step=0.5,
            format="%.2f",
            disabled=price_mode != "Preço fixo",
        )
        compare_price_value = st.number_input(
            "Preço antigo (promoção)",
            min_value=0.0,
            value=float(product.get("compare_at_price") or 0),
            step=0.5,
            format="%.2f",
            disabled=price_mode != "Preço fixo",
            help=(
                "Quando você baixa o preço de um produto, o app guarda o valor anterior "
                "aqui e mostra a promoção na loja."
            ),
        )
        clear_promotion = st.checkbox(
            "Limpar promoção deste produto",
            value=False,
            disabled=price_mode != "Preço fixo",
        )
        price_text = st.text_input(
            "Texto do preço",
            value=product.get("price_text") or "A combinar",
            disabled=price_mode == "Preço fixo",
        )
        description = st.text_area("Descrição curta", value=product.get("description", ""), height=80)
        description_long = st.text_area(
            "Descrição completa",
            value=product.get("description_long", ""),
            height=110,
        )

        specs = product.get("specs") or {}
        dimensions = st.text_input("Dimensões", value=specs.get("dimensoes", "A confirmar"))
        print_time = st.text_input("Tempo de impressão", value=specs.get("tempo", "A confirmar"))
        colors_text = st.text_input("Cores, separadas por vírgula", value=", ".join(product.get("colors") or []))

        image_reference = st.text_input(
            "Imagem principal (URL ou caminho do repo)",
            value=image_reference_value,
            help="Se já existe imagem enviada ao banco, deixe vazio para manter.",
        )
        gallery_text = st.text_area(
            "Galeria (uma URL/caminho por linha)",
            value=gallery_value,
            height=110,
        )
        uploaded_file = st.file_uploader(
            "Enviar nova imagem para salvar no banco",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"{form_key}-upload",
        )

        flag_cols = st.columns(5)
        with flag_cols[0]:
            customizable = st.checkbox("Personalizável", value=bool(product.get("customizable", False)))
        with flag_cols[1]:
            pinned = st.checkbox("Fixar primeiro", value=bool(product.get("pinned", False)))
        with flag_cols[2]:
            featured = st.checkbox("Destaque", value=bool(product.get("featured", True)))
        with flag_cols[3]:
            active = st.checkbox("Ativo", value=bool(product.get("active", True)))
        with flag_cols[4]:
            featured_rank = st.number_input(
                "Ordem",
                min_value=0,
                max_value=999,
                value=int(product.get("featured_rank") or 10),
                step=1,
            )

        submitted = st.form_submit_button(
            "Salvar produto" if is_edit else "Adicionar produto",
            type="primary",
            width="stretch",
        )

    if submitted:
        if not product_id.strip() or not name.strip() or not description.strip():
            st.error("Preencha ID, nome e descrição curta.")
            return
        payload = product_form_payload(
            product_id=product_id,
            name=name,
            category=category,
            price_mode=price_mode,
            price_value=price_value,
            compare_price_value=compare_price_value,
            clear_promotion=clear_promotion,
            price_text=price_text,
            description=description,
            description_long=description_long,
            dimensions=dimensions,
            print_time=print_time,
            colors_text=colors_text,
            image_reference=image_reference,
            gallery_text=gallery_text,
            uploaded_file=uploaded_file,
            customizable=customizable,
            pinned=pinned,
            featured=featured,
            featured_rank=int(featured_rank),
            active=active,
            existing_product=product if is_edit else None,
        )
        upsert_product(database_url, payload)
        st.success("Produto salvo no Neon.")
        st.rerun()


def render_admin_login(database_url: str) -> None:
    with st.form("admin-login-form"):
        st.subheader("Acesso administrativo")
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", type="primary", width="stretch")

    if submitted:
        if authenticate_admin(database_url, username, password):
            st.session_state.admin_authenticated = True
            st.session_state.admin_username = username.strip().lower()
            st.success("Login feito.")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


def render_admin_panel(database_url: str | None) -> None:
    if not database_url:
        st.error("Configure DATABASE_URL para usar a área administrativa.")
        return
    if psycopg is None:
        st.error("Instale as dependências com `pip install -r requirements.txt`.")
        return

    initialize_database(database_url)

    if not st.session_state.admin_authenticated:
        render_admin_login(database_url)
        return

    top_cols = st.columns([0.72, 0.28], vertical_alignment="center")
    with top_cols[0]:
        st.success(f"Logado como {st.session_state.admin_username}.")
    with top_cols[1]:
        if st.button("Sair", width="stretch"):
            st.session_state.admin_authenticated = False
            st.session_state.admin_username = ""
            st.rerun()

    admin_tabs = st.tabs(["Editar produtos", "Novo produto", "Senha"])

    with admin_tabs[0]:
        products = fetch_all_products_from_database(database_url)
        if not products:
            st.info("Nenhum produto cadastrado ainda.")
        else:
            options = {
                f"{product['name']} ({product['id']}){' - inativo' if not product.get('active') else ''}": product
                for product in products
            }
            selected_label = st.selectbox("Produto", list(options.keys()))
            selected_product = options[selected_label]
            render_product_admin_form(database_url, mode="edit", product=selected_product)

    with admin_tabs[1]:
        render_product_admin_form(
            database_url,
            mode="new",
            product={
                "id": "novo-produto",
                "name": "",
                "description": "",
                "description_long": "",
                "category": "Suportes",
                "price": Decimal("0.00"),
                "compare_at_price": None,
                "price_text": None,
                "specs": {"dimensoes": "A confirmar", "tempo": "A confirmar"},
                "colors": [],
                "images": [],
                "image": PERSONALIZED_PLACEHOLDER,
                "customizable": False,
                "pinned": False,
                "featured": True,
                "featured_rank": 10,
                "active": True,
            },
        )

    with admin_tabs[2]:
        with st.form("change-admin-password"):
            new_password = st.text_input("Nova senha", type="password")
            confirm_password = st.text_input("Confirmar nova senha", type="password")
            submitted = st.form_submit_button("Alterar senha", type="primary")
        if submitted:
            if len(new_password) < 8:
                st.error("Use uma senha com pelo menos 8 caracteres.")
            elif new_password != confirm_password:
                st.error("As senhas não conferem.")
            else:
                update_admin_password(database_url, st.session_state.admin_username, new_password)
                st.success("Senha alterada.")


def main() -> None:
    st.set_page_config(page_title=f"{BRAND_NAME} | Catálogo", layout="wide")
    apply_styles()
    init_state()

    database_url = get_setting("DATABASE_URL")
    phone = get_setting("WHATSAPP_PHONE", DEFAULT_WHATSAPP_PHONE) or DEFAULT_WHATSAPP_PHONE
    products, db_status, db_error = load_products(database_url)
    admin_view = st.query_params.get("admin") == "1"

    render_header(db_status, db_error)

    if admin_view:
        render_admin_panel(database_url)
        return

    search, category = render_search_controls(products, database_url, phone)
    render_store_banners()
    render_catalog(products, search, category)


if __name__ == "__main__":
    main()
