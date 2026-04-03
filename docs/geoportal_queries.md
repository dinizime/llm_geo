# Geoportal - Busca Inteligente: Catálogo de Perguntas e Fluxos de Resolução

## Visão Geral das Tools Disponíveis

| Tool | Descrição |
|---|---|
| `geocode` | Resolve topônimo/endereço em coordenadas (ponto) |
| `search_municipality` | Retorna geometria (polígono) de um município pelo nome |
| `search_state` | Retorna geometria de uma UF |
| `search_named_region` | Retorna geometria de regiões informais (Serra Gaúcha, Litoral Norte, Pampa, etc.) |
| `search_border` | Retorna geometria de trecho de fronteira internacional (linha) |
| `search_coastline` | Retorna geometria da linha de costa de uma UF ou trecho |
| `search_products` | Busca produtos no catálogo por tipo, geometria, escala, data, etc. |
| `rank_by_scale` | Ordena produtos pela melhor (maior) escala disponível |
| `rank_by_date` | Ordena produtos por data (mais novo ou mais antigo) |
| `compute_route` | Calcula rota rodoviária entre dois pontos (retorna LineString) |
| `buffer` | Gera área de influência (polígono) ao redor de uma geometria |
| `search_features` | Busca feições geográficas (pontes, barragens, aeroportos, portos...) dentro de uma área |
| `search_hydrography` | Busca rios, lagos, bacias hidrográficas por nome |
| `search_military_installation` | Busca OM (Organização Militar) pelo nome, sigla ou tipo |
| `search_infrastructure` | Busca rodovias, ferrovias, linhas de transmissão por identificador |
| `search_conservation_unit` | Busca UCs (parques, reservas, APAs) por nome |
| `search_indigenous_land` | Busca terras indígenas por nome |
| `intersect` | Retorna interseção entre duas geometrias |
| `get_elevation_range` | Consulta faixa de elevação dentro de uma geometria |
| `filter_by_elevation` | Filtra área mantendo apenas regiões acima/abaixo de cota X |
| `get_product_coverage` | Dado um produto, retorna seu footprint/articulação |
| `explain_product_type` | Retorna descrição de um tipo de produto para desambiguação |
| `autocomplete_placename` | Sugere topônimos a partir de fragmento (ex: "santa" -> Santa Maria, Santa Cruz...) |

---

## Categorias de Perguntas

### Categoria A: Localização Simples (topônimo direto)

> O usuário cita um lugar específico que pode ser geocodificado diretamente.

---

**P01 - Cartas topográficas de melhor escala possível em Alecrim**

Intenção: produto de tipo específico + melhor escala + localização pontual (município pequeno).

```
1. geocode("Alecrim, RS")                        → ponto (-27.66, -54.73)
2. search_municipality("Alecrim", "RS")           → polígono do município
3. search_products(
     tipo="carta_topografica",
     geometry=polígono_alecrim
   )                                              → lista de cartas (25k, 50k, 100k, 250k...)
4. rank_by_scale(produtos, order="best_first")     → ordena pela escala mais detalhada
5. Retorna: melhores cartas com escala, articulação, ano e link de download
```

Notas de orquestração:
- Não sabemos a priori se existe 25k em Alecrim, então buscamos tudo e ranqueamos.
- Se houver múltiplas cartas na mesma escala, desempatar por data (mais recente).

---

**P02 - Imagem de drone de Itaipu**

Intenção: produto específico + POI (infraestrutura conhecida).

```
1. geocode("Usina Hidrelétrica de Itaipu")        → ponto (-25.41, -54.59)
2. buffer(ponto_itaipu, raio=5000m)                → polígono de busca
3. search_products(
     tipo="imagem_drone",
     geometry=buffer_itaipu
   )                                              → lista de imagens de drone
4. Retorna: imagens encontradas com data, resolução, preview
```

Notas:
- "Itaipu" é uma infraestrutura, não um município. O geocode precisa resolver como POI.
- Buffer necessário porque imagens de drone são levantamentos locais com footprint pequeno.

---

**P03 - Modelos 3D de Brasília**

Intenção: produto raro + cidade grande.

