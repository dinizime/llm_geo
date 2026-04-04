"""Benchmark queries with result-based validation.

Each query defines what a CORRECT ANSWER looks like, not which tools to use.
The agent is free to choose any path -- we only check the final result.
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
    # NEW: Numeric range validation -- {metric: (min, max)}
    expected_numeric: dict[str, tuple[float, float]] = field(default_factory=dict)
    # NEW: Boolean predicate validation -- {predicate: expected_value}
    expected_boolean: dict[str, bool] = field(default_factory=dict)
    # NEW: Count range validation -- {feature_type: (min, max)}
    expected_count: dict[str, tuple[int, int]] = field(default_factory=dict)


BENCHMARK_QUERIES: list[BenchmarkQuery] = [
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY A: Localização Simples (topônimo → produto)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY B: Região Informal
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY C: Rota (produto)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY D: Filtro Temporal
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY E: Instalação Militar
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY F: Fronteira Internacional
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY G: Feições Geográficas
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY H: Hidrografia
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY I: Inventário
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY J: Escala
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY K: Desambiguação
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY L: Conceitual (sem busca espacial)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY M: Buffer / Raio (produto)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY N: Combinada (multi-step produto)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY O: Formulações Variadas (produto)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY P: Estado (busca por UF)
    # ═══════════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════
    # NEW CATEGORIES: SPATIAL REASONING (Q-AB)
    # ═══════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY Q: Planejamento de Rota
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="Q01", category="Planejamento de Rota", difficulty="medium",
        query="Quantas pontes tem na rota entre Alegrete e Rosário do Sul?",
        answer_keywords=["ponte", "alegrete", "rosário"],
        expected_count={"ponte": (1, 10)},
    ),
    BenchmarkQuery(
        id="Q02", category="Planejamento de Rota", difficulty="hard",
        query="Quais postos de combustível existem ao longo da BR-290?",
        answer_keywords=["posto", "BR-290"],
    ),
    BenchmarkQuery(
        id="Q03", category="Planejamento de Rota", difficulty="hard",
        query="A rota entre Porto Alegre e Pelotas passa por quantos municípios?",
        answer_keywords=["porto alegre", "pelotas"],
    ),
    BenchmarkQuery(
        id="Q04", category="Planejamento de Rota", difficulty="medium",
        query="Qual a distância por estrada entre Santa Maria e Alegrete?",
        answer_keywords=["santa maria", "alegrete", "km"],
        expected_numeric={"distance_km": (200, 350)},
    ),
    BenchmarkQuery(
        id="Q05", category="Planejamento de Rota", difficulty="medium",
        query="Qual a distância em linha reta de Porto Alegre a Uruguaiana?",
        answer_keywords=["porto alegre", "uruguaiana", "km"],
        expected_numeric={"distance_km": (450, 650)},
    ),
    BenchmarkQuery(
        id="Q06", category="Planejamento de Rota", difficulty="hard",
        query="Existe algum hospital ao longo da rota entre Alegrete e Uruguaiana?",
        answer_keywords=["hospital"],
    ),
    BenchmarkQuery(
        id="Q07", category="Planejamento de Rota", difficulty="hard",
        query="Quais pontes e túneis existem na rota entre Florianópolis e Porto Alegre?",
        answer_keywords=["ponte", "florianópolis", "porto alegre"],
    ),
    BenchmarkQuery(
        id="Q08", category="Planejamento de Rota", difficulty="medium",
        query="Qual o comprimento da rota rodoviária entre Santa Maria e Porto Alegre?",
        answer_keywords=["santa maria", "porto alegre", "km"],
    ),
    BenchmarkQuery(
        id="Q09", category="Planejamento de Rota", difficulty="hard",
        query="Preciso deslocar um comboio de Uruguaiana a Bagé. Quais são as pontes no caminho?",
        answer_keywords=["ponte", "uruguaiana", "bagé"],
    ),
    BenchmarkQuery(
        id="Q10", category="Planejamento de Rota", difficulty="hard",
        query="Na rota entre Santa Maria e São Borja, em que ponto cruza o Rio Ibicuí?",
        answer_keywords=["ibicuí"],
    ),
    BenchmarkQuery(
        id="Q11", category="Planejamento de Rota", difficulty="hard",
        query="Planejando deslocamento de tropa de Porto Alegre a Livramento. Qual a extensão da rota e quantas pontes vou cruzar?",
        answer_keywords=["livramento", "km"],
    ),
    BenchmarkQuery(
        id="Q12", category="Planejamento de Rota", difficulty="medium",
        query="Qual a distância de Alegrete a Santa Maria pela estrada?",
        answer_keywords=["alegrete", "santa maria", "km"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY R: Identificação de Obstáculos
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="R01", category="Identificação de Obstáculos", difficulty="medium",
        query="Quais são os obstáculos verticais num raio de 5 km de Uruguaiana?",
        answer_keywords=["uruguaiana"],
    ),
    BenchmarkQuery(
        id="R02", category="Identificação de Obstáculos", difficulty="hard",
        query="Existem torres de comunicação na aproximação do aeroporto de Santa Maria?",
        answer_keywords=["torre", "santa maria"],
    ),
    BenchmarkQuery(
        id="R03", category="Identificação de Obstáculos", difficulty="medium",
        query="Quantos aerogeradores existem no município de Osório?",
        answer_keywords=["aerogerador", "osório"],
        expected_count={"aerogerador": (1, 10)},
    ),
    BenchmarkQuery(
        id="R04", category="Identificação de Obstáculos", difficulty="hard",
        query="Linhas de transmissão que cruzam a rota entre Porto Alegre e Caxias do Sul",
        answer_keywords=["linha", "transmissão"],
    ),
    BenchmarkQuery(
        id="R05", category="Identificação de Obstáculos", difficulty="medium",
        query="Tem alguma torre de comunicação perto da 8ª Brigada?",
        answer_keywords=["torre", "brigada"],
    ),
    BenchmarkQuery(
        id="R06", category="Identificação de Obstáculos", difficulty="hard",
        query="Para um voo de helicóptero de Santa Maria a Alegrete, quais obstáculos verticais devo considerar?",
        answer_keywords=["santa maria", "alegrete"],
    ),
    BenchmarkQuery(
        id="R07", category="Identificação de Obstáculos", difficulty="medium",
        query="Existem aerogeradores num raio de 10km do aeroporto Salgado Filho?",
        answer_keywords=["aerogerador", "salgado filho"],
    ),
    BenchmarkQuery(
        id="R08", category="Identificação de Obstáculos", difficulty="hard",
        query="Qual a torre de comunicação mais alta no RS?",
        answer_keywords=["torre"],
    ),
    BenchmarkQuery(
        id="R09", category="Identificação de Obstáculos", difficulty="medium",
        query="Quantas torres de comunicação existem no município de Santa Maria?",
        answer_keywords=["torre", "santa maria"],
    ),
    BenchmarkQuery(
        id="R10", category="Identificação de Obstáculos", difficulty="hard",
        query="Mapeie todos os obstáculos à navegação aérea na região metropolitana de Porto Alegre",
        answer_keywords=["porto alegre"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY S: Infraestrutura e Serviços
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="S01", category="Infraestrutura", difficulty="easy",
        query="Quais são os hospitais de Santa Maria?",
        answer_keywords=["hospital", "santa maria"],
    ),
    BenchmarkQuery(
        id="S02", category="Infraestrutura", difficulty="medium",
        query="Quantas escolas existem no município de Alegrete?",
        answer_keywords=["escola", "alegrete"],
    ),
    BenchmarkQuery(
        id="S03", category="Infraestrutura", difficulty="medium",
        query="Qual o hospital mais próximo da 8ª Brigada de Infantaria Mecanizada?",
        answer_keywords=["hospital", "brigada"],
    ),
    BenchmarkQuery(
        id="S04", category="Infraestrutura", difficulty="medium",
        query="Postos de combustível num raio de 20km de Alegrete",
        answer_keywords=["posto", "alegrete"],
    ),
    BenchmarkQuery(
        id="S05", category="Infraestrutura", difficulty="hard",
        query="Quais são os aeroportos e campos de pouso no estado do RS?",
        answer_keywords=["aeroporto", "rio grande do sul"],
    ),
    BenchmarkQuery(
        id="S06", category="Infraestrutura", difficulty="medium",
        query="Existe heliporto em Santa Maria?",
        answer_keywords=["heliporto", "santa maria"],
    ),
    BenchmarkQuery(
        id="S07", category="Infraestrutura", difficulty="hard",
        query="Hospitais e escolas num raio de 10km da fronteira com o Uruguai perto de Jaguarão",
        answer_keywords=["hospital", "jaguarão"],
    ),
    BenchmarkQuery(
        id="S08", category="Infraestrutura", difficulty="easy",
        query="Quais aeroportos ficam perto de Porto Alegre?",
        answer_keywords=["aeroporto", "porto alegre"],
    ),
    BenchmarkQuery(
        id="S09", category="Infraestrutura", difficulty="hard",
        query="Quero um inventário completo de infraestrutura crítica de Uruguaiana: hospitais, escolas, postos de combustível e aeroportos",
        answer_keywords=["hospital", "uruguaiana"],
    ),
    BenchmarkQuery(
        id="S10", category="Infraestrutura", difficulty="medium",
        query="Qual o maior hospital de Santa Maria?",
        answer_keywords=["hospital", "santa maria"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY T: Resposta a Desastres
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="T01", category="Resposta a Desastres", difficulty="hard",
        query="Quais hospitais ficam a menos de 30km de Santa Maria? Preciso de apoio a operação de desastre.",
        answer_keywords=["hospital", "santa maria"],
    ),
    BenchmarkQuery(
        id="T02", category="Resposta a Desastres", difficulty="hard",
        query="Qual o aeroporto mais próximo de São Gabriel para evacuação aérea?",
        answer_keywords=["aeroporto", "são gabriel"],
    ),
    BenchmarkQuery(
        id="T03", category="Resposta a Desastres", difficulty="hard",
        query="Num raio de 50km de Cachoeira do Sul, quais heliportos e campos de pouso estão disponíveis?",
        answer_keywords=["cachoeira"],
    ),
    BenchmarkQuery(
        id="T04", category="Resposta a Desastres", difficulty="hard",
        query="Quais barragens existem a montante de Porto Alegre no Rio Jacuí?",
        answer_keywords=["barragem", "jacuí"],
    ),
    BenchmarkQuery(
        id="T05", category="Resposta a Desastres", difficulty="hard",
        query="Existem estações de tratamento de água vulneráveis na região de enchente do Rio Guaíba?",
        answer_keywords=["tratamento", "guaíba"],
    ),
    BenchmarkQuery(
        id="T06", category="Resposta a Desastres", difficulty="medium",
        query="Qual o hospital mais perto de Itaipu?",
        answer_keywords=["hospital", "itaipu"],
    ),
    BenchmarkQuery(
        id="T07", category="Resposta a Desastres", difficulty="hard",
        query="Preciso montar um posto de comando em Alegrete. Quais escolas posso usar num raio de 5km?",
        answer_keywords=["escola", "alegrete"],
    ),
    BenchmarkQuery(
        id="T08", category="Resposta a Desastres", difficulty="hard",
        query="Para apoio logístico em caso de enchente em Santa Maria, onde estão os postos de combustível e hospitais mais próximos?",
        answer_keywords=["hospital", "santa maria"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY U: Planejamento de Aviação
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="U01", category="Planejamento de Aviação", difficulty="medium",
        query="Quais aeroportos existem num raio de 100km de Santa Maria?",
        answer_keywords=["aeroporto", "santa maria"],
    ),
    BenchmarkQuery(
        id="U02", category="Planejamento de Aviação", difficulty="hard",
        query="Para pouso de helicóptero em Uruguaiana, onde fica o heliporto mais próximo?",
        answer_keywords=["heliporto", "uruguaiana"],
    ),
    BenchmarkQuery(
        id="U03", category="Planejamento de Aviação", difficulty="hard",
        query="Obstáculos verticais num raio de 15km do aeroporto de Bagé",
        answer_keywords=["bagé"],
    ),
    BenchmarkQuery(
        id="U04", category="Planejamento de Aviação", difficulty="medium",
        query="Quantos campos de pouso existem perto da fronteira com o Uruguai?",
        answer_keywords=["campo", "uruguai"],
    ),
    BenchmarkQuery(
        id="U05", category="Planejamento de Aviação", difficulty="hard",
        query="Preciso voar de Santa Maria a Alegrete. Quais torres e linhas de transmissão vou encontrar na rota?",
        answer_keywords=["torre", "santa maria", "alegrete"],
    ),
    BenchmarkQuery(
        id="U06", category="Planejamento de Aviação", difficulty="medium",
        query="Qual o aeroporto mais próximo da 8ª Brigada?",
        answer_keywords=["aeroporto", "brigada"],
    ),
    BenchmarkQuery(
        id="U07", category="Planejamento de Aviação", difficulty="medium",
        query="Distância do aeroporto Salgado Filho até o aeroporto de Santa Maria",
        answer_keywords=["salgado filho", "santa maria", "km"],
    ),
    BenchmarkQuery(
        id="U08", category="Planejamento de Aviação", difficulty="hard",
        query="Qual o aeroporto com maior pista no RS?",
        answer_keywords=["aeroporto"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY V: Hidrografia e Terreno
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="V01", category="Hidrografia e Terreno", difficulty="medium",
        query="Qual o comprimento do Rio Jacuí?",
        answer_keywords=["jacuí", "km"],
    ),
    BenchmarkQuery(
        id="V02", category="Hidrografia e Terreno", difficulty="hard",
        query="O Rio Ibicuí cruza o município de Alegrete?",
        answer_keywords=["ibicuí", "alegrete"],
        expected_boolean={"intersects": True},
    ),
    BenchmarkQuery(
        id="V03", category="Hidrografia e Terreno", difficulty="medium",
        query="Quantas pontes existem sobre o Rio Jacuí?",
        answer_keywords=["ponte", "jacuí"],
    ),
    BenchmarkQuery(
        id="V04", category="Hidrografia e Terreno", difficulty="hard",
        query="Quais barragens existem no Rio Jacuí e qual a distância entre elas?",
        answer_keywords=["barragem", "jacuí"],
    ),
    BenchmarkQuery(
        id="V05", category="Hidrografia e Terreno", difficulty="medium",
        query="Qual a área do município de Santa Maria?",
        answer_keywords=["santa maria", "km"],
    ),
    BenchmarkQuery(
        id="V06", category="Hidrografia e Terreno", difficulty="hard",
        query="Quais municípios o Rio Guaíba atravessa?",
        answer_keywords=["guaíba", "município"],
    ),
    BenchmarkQuery(
        id="V07", category="Hidrografia e Terreno", difficulty="medium",
        query="Qual a maior ponte de Santa Catarina?",
        answer_keywords=["ponte", "santa catarina"],
    ),
    BenchmarkQuery(
        id="V08", category="Hidrografia e Terreno", difficulty="medium",
        query="Qual o comprimento do Rio Guaíba?",
        answer_keywords=["guaíba", "km"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY W: Operações de Fronteira
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="W01", category="Operações de Fronteira", difficulty="medium",
        query="Qual a extensão da fronteira do Brasil com o Uruguai?",
        answer_keywords=["uruguai", "km"],
    ),
    BenchmarkQuery(
        id="W02", category="Operações de Fronteira", difficulty="hard",
        query="Quais municípios ficam na faixa de fronteira com a Argentina no RS?",
        answer_keywords=["argentina", "município"],
    ),
    BenchmarkQuery(
        id="W03", category="Operações de Fronteira", difficulty="hard",
        query="Existe algum campo de pouso perto da fronteira com o Uruguai na região de Jaguarão?",
        answer_keywords=["campo", "jaguarão"],
    ),
    BenchmarkQuery(
        id="W04", category="Operações de Fronteira", difficulty="medium",
        query="Quantas pontes internacionais existem na fronteira com a Argentina?",
        answer_keywords=["ponte", "argentina"],
    ),
    BenchmarkQuery(
        id="W05", category="Operações de Fronteira", difficulty="hard",
        query="Infraestrutura de saúde na faixa de fronteira com Uruguai: hospitais num raio de 30km da fronteira",
        answer_keywords=["hospital", "uruguai"],
    ),
    BenchmarkQuery(
        id="W06", category="Operações de Fronteira", difficulty="medium",
        query="Qual a distância de Porto Alegre até a fronteira com o Uruguai?",
        answer_keywords=["porto alegre", "uruguai", "km"],
    ),
    BenchmarkQuery(
        id="W07", category="Operações de Fronteira", difficulty="hard",
        query="Travessias de balsa na fronteira com a Argentina",
        answer_keywords=["balsa", "argentina"],
    ),
    BenchmarkQuery(
        id="W08", category="Operações de Fronteira", difficulty="hard",
        query="Quais postos de combustível ficam a menos de 50km da fronteira com o Uruguai?",
        answer_keywords=["posto", "uruguai"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY X: Rodovias e Infraestrutura Linear
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="X01", category="Rodovias", difficulty="medium",
        query="A BR-116 passa por quais municípios no RS?",
        answer_keywords=["BR-116", "município"],
    ),
    BenchmarkQuery(
        id="X02", category="Rodovias", difficulty="hard",
        query="Pontes ao longo da BR-290 entre Santa Maria e Uruguaiana",
        answer_keywords=["ponte", "BR-290"],
    ),
    BenchmarkQuery(
        id="X03", category="Rodovias", difficulty="medium",
        query="Qual o comprimento da BR-101 no trecho de Santa Catarina?",
        answer_keywords=["BR-101", "km"],
    ),
    BenchmarkQuery(
        id="X04", category="Rodovias", difficulty="hard",
        query="Existem estações ferroviárias ao longo da rota entre Porto Alegre e Santa Maria?",
        answer_keywords=["estação", "ferroviária"],
    ),
    BenchmarkQuery(
        id="X05", category="Rodovias", difficulty="hard",
        query="Cartas topográficas ao longo da BR-116 no RS",
        answer_keywords=["BR-116", "carta"],
    ),
    BenchmarkQuery(
        id="X06", category="Rodovias", difficulty="medium",
        query="A RS-040 cruza o município de Viamão?",
        answer_keywords=["RS-040", "viamão"],
        expected_boolean={"intersects": True},
    ),
    BenchmarkQuery(
        id="X07", category="Rodovias", difficulty="hard",
        query="Linhas de transmissão que cruzam a BR-290 no trecho de Santa Maria a Rosário do Sul",
        answer_keywords=["linha", "transmissão"],
    ),
    BenchmarkQuery(
        id="X08", category="Rodovias", difficulty="medium",
        query="Qual a distância rodoviária de Pelotas a Rio Grande?",
        answer_keywords=["pelotas", "rio grande", "km"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY Y: Instalações Militares Avançado
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="Y01", category="Militar Avançado", difficulty="medium",
        query="Qual a distância entre a 8ª Bda Inf Mec e o 3º BECmb?",
        answer_keywords=["km"],
    ),
    BenchmarkQuery(
        id="Y02", category="Militar Avançado", difficulty="hard",
        query="Quais hospitais ficam num raio de 20km do 3º BECmb em Cachoeira do Sul?",
        answer_keywords=["hospital", "cachoeira"],
    ),
    BenchmarkQuery(
        id="Y03", category="Militar Avançado", difficulty="hard",
        query="Campos de pouso num raio de 50km da 8ª Brigada para operação aeromóvel",
        answer_keywords=["campo", "brigada"],
    ),
    BenchmarkQuery(
        id="Y04", category="Militar Avançado", difficulty="hard",
        query="Postos de combustível na rota entre o 3º BECmb e a 8ª Bda Inf Mec",
        answer_keywords=["posto"],
    ),
    BenchmarkQuery(
        id="Y05", category="Militar Avançado", difficulty="medium",
        query="Qual a área de cobertura num raio de 30km da 8ª Brigada?",
        answer_keywords=["brigada", "km"],
    ),
    BenchmarkQuery(
        id="Y06", category="Militar Avançado", difficulty="hard",
        query="Pontes na rota entre Pelotas e Cachoeira do Sul para deslocamento de tropa de engenharia",
        answer_keywords=["ponte", "pelotas", "cachoeira"],
    ),
    BenchmarkQuery(
        id="Y07", category="Militar Avançado", difficulty="hard",
        query="Obstáculos verticais na área de treinamento da 8ª Brigada, num raio de 15km",
        answer_keywords=["brigada"],
    ),
    BenchmarkQuery(
        id="Y08", category="Militar Avançado", difficulty="medium",
        query="Quais municípios ficam num raio de 50km do 3º BECmb?",
        answer_keywords=["município", "cachoeira"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY Z: Multi-Step Complexo
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="Z01", category="Multi-Step Complexo", difficulty="hard",
        query="Quantas pontes tem na rota entre Alegrete e Rosário do Sul, e qual a mais próxima de Rosário?",
        answer_keywords=["ponte", "rosário"],
    ),
    BenchmarkQuery(
        id="Z02", category="Multi-Step Complexo", difficulty="hard",
        query="Quais hospitais ficam a menos de 10km de alguma ponte na rota entre Santa Maria e Alegrete?",
        answer_keywords=["hospital", "ponte"],
    ),
    BenchmarkQuery(
        id="Z03", category="Multi-Step Complexo", difficulty="hard",
        query="Carta topográfica de melhor escala para o trecho da fronteira com Argentina mais próximo de Porto Alegre",
        answer_keywords=["argentina", "carta"],
    ),
    BenchmarkQuery(
        id="Z04", category="Multi-Step Complexo", difficulty="hard",
        query="Ortoimagens mais recentes ao longo do Rio Jacuí, nos municípios de Cachoeira do Sul",
        answer_keywords=["ortoimagem", "jacuí"],
    ),
    BenchmarkQuery(
        id="Z05", category="Multi-Step Complexo", difficulty="hard",
        query="Existe cobertura cartográfica 25k na rota entre a 8ª Brigada e o 3º BECmb?",
        answer_keywords=["carta", "25"],
    ),
    BenchmarkQuery(
        id="Z06", category="Multi-Step Complexo", difficulty="hard",
        query="Quantos aeroportos e heliportos existem num raio de 100km da fronteira com Uruguai?",
        answer_keywords=["aeroporto", "uruguai"],
    ),
    BenchmarkQuery(
        id="Z07", category="Multi-Step Complexo", difficulty="hard",
        query="Qual a área total dos municípios cortados pela BR-290 no RS?",
        answer_keywords=["BR-290", "km"],
    ),
    BenchmarkQuery(
        id="Z08", category="Multi-Step Complexo", difficulty="hard",
        query="Imagens de drone disponíveis nas barragens do Rio Jacuí",
        answer_keywords=["drone", "barragem", "jacuí"],
    ),
    BenchmarkQuery(
        id="Z09", category="Multi-Step Complexo", difficulty="hard",
        query="Para operação na fronteira com Uruguai perto de Jaguarão, qual o hospital, aeroporto e posto de combustível mais próximos?",
        answer_keywords=["hospital", "aeroporto", "jaguarão"],
    ),
    BenchmarkQuery(
        id="Z10", category="Multi-Step Complexo", difficulty="hard",
        query="Qual a maior ponte na rota entre Porto Alegre e Santa Maria?",
        answer_keywords=["ponte"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY AA: Atributos e Superlativos
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="AA01", category="Atributos e Superlativos", difficulty="easy",
        query="Qual a população de Alegrete?",
        answer_keywords=["alegrete"],
    ),
    BenchmarkQuery(
        id="AA02", category="Atributos e Superlativos", difficulty="medium",
        query="Qual o município mais populoso do RS?",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="AA03", category="Atributos e Superlativos", difficulty="medium",
        query="Qual a ponte mais longa do Rio Grande do Sul?",
        answer_keywords=["ponte"],
    ),
    BenchmarkQuery(
        id="AA04", category="Atributos e Superlativos", difficulty="medium",
        query="Qual a maior edificação do Paraná?",
        answer_keywords=["paraná"],
    ),
    BenchmarkQuery(
        id="AA05", category="Atributos e Superlativos", difficulty="medium",
        query="Quantas terras indígenas tem no Rio Grande do Sul?",
        answer_keywords=["terra", "indígena"],
        expected_count={"terra_indigena": (2, 10)},
    ),
    BenchmarkQuery(
        id="AA06", category="Atributos e Superlativos", difficulty="medium",
        query="Qual a barragem mais alta do RS?",
        answer_keywords=["barragem"],
    ),
    BenchmarkQuery(
        id="AA07", category="Atributos e Superlativos", difficulty="medium",
        query="Qual a área do estado de São Paulo?",
        answer_keywords=["são paulo", "km"],
    ),
    BenchmarkQuery(
        id="AA08", category="Atributos e Superlativos", difficulty="easy",
        query="Qual a população de Porto Alegre?",
        answer_keywords=["porto alegre"],
    ),
    BenchmarkQuery(
        id="AA09", category="Atributos e Superlativos", difficulty="hard",
        query="Qual terra indígena do RS tem maior área?",
        answer_keywords=["terra", "indígena"],
    ),
    BenchmarkQuery(
        id="AA10", category="Atributos e Superlativos", difficulty="medium",
        query="Qual o aeroporto com maior pista no RS?",
        answer_keywords=["aeroporto"],
    ),

    # ═══════════════════════════════════════════════════════════════
    # CATEGORY AB: Formulação Natural Variada (espacial)
    # ═══════════════════════════════════════════════════════════════
    BenchmarkQuery(
        id="AB01", category="Formulação Natural", difficulty="easy",
        query="pontes perto de santa maria",
        answer_keywords=["ponte", "santa maria"],
    ),
    BenchmarkQuery(
        id="AB02", category="Formulação Natural", difficulty="easy",
        query="hospital mais perto de Alegrete",
        answer_keywords=["hospital", "alegrete"],
    ),
    BenchmarkQuery(
        id="AB03", category="Formulação Natural", difficulty="medium",
        query="Me diz as torres de celular de Uruguaiana",
        answer_keywords=["torre", "uruguaiana"],
    ),
    BenchmarkQuery(
        id="AB04", category="Formulação Natural", difficulty="easy",
        query="tem aeroporto em Santa Maria?",
        answer_keywords=["aeroporto", "santa maria"],
    ),
    BenchmarkQuery(
        id="AB05", category="Formulação Natural", difficulty="medium",
        query="distância POA até SM",
        answer_keywords=["km"],
    ),
    BenchmarkQuery(
        id="AB06", category="Formulação Natural", difficulty="medium",
        query="quanto mede o rio Guaíba?",
        answer_keywords=["guaíba", "km"],
    ),
    BenchmarkQuery(
        id="AB07", category="Formulação Natural", difficulty="easy",
        query="área de Porto Alegre",
        answer_keywords=["porto alegre", "km"],
    ),
    BenchmarkQuery(
        id="AB08", category="Formulação Natural", difficulty="medium",
        query="de Santa Maria a Alegrete tem alguma ponte?",
        answer_keywords=["ponte"],
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
