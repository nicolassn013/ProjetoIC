"""
Aquisição dos arquivos da estação MAWS55 até o banco (FTP ou pasta local).

Exemplos (a partir da raiz do projeto):
  python pipeline/aquisicao_maws55.py                      # FTP, 8 arquivos mais recentes
  python pipeline/aquisicao_maws55.py --simular            # lê e trata, não grava nada
  python pipeline/aquisicao_maws55.py --periodo 202607     # um mês
  python pipeline/aquisicao_maws55.py --fonte pasta --pasta C:\\dados\\maws55
O FTP é configurado em config.env (veja config.exemplo.env). Sem segredo no código.
"""

import argparse
import os
import sys

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PASTA_PROJETO, "app"))
sys.path.insert(0, os.path.join(PASTA_PROJETO, "pipeline"))

import banco                                   # noqa: E402
import consultas                               # noqa: E402
from aquisicao import ingestao                 # noqa: E402
from aquisicao.config import ConfigError, carregar_config_ftp   # noqa: E402
from aquisicao.fontes import criar_fonte, filtrar_e_ordenar     # noqa: E402

LIMITE_SEM_CONFIRMAR = 500
LINHAS_DETALHADAS = 20      # acima disso, só os erros são listados um a um


def ler_argumentos(argv=None):
    p = argparse.ArgumentParser(description="Estação MAWS55 -> banco de dados")
    p.add_argument("--fonte", choices=["ftp", "pasta"], default="ftp")
    p.add_argument("--pasta", help="pasta com os .txt (fonte 'pasta')")
    p.add_argument("--config", help="caminho do config.env (padrão: raiz do projeto)")
    p.add_argument("--periodo", help="tudo, AAAA, AAAAMM ou AAAAMMDD")
    p.add_argument("--ultimos", type=int, default=8, help="sem --periodo: quantos arquivos recentes (padrão 8)")
    p.add_argument("--simular", action="store_true", help="não grava no banco nem guarda cópia")
    p.add_argument("--confirmar", action="store_true", help=f"permite mais de {LIMITE_SEM_CONFIRMAR} arquivos")
    return p.parse_args(argv)


def main(argv=None):
    args = ler_argumentos(argv)
    try:
        config = carregar_config_ftp(args.config) if args.fonte == "ftp" else None
        fonte = criar_fonte(args.fonte, config, args.pasta)
    except (ConfigError, ValueError) as erro:
        print(f"[ERRO] {erro}")
        return 2

    try:
        with fonte:
            nomes = filtrar_e_ordenar(fonte.listar(), args.periodo, None if args.periodo else args.ultimos)
            print(f"-> {len(nomes)} arquivo(s) selecionado(s)" + (" [SIMULAÇÃO]" if args.simular else ""))
            if len(nomes) > LIMITE_SEM_CONFIRMAR and not args.confirmar:
                print(f"[ERRO] Mais de {LIMITE_SEM_CONFIRMAR} arquivos. Confirme com --confirmar.")
                return 2
            if not nomes:
                print("[Aviso] Nenhum arquivo *_15m_AAAAMMDD_HHMM.txt encontrado.")
                return 0

            with banco.conectar_ou_criar() as conn:
                consultas.inicializar_schema(conn)
                resultados = ingestao.executar(conn, fonte, nomes, simular=args.simular)
    except (ConnectionError, FileNotFoundError) as erro:
        print(f"[ERRO] {erro}")
        return 1

    contagem = {}
    for r in resultados:
        contagem[r.status] = contagem.get(r.status, 0) + 1
        if len(resultados) <= LINHAS_DETALHADAS or r.status == "erro":
            detalhe = f" ({r.mensagem})" if r.mensagem else ""
            print(f"   {r.status:9} {r.nome}  linhas lidas={r.linhas_lidas} gravadas={r.linhas_gravadas}{detalhe}")
    print("-> Resumo:", ", ".join(f"{k}={v}" for k, v in sorted(contagem.items())))
    return 1 if contagem.get("erro") else 0


if __name__ == "__main__":
    sys.exit(main())