```
1. search_municipality("Brasília", "DF")           → polígono
2. search_products(
     tipo="modelo_3d",
     geometry=polígono_brasilia
   )                                              → lista (possivelmente vazia)
3. SE vazio:
     search_products(
       tipo=["modelo_3d", "nuvem_pontos", "mesh_3d"],
       geometry=polígono_brasilia
     )                                            → busca tipos correlatos
4. Retorna: resultados ou mensagem "nenhum modelo 3D disponível, mas existem MDS/nuvem de pontos"
```

Notas:
- Modelos 3D são raros. Importante ter fallback para produtos relacionados.
- Desambiguação de tipo: modelo 3D pode ser mesh, nuvem de pontos, CityGML, etc.

---

### Categoria B: Região Informal (não é município nem UF)

> O usuário referencia uma região geográfica que não corresponde a uma divisão administrativa exata.

---

**P04 - Ortoimagens no litoral do Rio Grande do Sul**

Intenção: produto comum + região natural (faixa costeira).

```
1. search_state("RS")                             → polígono do RS
2. search_coastline(uf="RS")                       → linha de costa
3. buffer(linha_costa_rs, raio=20000m)             → faixa costeira de 20km
4. intersect(buffer_costa, polígono_rs)            → recorta para ficar só dentro do RS
5. search_products(
     tipo="ortoimagem",
     geometry=faixa_costeira_rs
   )                                              → lista de ortoimagens
6. Retorna: ortoimagens com data, resolução, articulação
```

Notas:
- "Litoral" precisa ser interpretado como faixa costeira, não como município "Litoral".
- A largura do buffer é uma decisão do planejador (10-30km é razoável para litoral).

---

**P05 - MDS da Serra Gaúcha**

Intenção: produto de elevação + região informal.

```
1. search_named_region("Serra Gaúcha")             → polígono aproximado
2. search_products(
     tipo="mds",
     geometry=polígono_serra_gaucha
   )                                              → lista de MDS
3. Retorna: MDS disponíveis com resolução, data, fonte (LiDAR, radar, fotogramétrico)
```

Notas:
- "Serra Gaúcha" não tem limite oficial. A tool `search_named_region` precisa de um cadastro curado de regiões informais.
- Alternativa: usar filtro de elevação sobre o RS para obter áreas serranas.

---

**P06 - MDT do Pantanal**

Intenção: produto de elevação + bioma/região natural.

```
1. search_named_region("Pantanal")                 → polígono do bioma/região
2. search_products(
     tipo="mdt",
     geometry=polígono_pantanal
   )                                              → lista de MDT
3. rank_by_date(produtos, order="newest_first")
4. Retorna: MDTs com resolução e cobertura
```

---

**P07 - Ortoimagens da tríplice fronteira**

Intenção: produto + região geopolítica informal.

```
1. geocode("Tríplice Fronteira Brasil Argentina Paraguai")  → ponto (~Foz do Iguaçu)
2. buffer(ponto, raio=30000m)                               → área da região
3. intersect(buffer, fronteira_brasil)                       → recorta para território nacional
4. search_products(
     tipo="ortoimagem",
     geometry=area_triplice
   )
5. Retorna: ortoimagens disponíveis
```

---

### Categoria C: Consulta com Rota

> O usuário quer produtos ao longo de um trajeto entre dois pontos.

---

**P08 - Imagens de drone nas pontes da rota entre Santa Maria e Alegrete**

Intenção: produto + feições específicas (pontes) + ao longo de uma rota.

```
1. geocode("Santa Maria, RS")                     → ponto_origem
2. geocode("Alegrete, RS")                         → ponto_destino
3. compute_route(ponto_origem, ponto_destino)      → LineString da rota (~BR-290)
4. buffer(rota, raio=500m)                         → corredor ao longo da rota
5. search_features(
     tipo="ponte",
     geometry=corredor_rota
   )                                              → lista de pontes com localização
6. PARA CADA ponte:
     buffer(ponto_ponte, raio=1000m)
     search_products(
       tipo="imagem_drone",
       geometry=buffer_ponte
     )
7. Retorna: mapa da rota com pontes marcadas + imagens de drone disponíveis por ponte
```

Notas:
- Essa é uma das consultas mais complexas: 7 steps, iteração sobre feições.
- Se não houver imagem de drone em nenhuma ponte, sugerir ortoimagens como alternativa.

---

