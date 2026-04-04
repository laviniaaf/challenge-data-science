"""
engine.py :
Gera recomendações para melhorar o Klike Score de uma campanha publicitária.

Uso via CLI:
    python engine.py                          # demo com 3 campanhas
    python engine.py KLK-0001 KLK-0042       # campanhas específicas

Uso via Python:
    from engine import KlikeEngine
    import pandas as pd

    df     = pd.read_csv("../Fase 1/klike_challenge_dataset_pt.csv")
    engine = KlikeEngine(df)
    print(engine.relatorio(df.iloc[0], top_n=5))

Estratégia: rule-based com benchmarks estatísticos por plataforma.
Por que rule-based e não um modelo preditivo para gerar recomendações?
  - Interpretável: cada sugestão tem uma causa clara e auditável
  - Robusto com n=500: modelos sofrem com overfitting nessa escala
  - Direto ao ponto: sem caixa-preta, fácil de apresentar ao time de marketing
  - Atualizável: basta re-treinar com novos dados históricos
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class Recomendacao:
    """Representa uma recomendação única, priorizada por impacto."""
    titulo: str
    descricao: str
    impacto_klike: float        # estimativa de ganho em pontos de Klike Score
    metrica_primaria: str       # quais métricas são afetadas
    confianca: str              # 'alta' | 'media' | 'baixa'
    categoria: str              # 'criativo' | 'formato' | 'targeting' | 'conteudo' | 'audio'
    atributo_atual: str = ""
    atributo_sugerido: str = ""


class KlikeEngine:
    """
    Analisa uma campanha e retorna recomendações priorizadas por impacto estimado.

    Parameters:
    df : pd.DataFrame
        Dataset histórico com colunas em português (gerado na Fase 1).
        Usado apenas para computar benchmarks — não é armazenado em memória.
    """

    def __init__(self, df: pd.DataFrame):
        self._df = self._preprocess(df)
        self._bm  = self._compute_benchmarks(self._df)

    @staticmethod
    def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza tipos booleanos e cria campo auxiliar de faixa de duração."""
        df = df.copy()
        bool_map = {"True": 1, "False": 0, True: 1, False: 0}
        for col in ["tem_hook", "tem_rosto", "tem_cta", "tem_legenda", "e_retargeting"]:
            if col in df.columns:
                df[col] = df[col].map(bool_map)
        return df

    @staticmethod
    def _faixa_duracao(s: float) -> Optional[str]:
        """Converte duração em segundos para a faixa correspondente."""
        if pd.isna(s):
            return None
        if s <= 10:  return "≤10s"
        if s <= 20:  return "11-20s"
        if s <= 30:  return "21-30s"
        if s <= 60:  return "31-60s"
        return ">60s"

    @staticmethod
    def _compute_benchmarks(df: pd.DataFrame) -> dict:
        """
        Calcula medianas e deltas por plataforma.
        Usa mediana (não média) — mais robusta a outliers em gasto e ROAS.
        Resultado: dicionário plataforma → métricas de referência.
        """
        bm: dict = {}

        for plat in df["plataforma"].unique():
            sub = df[df["plataforma"] == plat]
            bm[plat] = {
                "klike_global": sub["pontuacao_klike"].median(),
                "ctr_global":   sub["taxa_cliques"].median(),
                "roas_global":  sub["roas"].median(),
                "n":            len(sub),
            }
            for attr in ["tem_hook", "tem_rosto", "tem_cta", "tem_legenda"]:
                com = sub[sub[attr] == 1]
                sem = sub[sub[attr] == 0]
                bm[plat][f"{attr}_delta_klike"] = (
                    com["pontuacao_klike"].median() - sem["pontuacao_klike"].median()
                )
                bm[plat][f"{attr}_delta_ctr"]   = (
                    com["taxa_cliques"].median() - sem["taxa_cliques"].median()
                )
                bm[plat][f"{attr}_delta_roas"]  = (
                    com["roas"].median() - sem["roas"].median()
                )
                bm[plat][f"{attr}_ctr_com"]     = com["taxa_cliques"].median()
                bm[plat][f"{attr}_ctr_sem"]     = sem["taxa_cliques"].median()
                bm[plat][f"{attr}_klike_com"]   = com["pontuacao_klike"].median()
                bm[plat][f"{attr}_klike_sem"]   = sem["pontuacao_klike"].median()
                
            r_sim = sub[sub["e_retargeting"] == 1]
            r_nao = sub[sub["e_retargeting"] == 0]
            bm[plat]["retarg_delta_klike"] = (
                r_sim["pontuacao_klike"].median() - r_nao["pontuacao_klike"].median()
            )
            bm[plat]["retarg_delta_roas"]  = r_sim["roas"].median() - r_nao["roas"].median()
            bm[plat]["retarg_roas_com"]    = r_sim["roas"].median()
            bm[plat]["retarg_roas_sem"]    = r_nao["roas"].median()
            bm[plat]["retarg_ctr_com"]     = r_sim["taxa_cliques"].median()
            bm[plat]["retarg_ctr_sem"]     = r_nao["taxa_cliques"].median()

            dens_med = sub.groupby("densidade_texto")["pontuacao_klike"].median()
            bm[plat]["best_densidade"] = dens_med.idxmax() if not dens_med.empty else "medium"
            bm[plat]["dens_klike"]     = dens_med.to_dict()

            fmt_med = sub.groupby("formato")["pontuacao_klike"].median()
            bm[plat]["best_formato"] = fmt_med.idxmax() if not fmt_med.empty else None
            bm[plat]["fmt_klike"]    = fmt_med.to_dict()
            
            sub2 = sub.dropna(subset=["duracao_video_s"]).copy()
            sub2["_faixa"] = sub2["duracao_video_s"].apply(KlikeEngine._faixa_duracao)
            dur_med = sub2.groupby("_faixa", observed=True)["pontuacao_klike"].median()
            bm[plat]["best_duracao"] = dur_med.idxmax() if not dur_med.empty else None
            bm[plat]["dur_klike"]    = dur_med.to_dict()

            top_q = sub[sub["pontuacao_klike"] >= sub["pontuacao_klike"].quantile(0.75)]
            mv    = top_q["proporcao_musica_voz"].dropna()
            bm[plat]["ideal_musica_q25"] = mv.quantile(0.25) if len(mv) else 0.2
            bm[plat]["ideal_musica_q75"] = mv.quantile(0.75) if len(mv) else 0.6
            bm[plat]["ideal_musica_med"] = mv.median()       if len(mv) else 0.38

        return bm


    def recomendar(self, campanha, top_n: int = 5) -> list[Recomendacao]:
        """
        Gera e prioriza recomendações para uma campanha.

        Parameters:
        campanha : dict ou pd.Series — campos da campanha a ser analisada
        top_n    : número máximo de recomendações a retornar (padrão: 5)

        Returns:
        Lista de Recomendacao ordenada por impacto_klike decrescente.
        """
        c = campanha.to_dict() if isinstance(campanha, pd.Series) else dict(campanha)

        _bmap = {"True": True, "False": False, 1: True, 0: False, True: True, False: False}
        for attr in ["tem_hook", "tem_rosto", "tem_cta", "tem_legenda", "e_retargeting"]:
            if attr in c:
                c[attr] = _bmap.get(c[attr], c[attr])

        plat = c.get("plataforma", "Meta")
        bm   = self._bm.get(plat, next(iter(self._bm.values())))
        recs: list[Recomendacao] = []

        if not c.get("tem_hook", True):
            dk       = bm["tem_hook_delta_klike"]
            dctr_abs = bm["tem_hook_delta_ctr"]
            ctr_sem  = bm["tem_hook_ctr_sem"]
            pct_ctr  = (dctr_abs / ctr_sem * 100) if ctr_sem > 0 else 0

            roas_obs = bm["tem_hook_delta_roas"]
            if plat == "TikTok" and roas_obs > 0:
                nota_roas = f" O ROAS também melhora em ~{roas_obs:.2f} no TikTok."
            elif plat == "Meta" and roas_obs < 0:
                nota_roas = (
                    f" Atenção: no Meta, hook reduz ROAS em ~{abs(roas_obs):.2f} "
                    f"— o impacto positivo está no CTR, não na conversão direta."
                )
            else:
                nota_roas = ""

            recs.append(Recomendacao(
                titulo="Adicionar hook nos primeiros 3 segundos",
                descricao=(
                    f"Campanhas com hook no {plat} têm CTR ~{dctr_abs*100:.1f}pp maior "
                    f"({pct_ctr:.0f}% de aumento relativo) e Klike Score ~{dk:.0f} pts mais alto "
                    f"(de {bm['tem_hook_klike_sem']:.0f} → {bm['tem_hook_klike_com']:.0f}). "
                    f"O hook captura atenção antes do primeiro scroll.{nota_roas}"
                ),
                impacto_klike=dk,
                metrica_primaria=f"Klike Score (+{dk:.0f} pts), CTR (+{pct_ctr:.0f}%)",
                confianca="alta",
                categoria="criativo",
                atributo_atual="sem hook",
                atributo_sugerido="hook nos 3 segundos iniciais",
            ))

        if not c.get("tem_rosto", True):
            dk      = bm["tem_rosto_delta_klike"]
            dctr    = bm["tem_rosto_delta_ctr"]
            ctr_sem = bm["tem_rosto_ctr_sem"]
            pct_ctr = (dctr / ctr_sem * 100) if ctr_sem > 0 else 0

            recs.append(Recomendacao(
                titulo="Incluir rosto humano no criativo",
                descricao=(
                    f"Criativos com rosto no {plat} têm Klike Score ~{dk:.0f} pts mais alto "
                    f"(de {bm['tem_rosto_klike_sem']:.0f} → {bm['tem_rosto_klike_com']:.0f}) "
                    f"e CTR ~{dctr*100:.1f}pp maior ({pct_ctr:.0f}% relativo). "
                    f"Rosto humano é o único atributo com impacto positivo em todas as plataformas — "
                    f"gera identificação e aumenta retenção."
                ),
                impacto_klike=dk,
                metrica_primaria=f"Klike Score (+{dk:.0f} pts), CTR (+{pct_ctr:.0f}%)",
                confianca="alta",
                categoria="criativo",
                atributo_atual="sem rosto",
                atributo_sugerido="incluir rosto humano visível",
            ))
            
        if not c.get("tem_cta", True):
            dk    = bm["tem_cta_delta_klike"]
            droas = bm["tem_cta_delta_roas"]
            nota  = (
                f" ROAS melhora em ~{droas:.2f}." if droas > 0.05
                else f" Impacto no ROAS é neutro para {plat}."
            )
            recs.append(Recomendacao(
                titulo="Adicionar call-to-action explícito",
                descricao=(
                    f"CTA aumenta o Klike Score em ~{dk:.0f} pts no {plat} "
                    f"(de {bm['tem_cta_klike_sem']:.0f} → {bm['tem_cta_klike_com']:.0f}). "
                    f"Indica ao usuário a próxima ação e reduz fricção na jornada.{nota}"
                ),
                impacto_klike=dk,
                metrica_primaria=f"Klike Score (+{dk:.0f} pts)",
                confianca="media",
                categoria="criativo",
                atributo_atual="sem CTA",
                atributo_sugerido="CTA claro (ex: 'Saiba mais', 'Compre agora', 'Baixe grátis')",
            ))


        if not c.get("tem_legenda", True):
            dk = bm["tem_legenda_delta_klike"]
            recs.append(Recomendacao(
                titulo="Adicionar legenda ao vídeo",
                descricao=(
                    f"Legendas aumentam o Klike Score em ~{dk:.0f} pts no {plat}. "
                    f"~85% das pessoas assistem vídeos sem som em redes sociais — "
                    f"sem legenda a mensagem não chega para a maioria da audiência."
                ),
                impacto_klike=dk,
                metrica_primaria=f"Klike Score (+{dk:.0f} pts)",
                confianca="media",
                categoria="acessibilidade",
                atributo_atual="sem legenda",
                atributo_sugerido="legenda em closed caption",
            ))

        dens_atual  = c.get("densidade_texto")
        best_dens   = bm.get("best_densidade")
        dens_klike  = bm.get("dens_klike", {})

        if dens_atual and best_dens and dens_atual != best_dens and dens_atual in dens_klike:
            k_atual  = dens_klike.get(dens_atual, 0)
            k_melhor = dens_klike.get(best_dens, 0)
            dk       = k_melhor - k_atual
            if dk > 0:
                recs.append(Recomendacao(
                    titulo=f"Reduzir densidade de texto de '{dens_atual}' para '{best_dens}'",
                    descricao=(
                        f"No {plat}, texto '{best_dens}' tem Klike Score mediano de ~{k_melhor:.0f} "
                        f"vs. ~{k_atual:.0f} com '{dens_atual}' (+{dk:.0f} pts). "
                        f"Menos texto deixa o criativo visual respirar e melhora a leitura em tela de celular."
                    ),
                    impacto_klike=dk,
                    metrica_primaria=f"Klike Score (+{dk:.0f} pts)",
                    confianca="media",
                    categoria="conteudo",
                    atributo_atual=f"densidade '{dens_atual}'",
                    atributo_sugerido=f"densidade '{best_dens}'",
                ))

        fmt_atual = c.get("formato")
        best_fmt  = bm.get("best_formato")
        fmt_klike = bm.get("fmt_klike", {})

        if fmt_atual and best_fmt and fmt_atual != best_fmt and fmt_atual in fmt_klike:
            k_atual  = fmt_klike.get(fmt_atual, 0)
            k_melhor = fmt_klike.get(best_fmt, 0)
            dk       = k_melhor - k_atual
            contexto = {
                "TikTok":   "Formato vertical é nativo do feed TikTok — máximo aproveitamento de tela.",
                "LinkedIn": "Formato horizontal é mais natural para LinkedIn desktop (principal dispositivo B2B).",
                "Meta":     "Meta aceita qualquer formato; vertical aproveita melhor o feed mobile.",
            }.get(plat, "")

            if dk > 3:
                recs.append(Recomendacao(
                    titulo=f"Mudar formato de '{fmt_atual}' para '{best_fmt}'",
                    descricao=(
                        f"No {plat}, formato '{best_fmt}' entrega ~{k_melhor:.0f} pts de Klike Score "
                        f"vs. ~{k_atual:.0f} com '{fmt_atual}' (+{dk:.0f} pts). {contexto}"
                    ),
                    impacto_klike=dk,
                    metrica_primaria=f"Klike Score (+{dk:.0f} pts)",
                    confianca="alta" if dk > 10 else "media",
                    categoria="formato",
                    atributo_atual=f"formato {fmt_atual}",
                    atributo_sugerido=f"formato {best_fmt}",
                ))

        duracao = c.get("duracao_video_s")
        if duracao is not None and not pd.isna(duracao):
            faixa_atual = self._faixa_duracao(float(duracao))
            best_dur    = bm.get("best_duracao")
            dur_klike   = bm.get("dur_klike", {})

            if faixa_atual and best_dur and faixa_atual != best_dur and faixa_atual in dur_klike:
                k_atual  = dur_klike.get(faixa_atual, 0)
                k_melhor = dur_klike.get(best_dur, 0)
                dk       = k_melhor - k_atual

                _dur_alvo = {
                    "≤10s": "até 10s", "11-20s": "~15s",
                    "21-30s": "~25s",  "31-60s": "~25-30s", ">60s": "~25-30s",
                }

                if dk > 3:
                    recs.append(Recomendacao(
                        titulo=f"Ajustar duração para a faixa '{best_dur}'",
                        descricao=(
                            f"No {plat}, vídeos na faixa '{best_dur}' têm Klike Score ~{k_melhor:.0f} "
                            f"vs. ~{k_atual:.0f} da faixa '{faixa_atual}' (+{dk:.0f} pts). "
                            f"O vídeo atual tem {duracao:.0f}s — considere uma versão em {_dur_alvo.get(best_dur, best_dur)}."
                        ),
                        impacto_klike=dk,
                        metrica_primaria=f"Klike Score (+{dk:.0f} pts)",
                        confianca="baixa",
                        categoria="formato",
                        atributo_atual=f"{duracao:.0f}s ({faixa_atual})",
                        atributo_sugerido=f"faixa {best_dur}",
                    ))

        if not c.get("e_retargeting", True):
            dk      = bm.get("retarg_delta_klike", 0)
            dr      = bm.get("retarg_delta_roas",  0)
            r_sem   = bm.get("retarg_roas_sem",    0)
            r_com   = bm.get("retarg_roas_com",    0)
            ctr_sem = bm.get("retarg_ctr_sem",     0)
            ctr_com = bm.get("retarg_ctr_com",     0)
            pct_r   = (dr / r_sem * 100) if r_sem > 0 else 0
            pct_ctr = ((ctr_com - ctr_sem) / ctr_sem * 100) if ctr_sem > 0 else 0

            if dr > 0.2 or dk > 3:
                recs.append(Recomendacao(
                    titulo="Testar versão com retargeting para audiência quente",
                    descricao=(
                        f"No {plat}, campanhas de retargeting têm ROAS ~{r_com:.2f} vs. ~{r_sem:.2f} "
                        f"em audiência nova (+{pct_r:.0f}%) e CTR ~{ctr_com*100:.1f}% vs. "
                        f"~{ctr_sem*100:.1f}% (+{pct_ctr:.0f}%). "
                        f"Usuários que já interagiram com a marca convertem mais com o mesmo gasto."
                    ),
                    impacto_klike=dk,
                    metrica_primaria=f"ROAS (+{pct_r:.0f}%), CTR (+{pct_ctr:.0f}%)",
                    confianca="media",
                    categoria="targeting",
                    atributo_atual="audiência nova (prospecting)",
                    atributo_sugerido="retargeting de audiência quente",
                ))

        musica = c.get("proporcao_musica_voz")
        if musica is not None and not pd.isna(musica):
            q25  = bm.get("ideal_musica_q25", 0.2)
            q75  = bm.get("ideal_musica_q75", 0.55)
            med  = bm.get("ideal_musica_med", 0.38)

            if float(musica) > q75 + 0.10:   # acima do range ideal
                diff  = float(musica) - med
                dk    = min(diff * 14.0, 8.0)   # heurística baseada na correlação negativa
                recs.append(Recomendacao(
                    titulo=f"Reduzir proporção de música (atual: {float(musica):.2f})",
                    descricao=(
                        f"No {plat}, campanhas de alto desempenho têm proporção música/voz "
                        f"entre {q25:.2f}–{q75:.2f} (mediana: {med:.2f}). "
                        f"Proporção atual de {float(musica):.2f} está acima do ideal — "
                        f"mais voz e menos trilha de fundo melhora retenção e compreensão da mensagem."
                    ),
                    impacto_klike=dk,
                    metrica_primaria=f"Klike Score (~+{dk:.0f} pts estimados)",
                    confianca="baixa",
                    categoria="audio",
                    atributo_atual=f"música/voz = {float(musica):.2f}",
                    atributo_sugerido=f"música/voz ≈ {med:.2f}",
                ))

        # Filtra recomendações com impacto positivo e ordena por impacto
        validas = [r for r in recs if r.impacto_klike > 0]
        validas.sort(key=lambda r: r.impacto_klike, reverse=True)
        return validas[:top_n]


    def relatorio(self, campanha, top_n: int = 5) -> str:
        """
        Retorna string formatada com as recomendações da campanha.
        Pronto para terminal, notebook (print) ou logging.
        """
        c   = campanha.to_dict() if isinstance(campanha, pd.Series) else dict(campanha)
        cid = c.get("id_campanha", "N/A")
        plat = c.get("plataforma", "N/A")
        klike_atual = c.get("pontuacao_klike", "?")
        recs = self.recomendar(campanha, top_n=top_n)

        bm_plat = self._bm.get(plat, {})
        klike_med = bm_plat.get("klike_global", 60.5)

        linhas = [
            "═" * 68,
            f"  RELATÓRIO DE RECOMENDAÇÕES",
            f"  Campanha : {cid}  |  Plataforma: {plat}",
            f"  Klike Score atual : {klike_atual}  |  Mediana {plat}: {klike_med:.1f}",
            "═" * 68,
        ]

        if not recs:
            linhas.append(
                "\n  ✓ Campanha já segue as melhores práticas do dataset. "
                "Nenhuma melhoria identificada."
            )
        else:
            for i, r in enumerate(recs, 1):
                conf_emoji = {"alta": "●●●", "media": "●●○", "baixa": "●○○"}.get(r.confianca, "?")
                linhas += [
                    f"\n  [{i}] {r.titulo}",
                    f"      Impacto estimado  : ~+{r.impacto_klike:.0f} pts Klike Score",
                    f"      Métricas afetadas : {r.metrica_primaria}",
                    f"      Confiança         : {conf_emoji} {r.confianca}",
                    f"      Categoria         : {r.categoria}",
                    f"      Atual → Sugerido  : {r.atributo_atual} → {r.atributo_sugerido}",
                    f"      {r.descricao}",
                ]

        ganho_total = sum(r.impacto_klike for r in recs)
        if recs:
            linhas += [
                "",
                f"  Potencial total estimado : ~+{ganho_total:.0f} pts",
                f"  (Se todas as recomendações fossem aplicadas de forma independente)",
            ]

        linhas.append("═" * 68)
        return "\n".join(linhas)


# Cli

if __name__ == "__main__":
    DATA_PATH = "../Fase 1/klike_challenge_dataset_pt.csv"

    try:
        df = pd.read_csv(DATA_PATH, parse_dates=["data"])
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {DATA_PATH}")
        print("       Execute a partir do diretório Fase 3/ ou ajuste DATA_PATH.")
        sys.exit(1)

    engine = KlikeEngine(df)

    # IDs passados como argumentos, ou demo padrão
    ids = sys.argv[1:] if len(sys.argv) > 1 else ["KLK-0001", "KLK-0003", "KLK-0020"]

    for cid in ids:
        row = df[df["id_campanha"] == cid]
        if row.empty:
            print(f"\n[!] Campanha '{cid}' não encontrada no dataset.")
            continue
        print(engine.relatorio(row.iloc[0], top_n=5))
        print()
