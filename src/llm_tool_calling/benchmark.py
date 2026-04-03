"""82 benchmark queries with result-based validation.

Each query defines what a CORRECT ANSWER looks like, not which tools to use.
The agent is free to choose any path — we only check the final result.
"""

from dataclasses import dataclass, field


@dataclass
class BenchmarkQuery:
    id: str
    category: str
    difficulty: str
    query: str
    # Keywords that MUST appear in the answer (case-insensitive).
    answer_keywords: list[str] = field(default_factory=list)
    # Product IDs that should be found via search_products during the conversation.
    # Empty = no product check (e.g. conceptual questions).
    expected_product_ids: list[int] = field(default_factory=list)


BENCHMARK_QUERIES: list[BenchmarkQuery] = [
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY A: Localização Simples (topônimo → produto)
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="A01", category="Localização Simples", difficulty="easy",
        query="Cartas topográficas de Alecrim",
        answer_keywords=["alecrim"],
        expected_product_ids=[1, 2, 3],
    ),
    BenchmarkQuery(
        id="A02", category="Localização Simples", difficulty="easy",
        query="Ortoimagens de Porto Alegre",
        answer_keywords=["porto alegre"],
        expected_product_ids=[4, 10],
    ),
    BenchmarkQuery(
        id="A03", category="Localização Simples", difficulty="easy",
        query="Tem MDS de Brasília?",
        answer_keywords=["brasília"],
    ),
    BenchmarkQuery(
        id="A04", category="Localização Simples", difficulty="easy",
        query="Quero uma carta topográfica 50k de Santa Maria",
        answer_keywords=["santa maria"],
    ),
    BenchmarkQuery(
        id="A05", category="Localização Simples", difficulty="easy",
        query="Imagem de satélite de Manaus",
        answer_keywords=["manaus"],
    ),
    BenchmarkQuery(
        id="A06", category="Localização Simples", difficulty="medium",
        query="Imagem de drone de Itaipu",
        answer_keywords=["itaipu"],
        expected_product_ids=[5],
    ),
    BenchmarkQuery(
        id="A07", category="Localização Simples", difficulty="medium",
        query="Modelos 3D de Brasília",
        answer_keywords=["brasília"],
    ),
    BenchmarkQuery(
        id="A08", category="Localização Simples", difficulty="easy",
        query="Existe carta topográfica 25k de Porto Alegre?",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="A09", category="Localização Simples", difficulty="easy",
        query="Preciso de ortoimagem de Manaus, tem?",
        answer_keywords=["manaus"],
    ),
    BenchmarkQuery(
        id="A10", category="Localização Simples", difficulty="easy",
        query="MDT de Santa Maria, RS",
        answer_keywords=["santa maria"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY B: Região Informal
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="B01", category="Região Informal", difficulty="medium",
        query="MDS da Serra Gaúcha",
        answer_keywords=["serra gaúcha"],
        expected_product_ids=[6],
    ),
    BenchmarkQuery(
        id="B02", category="Região Informal", difficulty="medium",
        query="MDT do Pantanal",
        answer_keywords=["pantanal"],
        expected_product_ids=[8],
    ),
    BenchmarkQuery(
        id="B03", category="Região Informal", difficulty="medium",
        query="Ortoimagens do Vale do Taquari",
        answer_keywords=["vale do taquari"],
    ),
    BenchmarkQuery(
        id="B04", category="Região Informal", difficulty="medium",
        query="Cartas topográficas da Serra Gaúcha",
        answer_keywords=["serra gaúcha"],
    ),
    BenchmarkQuery(
        id="B05", category="Região Informal", difficulty="medium",
        query="Tem imagem de satélite do Pantanal?",
        answer_keywords=["pantanal"],
    ),
    BenchmarkQuery(
        id="B06", category="Região Informal", difficulty="medium",
        query="Dados de elevação disponíveis no Vale do Taquari",
        answer_keywords=["vale do taquari"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY C: Rota
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="C01", category="Rota", difficulty="hard",
        query="Cartas topográficas ao longo da rota entre Florianópolis e Porto Alegre",
        answer_keywords=["florianópolis", "porto alegre"],
    ),
    BenchmarkQuery(
        id="C02", category="Rota", difficulty="hard",
        query="Ortoimagens no caminho de Santa Maria a Alegrete",
        answer_keywords=["santa maria", "alegrete"],
    ),
    BenchmarkQuery(
        id="C03", category="Rota", difficulty="hard",
        query="Imagens ao longo da estrada entre Porto Alegre e Santa Maria",
        answer_keywords=["porto alegre", "santa maria"],
    ),
    BenchmarkQuery(
        id="C04", category="Rota", difficulty="hard",
        query="Que cartas cobrem o trajeto de Florianópolis a Porto Alegre?",
        answer_keywords=["florianópolis", "porto alegre"],
    ),
    BenchmarkQuery(
        id="C05", category="Rota", difficulty="hard",
        query="Preciso de cartas topográficas para planejar deslocamento de Santa Maria até Alegrete",
        answer_keywords=["santa maria", "alegrete"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY D: Filtro Temporal
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="D01", category="Filtro Temporal", difficulty="medium",
        query="Produto mais recente de qualquer tipo sobre Manaus",
        answer_keywords=["manaus"],
    ),
    BenchmarkQuery(
        id="D02", category="Filtro Temporal", difficulty="medium",
        query="Ortoimagens de Porto Alegre entre 2020 e 2023",
        answer_keywords=["porto alegre"],
        expected_product_ids=[4, 10],
    ),
    BenchmarkQuery(
        id="D03", category="Filtro Temporal", difficulty="medium",
        query="Carta topográfica mais recente de Santa Maria",
        answer_keywords=["santa maria"],
        expected_product_ids=[9],
    ),
    BenchmarkQuery(
        id="D04", category="Filtro Temporal", difficulty="medium",
        query="Qual a imagem mais nova de Porto Alegre?",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="D05", category="Filtro Temporal", difficulty="medium",
        query="Imagem de satélite de Manaus de 2024",
        answer_keywords=["manaus"],
    ),
    BenchmarkQuery(
        id="D06", category="Filtro Temporal", difficulty="medium",
        query="Cartas 25k mais novas de Santa Maria",
        answer_keywords=["santa maria", "25"],
        expected_product_ids=[9],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY E: Instalação Militar
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="E01", category="Instalação Militar", difficulty="medium",
        query="Carta 50k que pegue a 8ª Bda Inf Mec",
        answer_keywords=["8"],
    ),
    BenchmarkQuery(
        id="E02", category="Instalação Militar", difficulty="medium",
        query="MDS num raio de 15km do 3º BECmb em Cachoeira do Sul",
        answer_keywords=["cachoeira"],
    ),
    BenchmarkQuery(
        id="E03", category="Instalação Militar", difficulty="medium",
        query="Todos os produtos disponíveis na área da 8ª Brigada de Infantaria Mecanizada",
        answer_keywords=["brigada"],
    ),
    BenchmarkQuery(
        id="E04", category="Instalação Militar", difficulty="medium",
        query="Ortoimagem da região do 3º Batalhão de Engenharia de Combate",
        answer_keywords=["engenharia"],
    ),
    BenchmarkQuery(
        id="E05", category="Instalação Militar", difficulty="hard",
        query="Carta topográfica de melhor escala na área da 8 Bda Inf Mec",
        answer_keywords=["8"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY F: Fronteira Internacional
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="F01", category="Fronteira", difficulty="hard",
        query="Imagem de satélite da fronteira com Uruguai",
        answer_keywords=["uruguai"],
        expected_product_ids=[11],
    ),
    BenchmarkQuery(
        id="F02", category="Fronteira", difficulty="hard",
        query="Cartas topográficas da fronteira com a Argentina",
        answer_keywords=["argentina"],
    ),
    BenchmarkQuery(
        id="F03", category="Fronteira", difficulty="hard",
        query="Ortoimagens ao longo da fronteira com o Uruguai",
        answer_keywords=["uruguai"],
    ),
    BenchmarkQuery(
        id="F04", category="Fronteira", difficulty="hard",
        query="Que produtos cobrem a fronteira sul com a Argentina?",
        answer_keywords=["argentina"],
    ),
    BenchmarkQuery(
        id="F05", category="Fronteira", difficulty="hard",
        query="Imagens disponíveis na divisa com Uruguai",
        answer_keywords=["uruguai"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY G: Feições Geográficas
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="G01", category="Feições Geográficas", difficulty="hard",
        query="Imagens de drone das pontes na região de Santa Maria",
        answer_keywords=["ponte"],
    ),
    BenchmarkQuery(
        id="G02", category="Feições Geográficas", difficulty="hard",
        query="Tem imagem dos aeroportos do Rio Grande do Sul?",
        answer_keywords=["aeroporto"],
    ),
    BenchmarkQuery(
        id="G03", category="Feições Geográficas", difficulty="hard",
        query="Ortoimagens de barragens na região de Santa Maria",
        answer_keywords=["barragem"],
    ),
    BenchmarkQuery(
        id="G04", category="Feições Geográficas", difficulty="hard",
        query="Quais pontes existem perto de Santa Maria?",
        answer_keywords=["ponte"],
    ),
    BenchmarkQuery(
        id="G05", category="Feições Geográficas", difficulty="hard",
        query="Imagem de drone de barragens próximas a Porto Alegre",
        answer_keywords=["barragem"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY H: Hidrografia
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="H01", category="Hidrografia", difficulty="medium",
        query="MDS ao longo do rio Jacuí",
        answer_keywords=["jacuí"],
    ),
    BenchmarkQuery(
        id="H02", category="Hidrografia", difficulty="medium",
        query="Ortoimagens do rio Guaíba",
        answer_keywords=["guaíba"],
    ),
    BenchmarkQuery(
        id="H03", category="Hidrografia", difficulty="hard",
        query="Cartas topográficas que cubram o rio Jacuí inteiro",
        answer_keywords=["jacuí"],
    ),
    BenchmarkQuery(
        id="H04", category="Hidrografia", difficulty="medium",
        query="Tem imagem de drone do rio Guaíba?",
        answer_keywords=["guaíba"],
    ),
    BenchmarkQuery(
        id="H05", category="Hidrografia", difficulty="medium",
        query="MDT da região do rio Jacuí",
        answer_keywords=["jacuí"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY I: Inventário
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="I01", category="Inventário", difficulty="easy",
        query="Que produtos existem para Porto Alegre?",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="I02", category="Inventário", difficulty="easy",
        query="O que tem disponível para Manaus?",
        answer_keywords=["manaus"],
    ),
    BenchmarkQuery(
        id="I03", category="Inventário", difficulty="easy",
        query="Lista tudo que existe para Brasília",
        answer_keywords=["brasília"],
    ),
    BenchmarkQuery(
        id="I04", category="Inventário", difficulty="easy",
        query="Quais produtos cobrem Santa Maria?",
        answer_keywords=["santa maria"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY J: Escala
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="J01", category="Escala", difficulty="medium",
        query="Cartas topográficas de melhor escala possível em Alecrim",
        answer_keywords=["alecrim", "25.000"],
        expected_product_ids=[1],
    ),
    BenchmarkQuery(
        id="J02", category="Escala", difficulty="medium",
        query="Qual a carta de maior detalhe disponível para Porto Alegre?",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="J03", category="Escala", difficulty="medium",
        query="Me dá a carta mais detalhada de Santa Maria",
        answer_keywords=["santa maria", "25"],
        expected_product_ids=[9],
    ),
    BenchmarkQuery(
        id="J04", category="Escala", difficulty="medium",
        query="Qual a melhor escala de carta disponível para Manaus?",
        answer_keywords=["manaus"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY K: Desambiguação
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="K01", category="Desambiguação", difficulty="medium",
        query="Carta de Santa Cruz",
        answer_keywords=["santa cruz"],
    ),
    BenchmarkQuery(
        id="K02", category="Desambiguação", difficulty="medium",
        query="Mapa de São José",
        answer_keywords=["são josé"],
    ),
    BenchmarkQuery(
        id="K03", category="Desambiguação", difficulty="hard",
        query="Carta topográfica de Santa",
        answer_keywords=["santa"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY L: Conceitual (sem busca espacial)
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="L01", category="Conceitual", difficulty="easy",
        query="Qual a diferença entre MDS e MDT?",
        answer_keywords=["superfície", "terreno"],
    ),
    BenchmarkQuery(
        id="L02", category="Conceitual", difficulty="easy",
        query="O que é uma ortoimagem?",
        answer_keywords=["ortoimagem"],
    ),
    BenchmarkQuery(
        id="L03", category="Conceitual", difficulty="easy",
        query="O que é uma carta topográfica na escala 1:25.000?",
        answer_keywords=["topográfica"],
    ),
    BenchmarkQuery(
        id="L04", category="Conceitual", difficulty="easy",
        query="Me explica o que é MDS",
        answer_keywords=["superfície"],
    ),
    BenchmarkQuery(
        id="L05", category="Conceitual", difficulty="easy",
        query="Qual a diferença entre imagem de drone e imagem de satélite?",
        answer_keywords=["drone", "satélite"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY M: Buffer / Raio
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="M01", category="Buffer/Raio", difficulty="medium",
        query="Tudo que tiver num raio de 50km de Porto Alegre",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="M02", category="Buffer/Raio", difficulty="medium",
        query="Imagem de drone num raio de 5km de Itaipu",
        answer_keywords=["itaipu"],
        expected_product_ids=[5],
    ),
    BenchmarkQuery(
        id="M03", category="Buffer/Raio", difficulty="medium",
        query="Ortoimagens num raio de 10km de Santa Maria",
        answer_keywords=["santa maria"],
    ),
    BenchmarkQuery(
        id="M04", category="Buffer/Raio", difficulty="medium",
        query="Cartas topográficas próximas a Alecrim, num raio de 20km",
        answer_keywords=["alecrim"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY N: Combinada (multi-step)
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="N01", category="Combinada", difficulty="hard",
        query="Imagens de drone nas pontes da rota entre Santa Maria e Alegrete",
        answer_keywords=["ponte", "santa maria", "alegrete"],
    ),
    BenchmarkQuery(
        id="N02", category="Combinada", difficulty="hard",
        query="Ortoimagens ao longo do rio Jacuí, perto de Porto Alegre",
        answer_keywords=["jacuí"],
    ),
    BenchmarkQuery(
        id="N03", category="Combinada", difficulty="hard",
        query="Carta topográfica de melhor escala na fronteira com Uruguai",
        answer_keywords=["uruguai"],
    ),
    BenchmarkQuery(
        id="N04", category="Combinada", difficulty="hard",
        query="MDS mais recente da Serra Gaúcha",
        answer_keywords=["serra gaúcha"],
        expected_product_ids=[6],
    ),
    BenchmarkQuery(
        id="N05", category="Combinada", difficulty="hard",
        query="Cartas 25k mais novas num raio de 30km da 8ª Bda Inf Mec",
        answer_keywords=["8"],
    ),
    BenchmarkQuery(
        id="N06", category="Combinada", difficulty="hard",
        query="Imagens de satélite recentes da fronteira com Argentina perto de Porto Alegre",
        answer_keywords=["argentina"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY O: Formulações Variadas (mesma intenção, frases diferentes)
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="O01", category="Formulação Variada", difficulty="easy",
        query="Cartas de Alecrim",
        answer_keywords=["alecrim"],
        expected_product_ids=[1, 2, 3],
    ),
    BenchmarkQuery(
        id="O02", category="Formulação Variada", difficulty="easy",
        query="Existe mapeamento de Alecrim?",
        answer_keywords=["alecrim"],
    ),
    BenchmarkQuery(
        id="O03", category="Formulação Variada", difficulty="easy",
        query="Me mostra o que vocês têm de cartas para a região de Alecrim no RS",
        answer_keywords=["alecrim"],
    ),
    BenchmarkQuery(
        id="O04", category="Formulação Variada", difficulty="easy",
        query="Buscar cartas topográficas disponíveis no município de Alecrim, Rio Grande do Sul",
        answer_keywords=["alecrim"],
        expected_product_ids=[1, 2, 3],
    ),
    BenchmarkQuery(
        id="O05", category="Formulação Variada", difficulty="easy",
        query="carta 25k alecrim",
        answer_keywords=["alecrim", "25"],
        expected_product_ids=[1],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY P: Estado (busca por UF)
    # ═══════════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="P01", category="Estado", difficulty="medium",
        query="Ortoimagens disponíveis no Rio Grande do Sul",
        answer_keywords=["rio grande do sul"],
    ),
    BenchmarkQuery(
        id="P02", category="Estado", difficulty="medium",
        query="Cartas topográficas de São Paulo",
        answer_keywords=["são paulo"],
    ),
    BenchmarkQuery(
        id="P03", category="Estado", difficulty="medium",
        query="Que MDS tem no RS?",
        answer_keywords=["rio grande do sul"],
    ),
    BenchmarkQuery(
        id="P04", category="Estado", difficulty="medium",
        query="Imagens de satélite de SP",
        answer_keywords=["são paulo"],
    ),
]


def get_queries(category: str | None = None, difficulty: str | None = None) -> list[BenchmarkQuery]:
    queries = BENCHMARK_QUERIES
    if category:
        queries = [q for q in queries if q.category == category]
    if difficulty:
        queries = [q for q in queries if q.difficulty == difficulty]
    return queries


def get_categories() -> list[str]:
    return sorted(set(q.category for q in BENCHMARK_QUERIES))


def get_query_by_id(query_id: str) -> BenchmarkQuery | None:
    for q in BENCHMARK_QUERIES:
        if q.id == query_id:
            return q
    return None