**P09 - Cartas topográficas ao longo da BR-101 entre Florianópolis e Porto Alegre**

Intenção: cobertura cartográfica de um eixo rodoviário.

```
1. geocode("Florianópolis, SC")                    → ponto_origem
2. geocode("Porto Alegre, RS")                     → ponto_destino
3. compute_route(ponto_origem, ponto_destino)      → rota pela BR-101
4. buffer(rota, raio=5000m)                        → corredor de 5km
5. search_products(
     tipo="carta_topografica",
     geometry=corredor
   )                                              → lista de cartas
6. rank_by_scale(produtos, order="best_first")
7. Retorna: articulação de cartas que cobrem o trajeto
```

---

**P10 - MDS ao longo do rio Jacuí, de Dona Francisca até o Guaíba**

Intenção: produto ao longo de feição hidrográfica.

```
1. search_hydrography("Rio Jacuí")                 → LineString do rio
2. geocode("Dona Francisca, RS")                   → ponto_inicio
3. geocode("Lago Guaíba")                          → ponto_fim
4. clip_line(rio_jacui, ponto_inicio, ponto_fim)   → trecho do rio
5. buffer(trecho_rio, raio=3000m)                  → corredor fluvial
6. search_products(
     tipo="mds",
     geometry=corredor_fluvial
   )
7. Retorna: MDS disponíveis ao longo do trecho
```

---

### Categoria D: Filtro Temporal

> O usuário quer os produtos mais novos, mais antigos, ou de um período específico.

---

**P11 - Cartas 25k mais novas de Santa Maria**

Intenção: produto + escala fixa + filtro temporal + topônimo truncado ("santa" = ambíguo).

```
1. autocomplete_placename("santa")                 → [Santa Maria, Santa Cruz do Sul, Santa Rosa, Santana do Livramento...]
   DECISÃO: contexto "cartas 25k" + RS = provavelmente Santa Maria (maior cidade militar do RS)
   SE ambíguo: perguntar ao usuário
2. search_municipality("Santa Maria", "RS")        → polígono
3. search_products(
     tipo="carta_topografica",
     escala="1:25.000",
     geometry=polígono_santa_maria
   )                                              → lista de cartas 25k
4. rank_by_date(produtos, order="newest_first")
5. Retorna: cartas 25k ordenadas por data de publicação
```

Notas:
- "santa" é truncado e altamente ambíguo. A tool `autocomplete_placename` é essencial.
- Heurística de desambiguação: se o perfil do usuário é militar e está no RS, Santa Maria é provável.

---

**P12 - Ortoimagens de Porto Alegre entre 2020 e 2023**

Intenção: produto + município + intervalo de datas.

```
1. search_municipality("Porto Alegre", "RS")       → polígono
2. search_products(
     tipo="ortoimagem",
     geometry=polígono_poa,
     data_inicio="2020-01-01",
     data_fim="2023-12-31"
   )
3. rank_by_date(produtos, order="newest_first")
4. Retorna: ortoimagens do período
```

---

**P13 - Produto mais recente de qualquer tipo sobre Manaus**

Intenção: qualquer produto + cidade + mais recente.

```
1. search_municipality("Manaus", "AM")             → polígono
2. search_products(
     tipo="*",
     geometry=polígono_manaus
   )                                              → todos os produtos
3. rank_by_date(produtos, order="newest_first")
4. Retorna: produto mais recente independente do tipo
```

---

### Categoria E: Referência Militar / Instalação

> O usuário referencia uma OM, brigada, batalhão ou instalação militar.

---

**P14 - Carta 50k que pegue a 8ª Bda Inf Mec**

Intenção: produto + escala + localização de OM.

```
1. search_military_installation("8ª Brigada de Infantaria Mecanizada")
                                                   → ponto em Pelotas, RS
2. buffer(ponto_8bda, raio=2000m)                  → área da OM
3. search_products(
     tipo="carta_topografica",
     escala="1:50.000",
     geometry=buffer_8bda
   )                                              → cartas 50k que intersectam
4. Retorna: carta(s) 50k com nomenclatura (ex: SH-22-Y-C-V-2)
```

Notas:
- "8 bda inf mec" é abreviação militar. A tool precisa entender siglas de OM.
- A OM pode estar entre duas folhas de carta. Retornar todas que intersectam.

---

**P15 - MDS num raio de 15km do 3º BPE em Cachoeira do Sul**

Intenção: produto + buffer + OM.

```
1. search_military_installation("3º Batalhão de Engenharia de Combate", "Cachoeira do Sul")
                                                   → ponto
2. buffer(ponto_3bpec, raio=15000m)                → polígono circular
3. search_products(
     tipo="mds",
     geometry=buffer_15km
   )
4. Retorna: MDS disponíveis na área
```

---

**P16 - Todos os produtos disponíveis no Campo de Instrução de Santa Maria**

Intenção: todos os tipos + instalação militar.

```
1. search_military_installation("CISM", tipo="campo_instrucao")
                                                   → polígono (ou ponto + buffer grande)
2. search_products(
     tipo="*",
     geometry=polígono_cism
   )
3. Retorna: inventário completo por tipo de produto
```

---

### Categoria F: Fronteira Internacional

> O usuário quer produtos em áreas de fronteira.

---

**P17 - Imagem de satélite da fronteira com Uruguai**

Intenção: produto de satélite + fronteira inteira com um país.

```
1. search_border(pais1="Brasil", pais2="Uruguai")  → LineString da fronteira
2. buffer(linha_fronteira, raio=10000m)            → faixa de fronteira
3. intersect(faixa, territorio_brasil)             → recorta lado brasileiro
4. search_products(
     tipo="imagem_satelite",
     geometry=faixa_fronteira_br
   )
5. Retorna: imagens de satélite ao longo da fronteira
```

Notas:
- A fronteira com Uruguai é extensa (~1000km). Possivelmente retorna muitos produtos.
- Pode ser necessário paginar ou agrupar por setor (Chuí, Jaguarão, Quaraí, etc.).

---

**P18 - Ortoimagens da fronteira seca entre Livramento e Rivera**

Intenção: produto + trecho específico de fronteira.

```
1. geocode("Santana do Livramento, RS")            → ponto
2. geocode("Rivera, Uruguai")                      → ponto
3. search_border(pais1="Brasil", pais2="Uruguai",
                 proximidade=ponto_livramento)      → trecho de fronteira local
4. buffer(trecho_fronteira, raio=5000m)
5. intersect(buffer, territorio_brasil)
6. search_products(
     tipo="ortoimagem",
     geometry=area_busca
   )
7. Retorna: ortoimagens da conurbação Livramento-Rivera
```

---

**P19 - Cartas topográficas da faixa de fronteira do Amapá com a Guiana Francesa**

```
1. search_state("AP")                              → polígono Amapá
2. search_border(pais1="Brasil", pais2="Guiana Francesa") → linha fronteira
3. buffer(fronteira, raio=150000m)                 → faixa de 150km (faixa de fronteira legal)
4. intersect(buffer, polígono_ap)                  → área dentro do AP
5. search_products(
     tipo="carta_topografica",
     geometry=area_faixa
   )
6. rank_by_scale(produtos, order="best_first")
7. Retorna: cartas disponíveis na faixa de fronteira
```

---

### Categoria G: Feições Geográficas Específicas

> O usuário busca produtos sobre tipos de feição (rios, barragens, aeroportos, etc.).

---

**P20 - Imagens de drone de barragens no rio Taquari**

Intenção: produto + feição (barragens) + feição (rio).

```
1. search_hydrography("Rio Taquari", uf="RS")      → LineString do rio
2. buffer(rio_taquari, raio=2000m)                 → corredor do rio
3. search_features(
     tipo="barragem",
     geometry=corredor_taquari
   )                                              → lista de barragens
4. PARA CADA barragem:
     buffer(ponto_barragem, raio=2000m)
     search_products(tipo="imagem_drone", geometry=buffer)
5. Retorna: barragens com indicação de disponibilidade de imagens de drone
```

---

**P21 - Ortoimagens de aeroportos no Mato Grosso**

```
1. search_state("MT")                              → polígono
2. search_features(
     tipo="aeroporto",
     geometry=polígono_mt
   )                                              → lista de aeroportos
3. PARA CADA aeroporto:
     buffer(ponto_aeroporto, raio=5000m)
     search_products(tipo="ortoimagem", geometry=buffer)
4. Retorna: cobertura de ortoimagem por aeroporto
```

---

**P22 - MDT das áreas alagáveis do rio Guaíba**

```
1. search_hydrography("Rio Guaíba")                → geometria
2. buffer(rio_guaiba, raio=5000m)                  → área ribeirinha
3. filter_by_elevation(area_ribeirinha, max=10m)   → áreas baixas (alagáveis)
4. search_products(
     tipo="mdt",
     geometry=areas_alagaveis
   )
5. Retorna: MDTs que cobrem áreas de risco de alagamento
```

---

**P23 - Imagens de satélite dos reservatórios da bacia do São Francisco**

```
1. search_hydrography("Bacia do São Francisco", tipo="bacia") → polígono da bacia
2. search_features(
     tipo="reservatorio",
     geometry=bacia_sf
   )                                              → lista de reservatórios
3. PARA CADA reservatório:
     search_products(tipo="imagem_satelite", geometry=reservatorio.geometry)
4. Retorna: cobertura por reservatório
```

---

### Categoria H: Unidades de Conservação e Terras Especiais

> Busca por produtos em áreas protegidas.

---

**P24 - MDS do Parque Nacional de Aparados da Serra**

```
1. search_conservation_unit("Parque Nacional de Aparados da Serra")
                                                   → polígono da UC
2. search_products(
     tipo="mds",
     geometry=polígono_uc
   )
3. Retorna: MDS disponíveis dentro do parque
```

---

**P25 - Ortoimagens da Terra Indígena Raposa Serra do Sol**

```
1. search_indigenous_land("Raposa Serra do Sol")   → polígono da TI
2. search_products(
     tipo="ortoimagem",
     geometry=polígono_ti
   )
3. Retorna: ortoimagens disponíveis
```

---

**P26 - Carta topográfica da APA da Baleia Franca**

```
1. search_conservation_unit("APA da Baleia Franca") → polígono
2. search_products(
     tipo="carta_topografica",
     geometry=polígono_apa
   )
3. rank_by_scale(produtos, order="best_first")
4. Retorna: cartas disponíveis
```

---

### Categoria I: Cobertura Completa / Inventário

> O usuário quer saber "o que tem" numa região, sem especificar tipo.

---

**P27 - Que produtos existem para o município de São Gabriel?**

```
1. search_municipality("São Gabriel", "RS")        → polígono
2. search_products(
     tipo="*",
     geometry=polígono_sg
   )
3. AGRUPAR por tipo de produto
4. Retorna: inventário → "3 ortoimagens, 2 cartas 50k, 1 carta 25k, 1 MDS..."
```

---

**P28 - Qual a melhor cobertura cartográfica da região do Araguaia?**

```
1. search_named_region("Araguaia")                 → polígono
   OU search_hydrography("Rio Araguaia") + buffer
2. search_products(tipo="*", geometry=polígono)
3. PARA CADA tipo: calcular percentual de cobertura sobre a área
4. Retorna: relatório de cobertura (ex: "carta 250k: 100%, carta 100k: 60%, ortoimagem: 15%")
```

---

### Categoria J: Rodovias e Infraestrutura Linear

> O usuário referencia estradas, ferrovias, dutos, etc.

---

**P29 - Ortoimagens ao longo da BR-116 no trecho do RS**

```
1. search_infrastructure(tipo="rodovia", id="BR-116")   → LineString completa
2. search_state("RS")                                    → polígono RS
3. intersect(br116, polígono_rs)                         → trecho gaúcho
4. buffer(trecho_rs, raio=3000m)                         → corredor
5. search_products(tipo="ortoimagem", geometry=corredor)
6. Retorna: ortoimagens ao longo da BR-116 no RS
```

---

**P30 - MDS do traçado da ferrovia Bioceânica entre Maracaju e Porto Murtinho**

```
1. geocode("Maracaju, MS")
2. geocode("Porto Murtinho, MS")
3. search_infrastructure(tipo="ferrovia", nome="Bioceânica")
   SE não encontrada: compute_route(maracaju, porto_murtinho)
4. buffer(traçado, raio=5000m)
5. search_products(tipo="mds", geometry=corredor)
6. Retorna: MDS ao longo do eixo
```

---

**P31 - Imagens de drone das pontes da ferrovia Carajás**

```
1. search_infrastructure(tipo="ferrovia", nome="Estrada de Ferro Carajás")
                                                   → LineString
2. buffer(ferrovia, raio=500m)                     → corredor estreito
3. search_features(tipo="ponte", geometry=corredor)
4. PARA CADA ponte:
     buffer(ponte, raio=1000m)
     search_products(tipo="imagem_drone", geometry=buffer)
5. Retorna: pontes ferroviárias com disponibilidade de imagens de drone
```

---

### Categoria K: Consulta por Articulação / Nomenclatura de Folha

> O usuário sabe o código da folha cartográfica.

---

**P32 - Tem carta 25k na folha SH-22-Y-C-V-2?**

```
1. get_product_coverage(articulacao="SH-22-Y-C-V-2", escala="1:25.000")
                                                   → metadados da folha
2. Retorna: se existe, data de publicação, status (publicada, em produção, planejada)
```

Notas:
- Consulta direta sem geocoding. O usuário já sabe a nomenclatura.

---

**P33 - Quais folhas 50k cobrem a folha 250k SH-22?**

```
1. get_product_coverage(articulacao="SH-22", escala="1:250.000")
                                                   → polígono da folha
2. search_products(
     tipo="carta_topografica",
     escala="1:50.000",
     geometry=polígono_sh22
   )
3. Retorna: lista de todas as folhas 50k dentro da articulação SH-22
```

---

### Categoria L: Consultas com Critério de Elevação

> O usuário quer produtos filtrados por altitude.

---

**P34 - MDT de áreas acima de 1000m no Paraná**

```
1. search_state("PR")                              → polígono
2. filter_by_elevation(polígono_pr, min=1000m)     → áreas acima de 1000m
3. search_products(
     tipo="mdt",
     geometry=areas_altas
   )
4. Retorna: MDTs disponíveis nas áreas elevadas
```

---

**P35 - Ortoimagens de planícies alagáveis abaixo de 5m no litoral de SP**

```
1. search_state("SP")                              → polígono
2. search_coastline(uf="SP")                       → costa
3. buffer(costa, raio=20000m)                      → faixa costeira
4. intersect(faixa_costeira, polígono_sp)          → litoral paulista
5. filter_by_elevation(litoral_sp, max=5m)         → planícies baixas
6. search_products(tipo="ortoimagem", geometry=planícies)
7. Retorna: ortoimagens das áreas de risco costeiro
```

---

### Categoria M: Comparação Temporal / Multitemporal

> O usuário quer comparar produtos de datas diferentes sobre a mesma área.

---

**P36 - Comparar ortoimagens de antes e depois da enchente de 2024 no Vale do Taquari**

```
1. search_named_region("Vale do Taquari")          → polígono
2. search_products(
     tipo="ortoimagem",
     geometry=vale_taquari,
     data_fim="2024-04-30"
   )                                              → imagens "antes"
3. search_products(
     tipo="ortoimagem",
     geometry=vale_taquari,
     data_inicio="2024-05-01"
   )                                              → imagens "depois"
4. Retorna: pares de imagens pré/pós evento para comparação
```

---

**P37 - Evolução da mancha urbana de Goiânia: imagens de 2010, 2015 e 2020**

```
1. search_municipality("Goiânia", "GO")            → polígono
2. search_products(tipo="ortoimagem", geometry=goiania, data_inicio="2009-06-01", data_fim="2010-12-31")
3. search_products(tipo="ortoimagem", geometry=goiania, data_inicio="2014-06-01", data_fim="2015-12-31")
4. search_products(tipo="ortoimagem", geometry=goiania, data_inicio="2019-06-01", data_fim="2020-12-31")
5. Retorna: série temporal de ortoimagens
```

---

### Categoria N: Desambiguação Necessária

> A pergunta é ambígua e precisa de interação com o usuário.

---

**P38 - Carta de Santa Cruz**

Problema: qual Santa Cruz? Santa Cruz do Sul (RS)? Santa Cruz do Capibaribe (PE)? Santa Cruz (RN)?

```
1. autocomplete_placename("Santa Cruz")            → lista de candidatos
2. PERGUNTAR ao usuário: "Você se refere a qual localidade?"
   - Santa Cruz do Sul, RS
   - Santa Cruz, RN
   - Santa Cruz do Capibaribe, PE
   - Outra...
3. Após resposta: search_municipality(escolha)     → polígono
4. search_products(tipo="carta_topografica", geometry=polígono)
5. rank_by_scale(produtos, order="best_first")
6. Retorna: cartas disponíveis
```

---

**P39 - Mapa de São José**

Problemas: qual São José? + o que é "mapa"?

```
1. autocomplete_placename("São José")              → 20+ candidatos
2. explain_product_type("mapa")                    → pode ser carta, ortoimagem, etc.
3. PERGUNTAR ao usuário:
   a) "Qual São José?" (listar top 5 por população)
   b) "Que tipo de produto? Carta topográfica, ortoimagem, outro?"
4. Após respostas: resolver normalmente
```

---

**P40 - Imagem do rio**

Problema: qual rio? Qual tipo de imagem?

```
1. PERGUNTAR:
   a) "Qual rio você está buscando?"
   b) "Imagem de satélite, drone, ou ortoimagem?"
2. Após respostas: search_hydrography + search_products
```

---

### Categoria O: Consulta Negativa / Lacuna de Cobertura

> O usuário quer saber onde NÃO tem cobertura.

---

**P41 - Onde falta carta 25k no Rio Grande do Sul?**

```
1. search_state("RS")                              → polígono
2. search_products(
     tipo="carta_topografica",
     escala="1:25.000",
     geometry=polígono_rs
   )                                              → lista de cartas
3. PARA CADA carta: get_product_coverage → footprints
4. UNIR footprints → polígono de cobertura
5. DIFERENÇA(polígono_rs, cobertura)               → áreas sem carta 25k
6. Retorna: mapa de lacunas + lista de folhas faltantes
```

---

**P42 - Tem MDS LiDAR em algum lugar da Amazônia?**

```
1. search_named_region("Amazônia Legal")           → polígono
2. search_products(
     tipo="mds",
     fonte="lidar",
     geometry=polígono_amazonia
   )
3. SE vazio: Retorna "Não há MDS LiDAR na Amazônia"
   SE encontrou: Retorna localização e metadados
```

---

### Categoria P: Consulta por Proximidade / Raio

> O usuário quer produtos num raio específico.

---

**P43 - Tudo que tiver num raio de 50km de Uruguaiana**

```
1. geocode("Uruguaiana, RS")                       → ponto
2. buffer(ponto, raio=50000m)                      → círculo
3. search_products(tipo="*", geometry=circulo)
4. AGRUPAR por tipo
5. Retorna: inventário completo no raio
```

---

**P44 - Imagem de satélite mais recente num raio de 100km de Boa Vista, RR**

```
1. geocode("Boa Vista, RR")                        → ponto
2. buffer(ponto, raio=100000m)                     → círculo
3. search_products(tipo="imagem_satelite", geometry=circulo)
4. rank_by_date(produtos, order="newest_first")
5. Retorna: imagem mais recente
```

---

### Categoria Q: Consulta Multiestado / Nacional

> A busca abrange mais de uma UF ou todo o território.

---

**P45 - Cobertura de carta 100k de toda a faixa de fronteira terrestre do Brasil**

```
1. search_border(pais1="Brasil", pais2="*")        → todas as fronteiras terrestres
2. buffer(fronteiras, raio=150000m)                → faixa de 150km
3. intersect(buffer, territorio_brasil)            → faixa de fronteira legal
4. search_products(tipo="carta_topografica", escala="1:100.000", geometry=faixa)
5. calcular_cobertura_percentual(faixa, produtos)
6. Retorna: percentual de cobertura + mapa de lacunas
```

---

**P46 - MDS de todas as capitais estaduais**

```
1. PARA CADA UF brasileira:
     search_municipality(capital_da_uf)            → polígono
     search_products(tipo="mds", geometry=polígono)
2. AGRUPAR por capital
3. Retorna: disponibilidade de MDS por capital
```

---

### Categoria R: Pergunta sobre o Produto (não busca)

> O usuário não quer buscar, quer entender o que é um produto.

---

**P47 - Qual a diferença entre MDS e MDT?**

```
1. explain_product_type("mds")                     → definição
2. explain_product_type("mdt")                     → definição
3. Retorna: explicação comparativa (MDS inclui construções e vegetação, MDT é terreno nu)
```

Notas:
- Nenhuma busca geoespacial necessária. Apenas recuperação de metadados.

---

**P48 - O que é uma carta na escala 1:25.000?**

```
1. explain_product_type("carta_topografica", escala="1:25.000")
2. Retorna: explicação (cobertura da folha, nível de detalhe, equidistância de curvas, etc.)
```

---

## Resumo: Padrões de Tool Calling

| Padrão | Descrição | Exemplos |
|---|---|---|
| **Geocode + Search** | Resolve lugar, busca produto | P01, P02, P03 |
| **Região Informal + Search** | Resolve região sem limites oficiais | P04, P05, P06, P07 |
| **Rota + Buffer + Feature + Search** | Calcula trajeto, busca feições ao longo | P08, P09, P10 |
| **Temporal Ranking** | Busca com ordenação por data | P11, P12, P13 |
| **OM / Instalação Militar** | Resolve sigla/nome de OM | P14, P15, P16 |
| **Fronteira + Buffer + Clip** | Busca ao longo de fronteira | P17, P18, P19 |
| **Feature Search + Iteração** | Busca feições, depois produto por feição | P20, P21, P22, P23 |
| **UC / TI Lookup** | Resolve área protegida | P24, P25, P26 |
| **Inventário Completo** | Busca todos os tipos na área | P27, P28 |
| **Infraestrutura Linear** | Resolve rodovia/ferrovia + corredor | P29, P30, P31 |
| **Articulação Direta** | Usuário sabe o código da folha | P32, P33 |
| **Filtro de Elevação** | Restrição por altitude | P34, P35 |
| **Multitemporal** | Comparação entre datas | P36, P37 |
| **Desambiguação** | Topônimo ambíguo, interação necessária | P38, P39, P40 |
| **Lacuna / Negativa** | Onde NÃO tem produto | P41, P42 |
| **Raio / Proximidade** | Buffer circular a partir de ponto | P43, P44 |
| **Nacional / Multiestado** | Abrangência grande, iteração por UF | P45, P46 |
| **Explicação** | Pergunta conceitual, sem busca espacial | P47, P48 |

---

## Fluxo de Decisão do Planejador (LLM Orquestrador)

```
ENTRADA: pergunta do usuário em linguagem natural

1. CLASSIFICAR a intenção:
   ├── É pergunta conceitual (sem lugar)? → explain_product_type → RESPONDER
   └── Envolve busca geoespacial? → continuar

2. IDENTIFICAR o tipo de produto desejado:
   ├── Explícito ("carta 25k", "ortoimagem", "MDS") → tipo definido
   ├── Ambíguo ("mapa", "imagem") → PERGUNTAR ou inferir
   └── Todos ("o que tem", "todos os produtos") → tipo="*"

3. RESOLVER a geometria de busca:
   ├── Topônimo simples ("Alecrim") → geocode + search_municipality
   ├── Região informal ("Serra Gaúcha") → search_named_region
   ├── Feição geográfica ("rio Jacuí") → search_hydrography
   ├── Infraestrutura ("BR-116") → search_infrastructure
   ├── Instalação militar ("8 Bda Inf Mec") → search_military_installation
   ├── Fronteira ("fronteira com Uruguai") → search_border
   ├── UC / TI → search_conservation_unit / search_indigenous_land
   ├── Rota entre A e B → geocode(A) + geocode(B) + compute_route
   ├── Articulação ("SH-22-Y-C-V-2") → get_product_coverage
   ├── Ambíguo ("santa", "rio") → autocomplete_placename → PERGUNTAR
   └── Raio ("50km de X") → geocode(X) + buffer

4. APLICAR refinamentos:
   ├── Filtro de escala? → rank_by_scale
   ├── Filtro temporal? → rank_by_date ou filtro data_inicio/data_fim
   ├── Filtro de elevação? → filter_by_elevation
   ├── Busca de feições específicas (pontes, barragens)? → search_features
   └── Comparação temporal? → múltiplas buscas com datas diferentes

5. EXECUTAR a sequência de tools

6. FORMATAR a resposta:
   ├── Lista de produtos com metadados
   ├── Mapa de articulação
   ├── Relatório de cobertura/lacunas
   └── Sugestões de produtos alternativos se a busca original veio vazia
```
